from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from pyrogram.types import InputMediaDocument, Message
from PIL import Image
from datetime import datetime
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from helper.utils import progress_for_pyrogram, humanbytes, convert  # Verification se related functions hata diye
from helper.database import DvisPappa
from config import Config
import os
import time
import re

# Dictionary to track ongoing renaming operations
renaming_operations = {}

# ----------------- Episode Extraction Patterns (TV Series ke liye) -----------------
pattern1 = re.compile(r'S(\d+)(?:E|EP)(\d+)', re.IGNORECASE)
pattern2 = re.compile(r'S(\d+)\s*(?:E|EP|-\s*EP)(\d+)', re.IGNORECASE)
pattern3 = re.compile(r'(?:[([{<]\s*(?:E|EP)\s*(\d+)\s*[)\]}>])', re.IGNORECASE)
pattern3_2 = re.compile(r'(?:\s*-\s*(\d+)\s*)')
pattern4 = re.compile(r'S(\d+)[^\d]*(\d+)', re.IGNORECASE)

# ----------------- Quality Extraction Patterns -----------------
pattern5 = re.compile(r'\b(?:.*?(\d{3,4}[^\dp]*p).*?|.*?(\d{3,4}p))\b', re.IGNORECASE)
pattern6 = re.compile(r'[([{<]?\s*4k\s*[)\]}>]?', re.IGNORECASE)
pattern7 = re.compile(r'[([{<]?\s*2k\s*[)\]}>]?', re.IGNORECASE)
pattern8 = re.compile(r'[([{<]?\s*HdRip\s*[)\]}>]?|\bHdRip\b', re.IGNORECASE)
pattern9 = re.compile(r'[([{<]?\s*4kX264\s*[)\]}>]?', re.IGNORECASE)
pattern10 = re.compile(r'[([{<]?\s*4kx265\s*[)\]}>]?', re.IGNORECASE)

def extract_quality(filename):
    """Filename mein se quality extract karta hai."""
    match5 = re.search(pattern5, filename)
    if match5:
        print("Matched Pattern 5")
        quality5 = match5.group(1) or match5.group(2)
        print(f"Quality: {quality5}")
        return quality5

    match6 = re.search(pattern6, filename)
    if match6:
        print("Matched Pattern 6")
        quality6 = "4k"
        print(f"Quality: {quality6}")
        return quality6

    match7 = re.search(pattern7, filename)
    if match7:
        print("Matched Pattern 7")
        quality7 = "2k"
        print(f"Quality: {quality7}")
        return quality7

    match8 = re.search(pattern8, filename)
    if match8:
        print("Matched Pattern 8")
        quality8 = "HdRip"
        print(f"Quality: {quality8}")
        return quality8

    match9 = re.search(pattern9, filename)
    if match9:
        print("Matched Pattern 9")
        quality9 = "4kX264"
        print(f"Quality: {quality9}")
        return quality9

    match10 = re.search(pattern10, filename)
    if match10:
        print("Matched Pattern 10")
        quality10 = "4kx265"
        print(f"Quality: {quality10}")
        return quality10

    unknown_quality = "Unknown"
    print(f"Quality: {unknown_quality}")
    return unknown_quality

def extract_episode_number(filename):
    """Filename se episode number extract karta hai. Agar valid TV series pattern nahi milta to None return kare."""
    match = re.search(pattern1, filename)
    if match:
        print("Matched Pattern 1")
        return match.group(2)
    
    match = re.search(pattern2, filename)
    if match:
        print("Matched Pattern 2")
        return match.group(2)
    
    match = re.search(pattern3, filename)
    if match:
        print("Matched Pattern 3")
        return match.group(1)
    
    match = re.search(pattern3_2, filename)
    if match:
        print("Matched Pattern 3_2")
        return match.group(1)
    
    match = re.search(pattern4, filename)
    if match:
        print("Matched Pattern 4")
        return match.group(2)
    
    # Agar koi valid episode pattern nahi mila, to None return karo.
    return None

# ----------------- Example usage (Testing extraction functions) -----------------
if __name__ == "__main__":
    filename = "I Got a Cheat Skill in Another World and Became Unrivale.mp4.mp4"
    episode_number = extract_episode_number(filename)
    print(f"Extracted Episode Number: {episode_number}")
    quality = extract_quality(filename)
    print(f"Extracted Quality: {quality}")

