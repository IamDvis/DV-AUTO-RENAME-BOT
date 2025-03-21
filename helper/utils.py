import math, time, pytz, random, string
from datetime import datetime, date
from pytz import timezone
from shortzy import Shortzy
from config import Config, Txt
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

async def progress_for_pyrogram(current, total, ud_type, message, start):
    diff = time.time() - start
    # Har 5 second ya last update par progress bar update karo
    if round(diff % 5) == 0 or current == total:
        pct = current * 100 / total
        speed = current / diff
        elapsed_ms = round(diff) * 1000
        eta_ms = elapsed_ms + round((total - current) / speed) * 1000
        elapsed = TimeFormatter(milliseconds=elapsed_ms)
        eta = TimeFormatter(milliseconds=eta_ms)
        
        # Dynamic progress bar banane ka tarika:
        bar_length = 10  # total blocks
        filled_length = int(bar_length * current // total)
        bar = '[' + '■' * filled_length + '□' * (bar_length - filled_length) + f'] {round(pct, 2)}%'
        
        txt = bar + Txt.PROGRESS_BAR.format(
            round(pct, 2),
            humanbytes(current),
            humanbytes(total),
            humanbytes(speed),
            eta if eta != '' else "0 s"
        )
        try:
            await message.edit(
                text=f"{ud_type}\n\n{txt}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✖️ Cancel ✖️", callback_data="close")]])
            )
        except Exception:
            pass


            
            

def humanbytes(size):    
    if not size:
        return ""
    power = 2**10
    n = 0
    Dic_powerN = {0: ' ', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + 'b'


def TimeFormatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "d, ") if days else "") + \
        ((str(hours) + "h, ") if hours else "") + \
        ((str(minutes) + "m, ") if minutes else "") + \
        ((str(seconds) + "s, ") if seconds else "") + \
        ((str(milliseconds) + "ms, ") if milliseconds else "")
    return tmp[:-2] 

def convert(seconds):
    seconds = seconds % (24 * 3600)
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60      
    return "%d:%02d:%02d" % (hour, minutes, seconds)

async def send_log(b, u):
    if Config.LOG_CHANNEL is not None:
        curr = datetime.now(timezone("Asia/Kolkata"))
        date = curr.strftime('%d %B, %Y')
        time = curr.strftime('%I:%M:%S %p')
        await b.send_message(
            Config.LOG_CHANNEL,
            f"<b><u>New User Started The Bot</u></b> \n\n<b>User ID</b> : `{u.id}` \n<b>First Name</b> : {u.first_name} \n<b>Last Name</b> : {u.last_name} \n<b>User Name</b> : @{u.username} \n<b>User Mention</b> : {u.mention} \n<b>User Link</b> : <a href='tg://openmessage?user_id={u.id}'>Click Here</a>\n\nDate: {date}\nTime: {time}\n\nBy: {b.mention}"
        )
