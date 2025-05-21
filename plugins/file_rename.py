from pyrogram import Client, filters
from pyrogram.types import Message
from PIL import Image, UnidentifiedImageError
from datetime import datetime
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from helper.utils import progress_for_pyrogram, humanbytes, convert
from helper.database import DvisPappa
from config import Config
import os, time, re

RENAMES = {}

# --- Extraction Functions ---
def extract_episode(fname: str) -> str:
    pats = [
        r'S(\d+)(?:E|EP)(\d+)',
        r'S(\d+)\s*(?:E|EP|-\s*EP)(\d+)',
        r'(?:[([{<]\s*(?:E|EP)\s*(\d+)\s*[)\]}>])',
        r'(?:\s*-\s*(\d+)\s*)',
        r'S(\d+)[^\d]*(\d+)'
    ]
    for i, pat in enumerate(pats):
        m = re.search(pat, fname, re.IGNORECASE)
        if m:
            return m.group(2) if i in [0, 1, 4] else m.group(1)
    return None

def extract_quality(fname: str) -> str:
    qpats = [
        (r'\b(?:.*?(\d{3,4}[^\dp]*p).*?|.*?(\d{3,4}p))\b', lambda m: m.group(1) or m.group(2)),
        (r'[([{<]?\s*4k\s*[)\]}>]?', lambda m: "4k"),
        (r'[([{<]?\s*2k\s*[)\]}>]?', lambda m: "2k"),
        (r'[([{<]?\s*HdRip\s*[)\]}>]?|\bHdRip\b', lambda m: "HdRip"),
        (r'[([{<]?\s*4kX264\s*[)\]}>]?', lambda m: "4kX264"),
        (r'[([{<]?\s*4kx265\s*[)\]}>]?', lambda m: "4kx265")
    ]
    for pat, func in qpats:
        m = re.search(pat, fname, re.IGNORECASE)
        if m:
            return func(m)
    return "Unknown"

# --- Thumbnail Function ---
async def get_thumb(client: Client, msg: Message, mtype: str) -> str:
    t_file_id = await DvisPappa.get_thumbnail(msg.chat.id)
    downloaded_thumb_path = None

    if t_file_id:
        try:
            downloaded_thumb_path = await client.download_media(t_file_id)
            if downloaded_thumb_path:
                try:
                    with Image.open(downloaded_thumb_path) as img:
                        if img.width > 320:
                            img.convert("RGB").resize((320, 320), Image.LANCZOS).save(downloaded_thumb_path, "JPEG")
                    return downloaded_thumb_path
                except UnidentifiedImageError:
                    print(f"PIL.UnidentifiedImageError: Cannot identify image file: {downloaded_thumb_path}. Removing corrupt file.")
                    if os.path.exists(downloaded_thumb_path):
                        os.remove(downloaded_thumb_path)
                except Exception as e:
                    print(f"Error processing custom thumbnail {downloaded_thumb_path}: {e}")
                    if os.path.exists(downloaded_thumb_path):
                        os.remove(downloaded_thumb_path)
        except Exception as e:
            print(f"Error downloading custom thumbnail {t_file_id}: {e}")
            # FileReferenceExpired ya koi aur download error yahan catch hoga
            pass # Fallback to video thumbnail or None

    if mtype == "video" and msg.video and msg.video.thumbs:
        best = max(msg.video.thumbs, key=lambda t: t.width if hasattr(t, 'width') and t.width else 0)
        if best:
            try:
                downloaded_thumb_path = await client.download_media(best.file_id)
                if downloaded_thumb_path:
                    try:
                        with Image.open(downloaded_thumb_path) as img:
                            if img.width > 320:
                                img.convert("RGB").resize((320, 320), Image.LANCZOS).save(downloaded_thumb_path, "JPEG")
                        return downloaded_thumb_path
                    except UnidentifiedImageError:
                        print(f"PIL.UnidentifiedImageError: Cannot identify video thumbnail file: {downloaded_thumb_path}. Removing corrupt file.")
                        if os.path.exists(downloaded_thumb_path):
                            os.remove(downloaded_thumb_path)
                    except Exception as e:
                        print(f"Error processing video thumbnail {downloaded_thumb_path}: {e}")
                        if os.path.exists(downloaded_thumb_path):
                            os.remove(downloaded_thumb_path)
            except Exception as e:
                print(f"Error downloading video thumbnail {best.file_id}: {e}")
                pass # Return None if video thumbnail also fails

    return None