# ----------------- Auto Rename Bot Handler -----------------
@Client.on_message(filters.private & (filters.document | filters.video | filters.audio))
async def auto_rename_files(client, message):
    # Verification check block hata diya gaya hai.
    
    user_id = message.from_user.id
    format_template = await DvisPappa.get_format_template(user_id)
    media_preference = await DvisPappa.get_media_preference(user_id)
    
    if not format_template:
        return await message.reply_text("Pehle /autorename command se format set karo.")
    
    # File details extract karo
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
    
    # Agar file recent rename operation mein hai, to usse ignore karo.
    if file_id in renaming_operations:
        elapsed_time = (datetime.now() - renaming_operations[file_id]).seconds
        if elapsed_time < 10:
            print("Recent rename operation chal rahi hai, file ignore kar rahe hain.")
            return
    
    renaming_operations[file_id] = datetime.now()
    
    # Episode number extract karo (TV series ke liye)
    episode_number = extract_episode_number(file_name)
    if episode_number:
        print(f"Extracted Episode Number: {episode_number}")
        placeholders = ["episode", "Episode", "EPISODE", "{episode}"]
        for placeholder in placeholders:
            if placeholder in format_template:
                format_template = format_template.replace(placeholder, str(episode_number), 1)
    else:
        print("Episode pattern nahi mila (shayed movie hai)")
    
    # Quality extract karke replace karo
    quality_placeholders = ["quality", "Quality", "QUALITY", "{quality}"]
    extracted_quality = extract_quality(file_name)
    for quality_placeholder in quality_placeholders:
        if quality_placeholder in format_template:
            format_template = format_template.replace(quality_placeholder, extracted_quality)
    
    # Old file name replacement: agar "{old_name}" placeholder use hua ho to replace karo
    if "{old_name}" in format_template:
        old_name = os.path.splitext(file_name)[0]
        format_template = format_template.replace("{old_name}", old_name)
    
    # New file name aur file path set karo
    _, file_extension = os.path.splitext(file_name)
    new_file_name = f"{format_template}{file_extension}"
    file_path = f"downloads/{new_file_name}"
    
    download_msg = await message.reply_text(text="Download start ho raha hai...")
    
    try:
        path = await client.download_media(
            message=message,
            file_name=file_path,
            progress=progress_for_pyrogram,
            progress_args=("Download Started...", download_msg, time.time())
        )
    except Exception as e:
        del renaming_operations[file_id]
        return await download_msg.edit(str(e))
    
    # Duration extraction with improved error handling
    duration = 0
    try:
        parser = createParser(file_path)
        metadata = extractMetadata(parser)
        if metadata is not None and metadata.has("duration"):
            duration = metadata.get('duration').seconds
        else:
            duration = 0
    except Exception as e:
        print(f"Duration extract karne me error: {e}")
        duration = 0
    
    upload_msg = await download_msg.edit("Upload start ho raha hai...")
    ph_path = None
    c_caption = await DvisPappa.get_caption(message.chat.id)
    c_thumb = await DvisPappa.get_thumbnail(message.chat.id)
    
    # Default caption format as per desired format, ab quality bhi add kiya gaya hai:
    caption = c_caption.format(
        filename=new_file_name,
        filesize=humanbytes(file_size),
        duration=convert(duration),
        quality=extracted_quality
    ) if c_caption else f"📕Name ➠ : {new_file_name}\n\n🔗 Size ➠ : {humanbytes(file_size)}\n\n⏰ Duration ➠ : {convert(duration)}\n\n🎥 Quality ➠ : {extracted_quality}"
    
    # Thumbnail download process
    if c_thumb:
        ph_path = await client.download_media(c_thumb)
        print(f"Thumbnail download ho gaya: {ph_path}")
    elif media_type == "video" and message.video.thumbs:
        ph_path = await client.download_media(message.video.thumbs[0].file_id)
        if ph_path:
            Image.open(ph_path).convert("RGB").save(ph_path)
            img = Image.open(ph_path)
            img.resize((320, 320))
            img.save(ph_path, "JPEG")
    
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
