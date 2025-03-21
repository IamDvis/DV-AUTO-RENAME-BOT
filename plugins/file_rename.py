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

# Regex Patterns for File Name Extraction
pattern1 = re.compile(r'S(\d+)(?:E|EP)(\d+)', re.IGNORECASE)
pattern2 = re.compile(r'S(\d+)\s*(?:E|EP|-\s*EP)(\d+)', re.IGNORECASE)
pattern3 = re.compile(r'(?:[([<{]?\s*(?:E|EP)\s*(\d+)\s*[)\]>}]?)', re.IGNORECASE)
pattern3_2 = re.compile(r'(?:\s*-\s*(\d+)\s*)')
pattern4 = re.compile(r'S(\d+)[^\d]*(\d+)', re.IGNORECASE)
patternX = re.compile(r'(\d+)')

# Regex Patterns for Quality Extraction
pattern5_q = re.compile(r'\b(?:.*?(\d{3,4}[^\dp]*p).*?|.*?(\d{3,4}p))\b', re.IGNORECASE)
pattern6 = re.compile(r'[([<{]?\s*4k\s*[)\]>}]?', re.IGNORECASE)
pattern7 = re.compile(r'[([<{]?\s*2k\s*[)\]>}]?', re.IGNORECASE)
pattern8 = re.compile(r'[([<{]?\s*HdRip\s*[)\]>}]?|\bHdRip\b', re.IGNORECASE)
pattern9 = re.compile(r'[([<{]?\s*4kX264\s*[)\]>}]?', re.IGNORECASE)
pattern10 = re.compile(r'[([<{]?\s*4kx265\s*[)\]>}]?', re.IGNORECASE)

def extract_quality(filename: str) -> str:
    # Filename se quality extract karta hai using multiple regex patterns.
    match = re.search(pattern5_q, filename)
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
    # File name se episode number extract karta hai.
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

def extract_season_episode(filename: str) -> (str, str):
    # File name se season aur episode dono extract karta hai.
    match = re.search(pattern1, filename)
    if match:
        logger.info("Extracted Season and Episode using Pattern 1")
        return match.group(1), match.group(2)
    match = re.search(pattern2, filename)
    if match:
        logger.info("Extracted Season and Episode using Pattern 2")
        return match.group(1), match.group(2)
    # Agar season nahi milta, episode to extract kar lo.
    ep = extract_episode_number(filename)
    return "N/A", ep if ep else "N/A"

@Client.on_message(filters.private & (filters.document | filters.video | filters.audio))
async def auto_rename_files(client: Client, message: Message):
    user_id = message.from_user.id
    # Get auto rename format (caption template) from database; agar nahi mila to default use karenge
    caption_template = await DvisPappa.get_caption(message.chat.id)
    if not caption_template or caption_template.strip().lower() in ["caption", "{caption}"]:
        caption_template = "Title       : {title}\nSeason      : {season}\nEpisode     : {episode}\nAudio Track : {audio}\nQuality     : {quality}"
    
    media_preference = await DvisPappa.get_media_preference(user_id)
    
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

    # For file renaming, simply use the original base name
    base_name, file_extension = os.path.splitext(file_name)
    new_file_name = base_name + file_extension

    # Extract season and episode from file name
    season, episode = extract_season_episode(file_name)
    logger.info(f"Extracted Season: {season}, Episode: {episode}")
    quality_extracted = extract_quality(file_name)
    logger.info(f"Extracted Quality: {quality_extracted}")

    # Generate final caption using .format() on the template
    final_caption = caption_template.format(
        title=new_file_name,
        season=season,
        episode=episode,
        audio="N/A",
        quality=quality_extracted
    )

    download_msg = await message.reply_text(text="Trying To Download...")
    try:
        await client.download_media(
            message,
            file_name=os.path.join("downloads", new_file_name),
            progress=progress_for_pyrogram,
            progress_args=("Download Started...", download_msg, time.time())
        )
    except Exception as e:
        del renaming_operations[file_id]
        await download_msg.edit_text(str(e))
        return

    duration = 0
    try:
        parser = createParser(os.path.join("downloads", new_file_name))
        metadata = extractMetadata(parser)
        if metadata and metadata.has("duration"):
            duration = metadata.get("duration").seconds
    except Exception as e:
        logger.warning(f"Error extracting duration: {e}")

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
                document=os.path.join("downloads", new_file_name),
                thumb=ph_path,
                caption=final_caption,
                progress=progress_for_pyrogram,
                progress_args=("Upload Started...", upload_msg, time.time())
            )
        elif media_type == "video":
            await client.send_video(
                message.chat.id,
                video=os.path.join("downloads", new_file_name),
                caption=final_caption,
                thumb=ph_path,
                duration=duration,
                progress=progress_for_pyrogram,
                progress_args=("Upload Started...", upload_msg, time.time())
            )
        elif media_type == "audio":
            await client.send_audio(
                message.chat.id,
                audio=os.path.join("downloads", new_file_name),
                caption=final_caption,
                thumb=ph_path,
                duration=duration,
                progress=progress_for_pyrogram,
                progress_args=("Upload Started...", upload_msg, time.time())
            )
    except Exception as e:
        if os.path.exists(os.path.join("downloads", new_file_name)):
            os.remove(os.path.join("downloads", new_file_name))
        if ph_path and os.path.exists(ph_path):
            os.remove(ph_path)
        await upload_msg.edit_text(f"Error: {e}")
        del renaming_operations[file_id]
        return

    await download_msg.delete()
    if os.path.exists(os.path.join("downloads", new_file_name)):
        os.remove(os.path.join("downloads", new_file_name))
    if ph_path and os.path.exists(ph_path):
        os.remove(ph_path)

    del renaming_operations[file_id]
