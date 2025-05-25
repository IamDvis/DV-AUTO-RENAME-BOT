import os, time

class Config(object):
    API_ID    = int(os.environ.get("API_ID", "0"))
    API_HASH  = os.environ.get("API_HASH", "")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "") 

    DB_NAME = os.environ.get("DB_NAME","DvisPappa")    
    DB_URL  = os.environ.get("DB_URL","")
 
    BOT_UPTIME  = time.time()
    START_PIC   = os.environ.get("START_PIC", "https://files.catbox.moe/4kwe69.jpg")
    
    ADMIN = [
        int(admin_id_str) 
        for admin_id_str in os.environ.get('ADMIN', '').split() 
        if admin_id_str.isdigit()
    ] or [0]
    
    FORCE_SUB   = os.environ.get("FORCE_SUB", "") 
    LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", "0"))
    
    WEBHOOK = bool(os.environ.get("WEBHOOK", "True"))



class Txt(object):
    # part of text configuration
        
    START_TXT = """<b>ʜєʟʟσ</b> {}.
    
🚀 <b>ᴧᴅᴠᴧηᴄєᴅ & ᴘσᴡєʀꜰᴜʟ ʀєηᴧϻє ʙσᴛ</b>

✨ <b>ᴧᴜᴛσϻᴧᴛɪᴄᴧʟʟʏ ʀєηᴧϻє ʏσᴜʀ ꜰɪʟєꜱ</b> ᴡɪᴛʜ єᴧꜱє!
✨ <b>ꜱᴜᴘᴘσʀᴛꜱ ᴄᴜꜱᴛσϻ ᴛʜᴜϻʙηᴧɪʟꜱ</b> ꜰσʀ ᴘєʀꜱσηᴧʟɪᴢєᴅ ᴘʀєᴠɪєᴡꜱ.
✨ <b>ᴧᴅᴅ ᴄᴜꜱᴛσϻ ᴄᴧᴘᴛɪσηꜱ</b> ᴛσ ʏσᴜʀ ꜰɪʟєꜱ єꜰꜰσʀᴛʟєꜱꜱʟʏ.

📌 <b>ηєєᴅ ʜєʟᴘ?</b> ᴜꜱє ᴛʜє <b>/tutorial</b> ᴄσϻϻᴧηᴅ ᴛσ ʟєᴧʀη ʜσᴡ ᴛσ ɢєᴛ ꜱᴛᴧʀᴛєᴅ!
    
<b>❖ ϻᴧᴅє ʙʏ  ➛ @TGUrlsHub</b>"""
    
    FILE_NAME_TXT = """<b><u>ꜱєᴛᴜᴘ ᴧᴜᴛσ ʀєηᴧϻє ꜰσʀϻᴧᴛ</u></b>

ᴜꜱє ᴛʜєꜱє ᴋєʏᴡσʀᴅꜱ ᴛσ ꜱєᴛᴜᴘ ᴄᴜꜱᴛσϻ ꜰɪʟє ηᴧϻє

✓ episode :- ᴛσ ʀєᴘʟᴧᴄє єᴘɪꜱσᴅє ηᴜϻʙєʀ
✓ quality :- ᴛσ ʀєᴘʟᴧᴄє ᴠɪᴅєσ ʀєꜱσʟᴜᴛɪση
✓ season :- ᴛσ ʀєᴘʟᴧᴄє ꜱєᴧꜱση ηᴜϻʙєʀ

<b>➻ єxᴧϻᴘʟє :</b> <code> /autorename [@TGUrlsHub]  One Piece [Sseason EPepisode] [quality] </code>

<b>➻ ʏσᴜʀ ᴄᴜʀʀєηᴛ ᴧᴜᴛσ ʀєηᴧϻє ꜰσʀϻᴧᴛ :</b> <code>{format_template}</code> """
    
    ABOUT_TXT = f"""<b>🤖 ϻʏ ηᴧϻє :</b> <a href='https://t.me/EraVibesXbot'> Rename Bot ⚡</a>
<b>📝 ʟᴧηɢᴜᴧɢє :</b> <a href='https://python.org'>Python 3</a>
<b>📚 ʟɪʙʀᴧʀʏ :</b> <a href='https://pyrogram.org'>Pyrogram 2.0</a>
<b>🚀 ꜱєʀᴠєʀ :</b> <a href='https://heroku.com'>Heroku</a>
<b>📢 ᴄʜᴧηηєʟ :</b> <a href='https://t.me/net_pro_max'>Network</a>
<b>🧑‍💻 ᴅєᴠєʟσᴘєʀ :</b> <a href='https://t.me/DvisDmBot'>Dvis Pappa</a>
    
<b>❖ ϻᴧᴅє ʙʏ  ➛</b> @net_pro_max"""

      
    THUMBNAIL_TXT = """<b><u>🖼️ ʜσᴡ ᴛσ ꜱєᴛ ᴛʜᴜϻʙηᴧɪʟ</u></b>
    
⦿ ʏσᴜ ᴄᴧη ᴧᴅᴅ ᴄᴜꜱᴛσϻ ᴛʜᴜϻʙηᴧɪʟ ꜱɪϻᴘʟʏ ʙʏ ꜱєηᴅɪηɢ ᴧ ᴘʜσᴛσ ᴛσ ϻє....
    
⦿ /viewthumb - ᴜꜱє ᴛʜɪꜱ ᴄσϻϻᴧηᴅ ᴛσ ꜱєє ʏσᴜʀ ᴛʜᴜϻʙηᴧɪʟ
⦿ /delthumb - ᴜꜱє ᴛʜɪꜱ ᴄσϻϻᴧηᴅ ᴛσ ᴅєʟєᴛє ʏσᴜʀ ᴛʜᴜϻʙηᴧɪʟ

<b>❖ ϻᴧᴅє ʙʏ  ➛ @TGUrlsHub</b>"""

    CAPTION_TXT = """<b><u>📝  ʜσᴡ ᴛσ ꜱєᴛ ᴄᴧᴘᴛɪση</u></b>
    
⦿ /set_caption - ᴜꜱє ᴛʜɪꜱ ᴄσϻϻᴧηᴅ ᴛσ ꜱєᴛ ʏσᴜʀ ᴄᴧᴘᴛɪση
⦿ /see_caption - ᴜꜱє ᴛʜɪꜱ ᴄσϻϻᴧηᴅ ᴛσ ꜱєє ʏσᴜʀ ᴄᴧᴘᴛɪση
⦿ /del_caption - ᴜꜱє ᴛʜɪꜱ ᴄσϻϻᴧηᴅ ᴛσ ᴅєʟєᴛє ʏσᴜʀ ᴄᴧᴘᴛɪση

<b>❖ ϻᴧᴅє ʙʏ  ➛ @TGUrlsHub</b>"""

    PROGRESS_BAR = """\n
<b>📁 ꜱɪᴢє</b> : {1} | {2}
<b>⏳️ ᴅσηє</b> : {0}%
<b>🚀 ꜱᴘєєᴅ</b> : {3}/s
<b>⏰️ єᴛᴧ</b> : {4} 

<b>❖ ϻᴧᴅє ʙʏ  ➛ @TGUrlsHub</b>"""
    
    
    DONATE_TXT = """<b>🥲 ᴛʜᴧηᴋꜱ ꜰσʀ ꜱʜσᴡɪηɢ ɪηᴛєʀєꜱᴛ ɪη ᴅσηᴧᴛɪση! ❤️</b>
    
ɪꜰ ʏσᴜ ʟɪᴋє ϻʏ ʙσᴛꜱ & ᴘʀσᴊєᴄᴛꜱ, ʏσᴜ ᴄᴧη 🎁 ᴅσηᴧᴛє ϻє ᴧηʏ ᴧϻσᴜηᴛ ꜰʀσϻ 10 ʀꜱ ᴜᴘᴛσ ʏσᴜʀ ᴄʜσɪᴄє.
    
<b>🛍 ᴜᴘɪ ɪᴅ:</b> <code>upi id</code> """
    
    HELP_TXT = """<b>ʜєʏ</b> {}
    
ʜєʀє ɪꜱ ᴛʜє ʜєʟᴘ ꜰσʀ ϻʏ ᴄσϻϻᴧηᴅꜱ.

<b>❖ ϻᴧᴅє ʙʏ  ➛ @TGUrlsHub</b>"""



