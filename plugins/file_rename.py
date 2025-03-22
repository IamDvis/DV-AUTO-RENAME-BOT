from pyrogram import Client, filters
from pyrogram.types import Message
from PIL import Image
from datetime import datetime
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from helper.utils import progress_for_pyrogram, humanbytes, convert  # Verification related functions removed
from helper.database import DvisPappa
from config import Config
import os, time, re

# Global dictionary for tracking renaming operations
renaming_operations = {}

# ------------------ Episode Extraction Patterns ------------------
EPISODE_PATTERNS = [
    re.compile(r'S(\d+)(?:E|EP)(\d+)', re.IGNORECASE),
    re.compile(r'S(\d+)\s*(?:E|EP|-\s*EP)(\d+)', re.IGNORECASE),
    re.compile(r'(?:[([{<]\s*(?:E|EP)\s*(\d+)\s*[)\]}>])', re.IGNORECASE),
    re.compile(r'(?:\s*-\s*(\d+)\s*)'),
    re.compile(r'S(\d+)[^\d]*(\d+)', re.IGNORECASE)
]

def extract_episode_number(filename: str) -> str:
    """Filename se episode number extract karta hai. Agar koi valid pattern nahi milta, None return kare."""
    for idx, pattern in enumerate(EPISODE_PATTERNS):
        match = re.search(pattern, filename)
        if match:
            print(f"Matched Episode Pattern {idx+1}")
            # For pattern indexes 0, 1, 4 use group(2); otherwise group(1)
            return match.group(2) if idx in [0, 1, 4] else match.group(1)
    return None

# ------------------ Quality Extraction Patterns ------------------
QUALITY_PATTERNS = [
    re.compile(r'\b(?:.*?(\d{3,4}[^\dp]*p).*?|.*?(\d{3,4}p))\b', re.IGNORECASE),
    re.compile(r'[([{<]?\s*4k\s*[)\]}>]?', re.IGNORECASE),
    re.compile(r'[([{<]?\s*2k\s*[)\]}>]?', re.IGNORECASE),
    re.compile(r'[([{<]?\s*HdRip\s*[)\]}>]?|\bHdRip\b', re.IGNORECASE),
    re.compile(r'[([{<]?\s*4kX264\s*[)\]}>]?', re.IGNORECASE),
    re.compile(r'[([{<]?\s*4kx265\s*[)\]}>]?', re.IGNORECASE)
]

def extract_quality(filename: str) -> str:
    """Filename se quality extract karta hai. Agar match na ho, 'Unknown' return kare."""
    for idx, pattern in enumerate(QUALITY_PATTERNS):
        match = re.search(pattern, filename)
        if match:
            print(f"Matched Quality Pattern {idx+1}")
            if idx == 0:
                quality = match.group(1) or match.group(2)
                if quality:
                    return quality
            elif idx == 1:
                return "4k"
            elif idx == 2:
                return "2k"
            elif idx == 3:
                return "HdRip"
            elif idx == 4:
                return "4kX264"
            elif idx == 5:
                return "4kx265"
    print("No quality pattern matched, returning 'Unknown'")
    return "Unknown"

# ------------------ Thumbnail Processing ------------------
async def process_thumbnail(client: Client, message: Message, media_type: str) -> str:
    """Agar custom thumbnail available hai, use use karo; warna video thumbnail se best quality thumb select karo."""
    ph_path = None
    c_thumb = await DvisPappa.get_thumbnail(message.chat.id)
    if c_thumb:
        ph_path = await client.download_media(c_thumb)
        print(f"Custom thumbnail downloaded: {ph_path}")
    elif media_type == "video" and message.video.thumbs:
        # Select best thumbnail based on width
        best_thumb = max(message.video.thumbs, key=lambda t: t.width if hasattr(t, 'width') and t.width else 0)
        ph_path = await client.download_media(best_thumb.file_id)
        if ph_path:
            with Image.open(ph_path) as img:
                # Resize only if image width is more than 320
                if img.width > 320:
                    new_size = (320, 320)
                    img = img.convert("RGB").resize(new_size, Image.LANCZOS)
                    img.save(ph_path, "JPEG")
    return ph_path

