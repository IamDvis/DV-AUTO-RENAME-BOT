import os
import re
import time
import logging
from datetime import datetime

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import FloodWait
from PIL import Image
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser

from helper.utils import progress_for_pyrogram, humanbytes, convert
from helper.database import DvisPappa
from config import Config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global dictionary for tracking ongoing renaming operations
renaming_operations = {}

# -------------------- Regex Patterns for File Name Extraction --------------------
pattern1 = re.compile(r'S(\d+)(?:E|EP)(\d+)', re.IGNORECASE)
pattern2 = re.compile(r'S(\d+)\s*(?:E|EP|-\s*EP)(\d+)', re.IGNORECASE)
pattern3 = re.compile(r'(?:[([<{]?\s*(?:E|EP)\s*(\d+)\s*[)\]>}]?)', re.IGNORECASE)
pattern3_2 = re.compile(r'(?:\s*-\s*(\d+)\s*)')
pattern4 = re.compile(r'S(\d+)[^\d]*(\d+)', re.IGNORECASE)
patternX = re.compile(r'(\d+)')

# -------------------- Regex Patterns for Quality Extraction --------------------
pattern5 = re.compile(r'\b(?:.*?(\d{3,4}[^\dp]*p).*?|.*?(\d{3,4}p))\b', re.IGNORECASE)
pattern6 = re.compile(r'[([<{]?\s*4k\s*[)\]>}]?', re.IGNORECASE)
pattern7 = re.compile(r'[([<{]?\s*2k\s*[)\]>}]?', re.IGNORECASE)
pattern8 = re.compile(r'[([<{]?\s*HdRip\s*[)\]>}]?|\bHdRip\b', re.IGNORECASE)
pattern9 = re.compile(r'[([<{]?\s*4kX264\s*[)\]>}]?', re.IGNORECASE)
pattern10 = re.compile(r'[([<{]?\s*4kx265\s*[)\]>}]?', re.IGNORECASE)

# -------------------- Extraction Functions for File Name --------------------
def extract_quality(filename: str) -> str:
    # Filename se quality extract karta hai using multiple regex patterns.
    match = re.search(pattern5, filename)
    if match:
        quality = match.group(1) or match.group(2)
        logger.info(f"Matched Pattern 5: {quality}")
        return quality

    match = re.search(pattern6, filename)
    if match:
        logger.info("Matched Pattern 6: 4k")
        return "4k"

    match = re.search(pattern7, filename)
    if match:
        logger.info("Matched Pattern 7: 2k")
        return "2k"

    match = re.search(pattern8, filename)
    if match:
        logger.info("Matched Pattern 8: HdRip")
        return "HdRip"

    match = re.search(pattern9, filename)
    if match:
        logger.info("Matched Pattern 9: 4kX264")
        return "4kX264"

    match = re.search(pattern10, filename)
    if match:
        logger.info("Matched Pattern 10: 4kx265")
        return "4kx265"

    logger.info("No quality pattern matched, returning 'Unknown'")
    return "Unknown"

def extract_episode_number(filename: str) -> str:
    # Filename se episode number extract karta hai using multiple regex patterns.
    match = re.search(pattern1, filename)
    if match:
        logger.info("Matched Pattern 1")
        return match.group(2)

    match = re.search(pattern2, filename)
    if match:
        logger.info("Matched Pattern 2")
        return match.group(2)

    match = re.search(pattern3, filename)
    if match:
        logger.info("Matched Pattern 3")
        return match.group(1)

    match = re.search(pattern3_2, filename)
    if match:
        logger.info("Matched Pattern 3_2")
        return match.group(1)

    match = re.search(pattern4, filename)
    if match:
        logger.info("Matched Pattern 4")
        return match.group(2)

    match = re.search(patternX, filename)
    if match:
        logger.info("Matched Pattern X")
        return match.group(1)

    logger.info("No episode pattern matched")
    return ""

# -------------------- Caption Parsing Function --------------------
def parse_caption_info(caption: str) -> dict:
    # Caption text se details extract karta hai:
    # Title, Season, Episode, Audio Track, Quality, aur Promo (agar separator ho)
    info = {
        "title": "N/A",
        "season": "N/A",
        "episode": "N/A",
        "audio": "N/A",
        "quality": "N/A",
        "promo": ""
    }
    
    # Split caption into non-empty lines; pehli line ko title maan lenge.
    lines = caption.splitlines()
    non_empty_lines = [line.strip() for line in lines if line.strip() != ""]
    if non_empty_lines:
        info["title"] = non_empty_lines[0]
    
    season_match = re.search(r"Season\s*[:\-]\s*(\d+)", caption, re.IGNORECASE)
    if season_match:
        info["season"] = season_match.group(1)
    
    episode_match = re.search(r"(?:Episode|Ep)\s*[:\-]\s*(\d+)", caption, re.IGNORECASE)
    if episode_match:
        info["episode"] = episode_match.group(1)
    
    audio_match = re.search(r"Audio\s*track\s*[:\-]\s*([\w\s]+)", caption, re.IGNORECASE)
    if audio_match:
        audio_text = audio_match.group(1).strip()
        info["audio"] = audio_text.split("|")[0].strip()
    
    quality_match = re.search(r"Quality\s*[:\-]\s*(\S+)", caption, re.IGNORECASE)
    if quality_match:
        info["quality"] = quality_match.group(1)
    
    promo_split = re.split(r"━{5,}", caption)
    if len(promo_split) > 1:
        info["promo"] = promo_split[1].strip()
    
    return info

