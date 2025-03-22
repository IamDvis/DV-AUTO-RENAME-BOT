from pyrogram import Client, filters
from pyrogram.types import Message
from PIL import Image
from datetime import datetime
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from helper.utils import progress_for_pyrogram, humanbytes, convert
from helper.database import DvisPappa
from config import Config
import os, time, re

# Global dictionary for tracking recent renames
RENAMES = {}

# --- Extraction Functions ---
def extract_episode(filename: str) -> str:
    patterns = [
        r'S(\d+)(?:E|EP)(\d+)', 
        r'S(\d+)\s*(?:E|EP|-\s*EP)(\d+)', 
        r'(?:[([{<]\s*(?:E|EP)\s*(\d+)\s*[)\]}>])', 
        r'(?:\s*-\s*(\d+)\s*)', 
        r'S(\d+)[^\d]*(\d+)'
    ]
    for i, pat in enumerate(patterns):
        m = re.search(pat, filename, re.IGNORECASE)
        if m:
            return m.group(2) if i in [0, 1, 4] else m.group(1)
    return None

def extract_quality(filename: str) -> str:
    q_patterns = [
        (r'\b(?:.*?(\d{3,4}[^\dp]*p).*?|.*?(\d{3,4}p))\b', lambda m: m.group(1) or m.group(2)),
        (r'[([{<]?\s*4k\s*[)\]}>]?', lambda m: "4k"),
        (r'[([{<]?\s*2k\s*[)\]}>]?', lambda m: "2k"),
        (r'[([{<]?\s*HdRip\s*[)\]}>]?|\bHdRip\b', lambda m: "HdRip"),
        (r'[([{<]?\s*4kX264\s*[)\]}>]?', lambda m: "4kX264"),
        (r'[([{<]?\s*4kx265\s*[)\]}>]?', lambda m: "4kx265")
    ]
    for pat, func in q_patterns:
        m = re.search(pat, filename, re.IGNORECASE)
        if m:
            return func(m)
    return "Unknown"

# --- Thumbnail Processing ---
async def get_thumbnail(client: Client, msg: Message, mtype: str) -> str:
    thumb = await DvisPappa.get_thumbnail(msg.chat.id)
    if thumb:
        return await client.download_media(thumb)
    elif mtype == "video" and msg.video.thumbs:
        best = max(msg.video.thumbs, key=lambda t: t.width if hasattr(t, 'width') and t.width else 0)
        path = await client.download_media(best.file_id)
        with Image.open(path) as img:
            if img.width > 320:
                img.convert("RGB").resize((320, 320), Image.LANCZOS).save(path, "JPEG")
        return path
    return None

# --- Main Auto Rename Handler ---
@Client.on_message(filters.private & (filters.document | filters.video | filters.audio))
async def auto_rename(client: Client, msg: Message):
    user_id = msg.from_user.id
    fmt = await DvisPappa.get_format_template(user_id)
    m_pref = await DvisPappa.get_media_preference(user_id)
    if not fmt:
        return await msg.reply_text("Pehle /autorename command se format set karo.")
    
    if msg.document:
        fid, fname, fsize, mtype = msg.document.file_id, msg.document.file_name, msg.document.file_size, m_pref or "document"
    elif msg.video:
        fid, fname, fsize, mtype = msg.video.file_id, f"{msg.video.file_name}.mp4", msg.video.file_size, m_pref or "video"
    elif msg.audio:
        fid, fname, fsize, mtype = msg.audio.file_id, f"{msg.audio.file_name}.mp3", msg.audio.file_size, m_pref or "audio"
    else:
        return await msg.reply_text("Unsupported File Type")
    
    if fid in RENAMES and (datetime.now() - RENAMES[fid]).seconds < 10:
        return
    RENAMES[fid] = datetime.now()
    
    # Replace placeholders in format template
    ep = extract_episode(fname)
    if ep:
        for ph in ["episode", "Episode", "EPISODE", "{episode}"]:
            fmt = fmt.replace(ph, ep, 1)
    qual = extract_quality(fname)
    for ph in ["quality", "Quality", "QUALITY", "{quality}"]:
        fmt = fmt.replace(ph, qual)
    if "{old_name}" in fmt:
        fmt = fmt.replace("{old_name}", os.path.splitext(fname)[0])
    
    _, ext = os.path.splitext(fname)
    new_name = f"{fmt}{ext}"
    path = f"downloads/{new_name}"
    
    dmsg = await msg.reply_text("Download starting...")
    try:
        await client.download_media(message=msg, file_name=path, progress=progress_for_pyrogram, progress_args=("Download Started...", dmsg, time.time()))
    except Exception as e:
        del RENAMES[fid]
        return await dmsg.edit(str(e))
    
    dur = 0
    try:
        parser = createParser(path)
        meta = extractMetadata(parser)
        if meta and meta.has("duration"):
            dur = meta.get("duration").seconds
    except Exception as e:
        dur = 0

    umsg = await dmsg.edit("Upload starting...")
    cap = await DvisPappa.get_caption(msg.chat.id)
    caption = (cap.format(filename=new_name, filesize=humanbytes(fsize), duration=convert(dur), quality=qual)
               if cap else f"📕Name ➠ : {new_name}\n\n🔗 Size ➠ : {humanbytes(fsize)}\n\n⏰ Duration ➠ : {convert(dur)}\n\n🎥 Quality ➠ : {qual}")
    
    thumb_path = await get_thumbnail(client, msg, mtype)
    
    try:
        if mtype == "document":
            await client.send_document(msg.chat.id, document=path, thumb=thumb_path, caption=caption, progress=progress_for_pyrogram, progress_args=("Upload Started...", umsg, time.time()))
        elif mtype == "video":
            await client.send_video(msg.chat.id, video=path, caption=caption, thumb=thumb_path, duration=dur, progress=progress_for_pyrogram, progress_args=("Upload Started...", umsg, time.time()))
        elif mtype == "audio":
            await client.send_audio(msg.chat.id, audio=path, caption=caption, thumb=thumb_path, duration=dur, progress=progress_for_pyrogram, progress_args=("Upload Started...", umsg, time.time()))
    except Exception as e:
        os.remove(path)
        if thumb_path: os.remove(thumb_path)
        del RENAMES[fid]
        return await umsg.edit(f"Error: {e}")
    
    await dmsg.delete()
    os.remove(path)
    if thumb_path: os.remove(thumb_path)
    del RENAMES[fid]