# ------------------ Auto Rename Bot Handler ------------------
@Client.on_message(filters.private & (filters.document | filters.video | filters.audio))
async def auto_rename_files(client: Client, message: Message):
    user_id = message.from_user.id
    format_template = await DvisPappa.get_format_template(user_id)
    media_preference = await DvisPappa.get_media_preference(user_id)
    
    if not format_template:
        return await message.reply_text("Pehle /autorename command se format set karo.")
    
    # File details extraction
    if message.document:
        file_id = message.document.file_id
        file_name = message.document.file_name
        file_size = message.document.file_size
        media_type = media_preference or "document"
    elif message.video:
        file_id = message.video.file_id
        file_name = f"{message.video.file_name}.mp4"
        file_size = message.video.file_size
        media_type = media_preference or "video"
    elif message.audio:
        file_id = message.audio.file_id
        file_name = f"{message.audio.file_name}.mp3"
        file_size = message.audio.file_size
        media_type = media_preference or "audio"
    else:
        return await message.reply_text("Unsupported File Type")
    
    print(f"Original File Name: {file_name}")
    
    # Skip if file recently processed
    if file_id in renaming_operations:
        elapsed = (datetime.now() - renaming_operations[file_id]).seconds
        if elapsed < 10:
            print("Recent rename operation chal rahi hai, skipping file.")
            return
    renaming_operations[file_id] = datetime.now()
    
    # Episode extraction
    episode_number = extract_episode_number(file_name)
    if episode_number:
        print(f"Extracted Episode Number: {episode_number}")
        for placeholder in ["episode", "Episode", "EPISODE", "{episode}"]:
            if placeholder in format_template:
                format_template = format_template.replace(placeholder, str(episode_number), 1)
    else:
        print("No episode pattern found (shayed movie file)")
    
    # Quality extraction
    extracted_quality = extract_quality(file_name)
    for placeholder in ["quality", "Quality", "QUALITY", "{quality}"]:
        if placeholder in format_template:
            format_template = format_template.replace(placeholder, extracted_quality)
    
    # Replace old file name placeholder if present
    if "{old_name}" in format_template:
        old_name = os.path.splitext(file_name)[0]
        format_template = format_template.replace("{old_name}", old_name)
    
    # Prepare new file name and path
    _, file_extension = os.path.splitext(file_name)
    new_file_name = f"{format_template}{file_extension}"
    file_path = f"downloads/{new_file_name}"
    
    download_msg = await message.reply_text("Download start ho raha hai...")
    try:
        await client.download_media(
            message=message,
            file_name=file_path,
            progress=progress_for_pyrogram,
            progress_args=("Download Started...", download_msg, time.time())
        )
    except Exception as e:
        del renaming_operations[file_id]
        return await download_msg.edit(str(e))
    
    # Duration extraction
    duration = 0
    try:
        parser = createParser(file_path)
        metadata = extractMetadata(parser)
        if metadata and metadata.has("duration"):
            duration = metadata.get("duration").seconds
    except Exception as e:
        print(f"Duration extraction error: {e}")
    
    upload_msg = await download_msg.edit("Upload start ho raha hai...")
    
    # Caption formatting (quality bhi include)
    c_caption = await DvisPappa.get_caption(message.chat.id)
    caption = c_caption.format(
        filename=new_file_name,
        filesize=humanbytes(file_size),
        duration=convert(duration),
        quality=extracted_quality
    ) if c_caption else (
        f"📕Name ➠ : {new_file_name}\n\n"
        f"🔗 Size ➠ : {humanbytes(file_size)}\n\n"
        f"⏰ Duration ➠ : {convert(duration)}\n\n"
        f"🎥 Quality ➠ : {extracted_quality}"
    )
    
    # Process thumbnail with improved quality
    ph_path = await process_thumbnail(client, message, media_type)
    
    try:
        if media_type == "document":
            await client.send_document(
                message.chat.id,
                document=file_path,
                thumb=ph_path,
                caption=caption,
                progress=progress_for_pyrogram,
                progress_args=("Upload Started...", upload_msg, time.time())
            )
        elif media_type == "video":
            await client.send_video(
                message.chat.id,
                video=file_path,
                caption=caption,
                thumb=ph_path,
                duration=duration,
                progress=progress_for_pyrogram,
                progress_args=("Upload Started...", upload_msg, time.time())
            )
        elif media_type == "audio":
            await client.send_audio(
                message.chat.id,
                audio=file_path,
                caption=caption,
                thumb=ph_path,
                duration=duration,
                progress=progress_for_pyrogram,
                progress_args=("Upload Started...", upload_msg, time.time())
            )
    except Exception as e:
        os.remove(file_path)
        if ph_path:
            os.remove(ph_path)
        del renaming_operations[file_id]
        return await upload_msg.edit(f"Error: {e}")
    
    await download_msg.delete()
    os.remove(file_path)
    if ph_path:
        os.remove(ph_path)
    
    del renaming_operations[file_id]