# -------------------- Main Handler Function --------------------
@Client.on_message(filters.private & (filters.document | filters.video | filters.audio))
async def auto_rename_files(client: Client, message: Message):
    user_id = message.from_user.id
    # Get auto rename format (caption template) from database
    caption_template = await DvisPappa.get_caption(message.chat.id)
    media_preference = await DvisPappa.get_media_preference(user_id)
    
    # Agar caption template set nahi hua, to default template use karo
    if not caption_template:
        caption_template = "Title       : {title}\nSeason      : {season}\nEpisode     : {episode}\nAudio Track : {audio}\nQuality     : {quality}"

    # Determine file details based on type
    if message.document:
        file_id = message.document.file_id
        file_name = message.document.file_name
        media_type = media_preference or "document"
    elif message.video:
        file_id = message.video.file_id
        file_name = message.video.file_name if message.video.file_name else f"{message.video.file_id}.mp4"
        media_type = media_preference or "video"
    elif message.audio:
        file_id = message.audio.file_id
        file_name = message.audio.file_name if message.audio.file_name else f"{message.audio.file_id}.mp3"
        media_type = media_preference or "audio"
    else:
        await message.reply_text("Unsupported File Type")
        return

    logger.info(f"Original File Name: {file_name}")

    if file_id in renaming_operations:
        elapsed_time = (datetime.now() - renaming_operations[file_id]).seconds
        if elapsed_time < 10:
            logger.info("File is being ignored as it is currently being renamed or was renamed recently.")
            return
    renaming_operations[file_id] = datetime.now()

    # Extract episode and quality from file name
    episode_number = extract_episode_number(file_name)
    logger.info(f"Extracted Episode Number: {episode_number}")

    quality_extracted = extract_quality(file_name)
    logger.info(f"Extracted Quality: {quality_extracted}")

    # For file renaming: agar user ne /autorename caption ya {caption} set kiya hai,
    # to original file name (without extension) use karo, warna template se placeholders replace karo.
    if caption_template.strip().lower() in ["caption", "{caption}"]:
        new_format = os.path.splitext(file_name)[0]
    else:
        new_format = caption_template
        if episode_number:
            for placeholder in ["episode", "Episode", "EPISODE", "{episode}"]:
                if placeholder in new_format:
                    new_format = new_format.replace(placeholder, str(episode_number), 1)
                    break
        for quality_placeholder in ["quality", "Quality", "QUALITY", "{quality}"]:
            if quality_placeholder in new_format:
                new_format = new_format.replace(quality_placeholder, quality_extracted, 1)
                break

    _, file_extension = os.path.splitext(file_name)
    new_file_name = f"{new_format}{file_extension}"
    file_path = os.path.join("downloads", new_file_name)

    download_msg = await message.reply_text(text="Trying To Download...")
    try:
        path = await client.download_media(
            message,
            file_name=file_path,
            progress=progress_for_pyrogram,
            progress_args=("Download Started...", download_msg, time.time())
        )
    except Exception as e:
        del renaming_operations[file_id]
        await download_msg.edit_text(str(e))
        return

    duration = 0
    try:
        parser = createParser(file_path)
        metadata = extractMetadata(parser)
        if metadata and metadata.has("duration"):
            duration = metadata.get("duration").seconds
    except Exception as e:
        logger.warning(f"Error extracting duration: {e}")

    # Generate final caption for upload
    if caption_template.strip().lower() in ["caption", "{caption}"]:
        final_caption = (
            f"Title       : {new_file_name}\n"
            f"Season      : N/A\n"
            f"Episode     : {episode_number if episode_number else 'N/A'}\n"
            f"Audio Track : N/A\n"
            f"Quality     : {quality_extracted}\n"
        )
    else:
        caption_details = parse_caption_info(caption_template)
        caption_details["title"] = new_file_name
        final_caption = (
            f"Title       : {caption_details['title']}\n"
            f"Season      : {caption_details['season']}\n"
            f"Episode     : {caption_details['episode']}\n"
            f"Audio Track : {caption_details['audio']}\n"
            f"Quality     : {caption_details['quality']}\n\n"
            f"{caption_details['promo']}"
        )

    upload_msg = await download_msg.edit_text("Trying To Upload...")
    c_thumb = await DvisPappa.get_thumbnail(message.chat.id)
    ph_path = None
    if c_thumb:
        ph_path = await client.download_media(c_thumb)
    elif media_type == "video" and message.video.thumbs:
        ph_path = await client.download_media(message.video.thumbs[0].file_id)
        if ph_path:
            try:
                img = Image.open(ph_path).convert("RGB")
                img = img.resize((320, 320))
                img.save(ph_path, "JPEG")
            except Exception as e:
                logger.warning(f"Error processing thumbnail: {e}")

    try:
        if media_type == "document":
            await client.send_document(
                message.chat.id,
                document=file_path,
                thumb=ph_path,
                caption=final_caption,
                progress=progress_for_pyrogram,
                progress_args=("Upload Started...", upload_msg, time.time())
            )
        elif media_type == "video":
            await client.send_video(
                message.chat.id,
                video=file_path,
                caption=final_caption,
                thumb=ph_path,
                duration=duration,
                progress=progress_for_pyrogram,
                progress_args=("Upload Started...", upload_msg, time.time())
            )
        elif media_type == "audio":
            await client.send_audio(
                message.chat.id,
                audio=file_path,
                caption=final_caption,
                thumb=ph_path,
                duration=duration,
                progress=progress_for_pyrogram,
                progress_args=("Upload Started...", upload_msg, time.time())
            )
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        if ph_path and os.path.exists(ph_path):
            os.remove(ph_path)
        await upload_msg.edit_text(f"Error: {e}")
        del renaming_operations[file_id]
        return

    await download_msg.delete()
    if os.path.exists(file_path):
        os.remove(file_path)
    if ph_path and os.path.exists(ph_path):
        os.remove(ph_path)

    del renaming_operations[file_id]
