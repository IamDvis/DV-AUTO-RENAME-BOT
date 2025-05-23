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


RENAMES = {}


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


def extract_season(fname: str) -> str:
    s_pats = [
        r'S(\d+)(?:E|EP)(\d+)',
        r'S(\d+)\s*(?:E|EP|-\s*EP)(\d+)',
        r'S(\d+)[^\d]*(\d+)',
        r'\bseason\s*(\d+)\b',
        r'\bs(\d+)\b'
    ]
    for pat in s_pats:
        m = re.search(pat, fname, re.IGNORECASE)
        if m:
            return m.group(1)
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


async def get_thumb(client: Client, msg: Message, mtype: str) -> str:
    try:
        t = await DvisPappa.get_thumbnail(msg.chat.id)
        if t:
            return await client.download_media(t)
        elif mtype == "video" and hasattr(msg, 'video') and msg.video and msg.video.thumbs:
            best = max(msg.video.thumbs, key=lambda t: t.width if hasattr(t, 'width') and t.width else 0)
            p = await client.download_media(best.file_id)
            with Image.open(p) as img:
                if img.width > 320:
                    img.convert("RGB").resize((320,320), Image.LANCZOS).save(p, "JPEG")
            return p
    except Exception as e:
        print(f"Thumbnail Error: {e}")
    return None


@Client.on_message(filters.private & (filters.document | filters.video | filters.audio))
async def auto_rename(client: Client, msg: Message):
    if not msg.from_user:
        return

    uid = msg.from_user.id

    try:
        fmt = await DvisPappa.get_format_template(uid)
        mtype = (await DvisPappa.get_media_preference(uid)) or "document"
    except Exception as e:
        return await msg.reply_text(f"⚠️ Database Error: {str(e)}")

    if not fmt:
        return await msg.reply_text("⚠️ Pehle /autorename command se format set karo.")

    try:
        if msg.document:
            fid, fname, fsize = msg.document.file_id, msg.document.file_name, msg.document.file_size
        elif msg.video:
            fid, fname, fsize = msg.video.file_id, msg.video.file_name or f"video_{msg.video.file_unique_id}", msg.video.file_size
            fname = f"{os.path.splitext(fname)[0]}.mp4" if not os.path.splitext(fname)[1] else fname
        elif msg.audio:
            fid, fname, fsize = msg.audio.file_id, msg.audio.file_name or f"audio_{msg.audio.file_unique_id}", msg.audio.file_size
            fname = f"{os.path.splitext(fname)[0]}.mp3" if not os.path.splitext(fname)[1] else fname
        else:
            return await msg.reply_text("❌ Unsupported File Type")
    except Exception as e:
        return await msg.reply_text(f"❌ File Info Error: {str(e)}")

    ext = os.path.splitext(fname)[1].lower() if fname else ".mp4"
    video_exts = [".mp4", ".mkv", ".avi", ".mov", ".flv", ".wmv"]
    if ext in video_exts:
        mtype = "video"

    if fid in RENAMES and (datetime.now() - RENAMES[fid]).seconds < 10:
        return
    RENAMES[fid] = datetime.now()

    try:
        ep = extract_episode(fname or "")
        if ep:
            for ph in ["episode", "Episode", "EPISODE", "{episode}"]:
                fmt = fmt.replace(ph, ep, 1)
        
        # Extract season number
        season_num = extract_season(fname or "")
        if season_num:
            for ph in ["season", "Season", "SEASON", "{season}"]:
                fmt = fmt.replace(ph, season_num, 1)

        q = extract_quality(fname or "")
        for ph in ["quality", "Quality", "QUALITY", "{quality}"]:
            fmt = fmt.replace(ph, q)
        
        if "{old_name}" in fmt:
            fmt = fmt.replace("{old_name}", os.path.splitext(fname)[0] if fname else "file")
        
        new_name = f"{fmt}{ext}"
        path = f"downloads/{new_name}"

        dmsg = await msg.reply_text("🚀 Download starting...")
        try:
            await client.download_media(
                message=msg,
                file_name=path,
                progress=progress_for_pyrogram,
                progress_args=("🚀 Download Started...", dmsg, time.time())
            )
        except Exception as e:
            del RENAMES[fid]
            return await dmsg.edit(f"❌ Download Error: {str(e)}")

        dur = 0
        try:
            meta = extractMetadata(createParser(path))
            if meta and meta.has("duration"):
                dur = meta.get("duration").seconds
        except Exception as e:
            print(f"Metadata Error: {e}")
            dur = 0

        umsg = await dmsg.edit("📤 Upload starting...")

        default_caption = (
            f"📕Name ➠ : {new_name}\n\n"
            f"🔗 Size ➠ : {humanbytes(fsize)}\n\n"
            f"⏰ Duration ➠ : {convert(dur)}\n\n"
            f"🎥 Quality ➠ : {q}"
        )
        
        caption = default_caption

        try:
            cap = await DvisPappa.get_caption(msg.chat.id)
            if cap:
                try:
                    caption = cap.format(
                        filename=new_name,
                        filesize=humanbytes(fsize),
                        duration=convert(dur),
                        quality=q,
                        season=season_num if season_num else "" # Add season placeholder
                    )
                except KeyError as ke:
                    print(f"Warning: Custom caption formatting failed due to missing key: {ke}. Using default caption.")
                    caption = default_caption
                except Exception as e:
                    print(f"Error formatting custom caption: {e}. Using default caption.")
                    caption = default_caption
        except Exception as e:
            print(f"Error fetching custom caption from database: {e}. Using default caption.")
            caption = default_caption

        thumb = await get_thumb(client, msg, mtype)

        try:
            if mtype == "document":
                await client.send_document(
                    msg.chat.id,
                    document=path,
                    thumb=thumb,
                    caption=caption,
                    progress=progress_for_pyrogram,
                    progress_args=("📤 Upload Started...", umsg, time.time())
                )
            elif mtype == "video":
                await client.send_video(
                    msg.chat.id,
                    video=path,
                    caption=caption,
                    thumb=thumb,
                    duration=dur,
                    progress=progress_for_pyrogram,
                    progress_args=("📤 Upload Started...", umsg, time.time())
                )
            elif mtype == "audio":
                await client.send_audio(
                    msg.chat.id,
                    audio=path,
                    caption=caption,
                    thumb=thumb,
                    duration=dur,
                    progress=progress_for_pyrogram,
                    progress_args=("📤 Upload Started...", umsg, time.time())
                )
        except Exception as e:
            if os.path.exists(path):
                os.remove(path)
            if thumb and os.path.exists(thumb):
                os.remove(thumb)
            del RENAMES[fid]
            return await umsg.edit(f"❌ Upload Error: {str(e)}")

        await dmsg.delete()
        if os.path.exists(path):
            os.remove(path)
        if thumb and os.path.exists(thumb):
            os.remove(thumb)
        del RENAMES[fid]

    except Exception as e:
        if fid in RENAMES:
            del RENAMES[fid]
        return await msg.reply_text(f"❌ Main Error: {str(e)}")

