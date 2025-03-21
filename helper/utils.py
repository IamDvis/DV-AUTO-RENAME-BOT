import math, time, pytz, random, string
from datetime import datetime, date
from pytz import timezone
from shortzy import Shortzy
from config import Config, Txt
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

async def progress_for_pyrogram(current, total, ud_type, message, start):
    now = time.time()
    diff = now - start
    if round(diff % 5.00) == 0 or current == total:
        percentage = current * 100 / total
        speed = current / diff if diff > 0 else 0
        elapsed_time = round(diff) * 1000
        time_to_completion = round((total - current) / speed) * 1000 if speed else 0
        estimated_total_time = elapsed_time + time_to_completion

        elapsed_time_formatted = TimeFormatter(milliseconds=elapsed_time)
        estimated_total_time_formatted = TimeFormatter(milliseconds=estimated_total_time)

        # Fixed progress list jo user ne diya hai
        progress_list = [
            "[■□□□□□□□□□] 10%",
            "[■■□□□□□□□□] 20%",
            "[■■■□□□□□□□] 30%",
            "[■■■■□□□□□□] 40%",
            "[■■■■■□□□□□] 50%",
            "[■■■■■■□□□□] 60%",
            "[■■■■■■■□□□] 70%",
            "[■■■■■■■■□□] 80%",
            "[■■■■■■■■■□] 90%",
            "[■■■■■■■■■■] 100%"
        ]
        
        # Calculate index: percentage ko 10 se divide karke index nikalo, max index 9 hoga
        index = min(int(percentage // 10), 9)
        progress_str = progress_list[index]
        
        tmp = f"{progress_str}\n" \
              f"{round(percentage, 2)}% complete\n" \
              f"{humanbytes(current)} of {humanbytes(total)} at {humanbytes(speed)}/s\n" \
              f"Time elapsed: {elapsed_time_formatted} | ETA: {estimated_total_time_formatted if estimated_total_time_formatted else '0 s'}"
        
        try:
            await message.edit(
                text=f"{ud_type}\n\n{tmp}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✖️ Cancel ✖️", callback_data="close")]])
            )
        except Exception as e:
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