# --- Main Handler ---
@Client.on_message(filters.private & (filters.document | filters.video | filters.audio))
async def auto_rename(client: Client, msg: Message):
    uid = msg.from_user.id
    fmt = await DvisPappa.get_format_template(uid)
    mtype = (await DvisPappa.get_media_preference(uid)) or "document"
    
    if not fmt:
        return await msg.reply_text("⚠️ Pehle /autorename command se format set karo.")
    
    fid, fname, fsize = None, None, None
    if msg.document:
        fid, fname, fsize = msg.document.file_id, msg.document.file_name, msg.document.file_size
    elif msg.video:
        fid, fname, fsize = msg.video.file_id, f"{msg.video.file_name or 'video'}.mp4", msg.video.file_size
    elif msg.audio:
        fid, fname, fsize = msg.audio.file_id, f"{msg.audio.file_name or 'audio'}.mp3", msg.audio.file_size
    else:
        return await msg.reply_text("❌ Unsupported File Type")
    
    ext = os.path.splitext(fname)[1].lower()
    video_exts = [".mp4", ".mkv", ".avi", ".mov", ".flv", ".wmv"]
    if ext in video_exts:
        mtype = "video"
    
    if fid in RENAMES and (datetime.now() - RENAMES[fid]).seconds < 10:
        return
    RENAMES[fid] = datetime.now()
    
    ep = extract_episode(fname)
    if ep:
        for ph in ["episode", "Episode", "EPISODE", "{episode}"]:
            fmt = fmt.replace(ph, ep, 1)
    q = extract_quality(fname)
    for ph in ["quality", "Quality", "QUALITY", "{quality}"]:
        fmt = fmt.replace(ph, q)
    if "{old_name}" in fmt:
        fmt = fmt.replace("{old_name}", os.path.splitext(fname)[0])
    
    new_name = f"{fmt}{ext}"
    path = f"downloads/{new_name}"
    
    dmsg = await msg.reply_text("🚀 Download starting...")
    try:
        await client.download_media(message=msg, file_name=path, progress=progress_for_pyrogram, progress_args=("Download Started...", dmsg, time.time()))
    except Exception as e:
        del RENAMES[fid]
        if os.path.exists(path): os.remove(path) # Download fail hone par file clean karo
        return await dmsg.edit(f"❌ Download Error: {e}")
    
    dur = 0
    try:
        meta = extractMetadata(createParser(path))
        if meta and meta.has("duration"):
            dur = meta.get("duration").seconds
    except Exception as e:
        print(f"Error extracting metadata: {e}")
        dur = 0
    
    umsg = await dmsg.edit("📤 Upload starting...")
    cap = await DvisPappa.get_caption(msg.chat.id)
    caption = (cap.format(filename=new_name, filesize=humanbytes(fsize), duration=convert(dur), quality=q)
               if cap else f"📕Name ➠ : {new_name}\n\n🔗 Size ➠ : {humanbytes(fsize)}\n\n⏰ Duration ➠ : {convert(dur)}\n\n🎥 Quality ➠ : {q}")
    
    thumb = await get_thumb(client, msg, mtype)
    
    try:
        if mtype == "document":
            await client.send_document(msg.chat.id, document=path, thumb=thumb, caption=caption, progress=progress_for_pyrogram, progress_args=("Upload Started...", umsg, time.time()))
        elif mtype == "video":
            await client.send_video(msg.chat.id, video=path, caption=caption, thumb=thumb, duration=dur, progress=progress_for_pyrogram, progress_args=("Upload Started...", umsg, time.time()))
        elif mtype == "audio":
            await client.send_audio(msg.chat.id, audio=path, caption=caption, thumb=thumb, duration=dur, progress=progress_for_pyrogram, progress_args=("Upload Started...", umsg, time.time()))
    except Exception as e:
        print(f"Upload Error: {e}") # Upload error ko print karo
        if os.path.exists(path): os.remove(path)
        if thumb and os.path.exists(thumb): os.remove(thumb)
        del RENAMES[fid]
        return await umsg.edit(f"❌ Upload Error: {e}")
    
    await dmsg.delete()
    if os.path.exists(path): os.remove(path)
    if thumb and os.path.exists(thumb): os.remove(thumb)
    del RENAMES[fid]
