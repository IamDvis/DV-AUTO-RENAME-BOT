import random
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

from helper.database import DvisPappa
from config import Config, Txt

@Client.on_message(filters.private & filters.command("start"))
async def start(client, message):
    user = message.from_user
    await DvisPappa.add_user(client, message)
    
    button = InlineKeyboardMarkup([
        [
            InlineKeyboardButton('📢 ᴜᴘᴅᴧᴛєꜱ', url='https://t.me/net_pro_max'),
            InlineKeyboardButton('💬 ꜱᴜᴘᴘσʀᴛ', url='https://t.me/+cXIPgHSuJnxiNjU1')
        ],
        [
            InlineKeyboardButton('⚙️ ʜєʟᴘ', callback_data='help'),
            InlineKeyboardButton('💙 ᴧʙσᴜᴛ', callback_data='about')
        ],
        [
            InlineKeyboardButton("🧑‍💻 ᴅєᴠєʟσᴘєʀ 🧑‍💻", url='https://t.me/DvisDmBot')
        ]
    ])
    
    if Config.START_PIC:
        await message.reply_photo(
            Config.START_PIC, 
            caption=Txt.START_TXT.format(user.mention), 
            reply_markup=button
        )
    else:
        await message.reply_text(
            text=Txt.START_TXT.format(user.mention), 
            reply_markup=button, 
            disable_web_page_preview=True
        )

@Client.on_callback_query()
async def cb_handler(client, query: CallbackQuery):
    data = query.data 
    user_id = query.from_user.id  
    
    if data == "home":
        await query.message.edit_text(
            text=Txt.START_TXT.format(query.from_user.mention),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton('📢 ᴜᴘᴅᴧᴛєꜱ', url='https://t.me/net_pro_max'),
                    InlineKeyboardButton('💬 ꜱᴜᴘᴘσʀᴛ', url='https://t.me/+cXIPgHSuJnxiNjU1')
                ],
                [
                    InlineKeyboardButton('⚙️ ʜєʟᴘ', callback_data='help'),
                    InlineKeyboardButton('💙 ᴧʙσᴜᴛ', callback_data='about')
                ],
                [
                    InlineKeyboardButton("🧑‍💻 ᴅєᴠєʟσᴘєʀ 🧑‍💻", url='https://t.me/DvisDmBot')
                ]
            ])
        )
    
    elif data == "caption":
        await query.message.edit_text(
            text=Txt.CAPTION_TXT,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✖️ ᴄʟσꜱє", callback_data="close"),
                    InlineKeyboardButton("🔙 ʙᴧᴄᴋ", callback_data="help")
                ]
            ])
        )
    
    elif data == "help":
        await query.message.edit_text(
            text=Txt.HELP_TXT.format(client.mention),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("⚙️ ꜱєᴛᴜᴘ ᴧᴜᴛσʀєηᴧϻє ꜰσʀϻᴧᴛ ⚙️", callback_data='file_names')
                ],
                [
                    InlineKeyboardButton('🖼️ ᴛʜᴜϻʙηᴧɪʟ', callback_data='thumbnail'),
                    InlineKeyboardButton('✏️ ᴄᴧᴘᴛɪση', callback_data='caption')
                ],
                [
                    InlineKeyboardButton('🏠 ʜσϻє', callback_data='home'),
                    InlineKeyboardButton('💰 ᴅσηᴧᴛє', callback_data='donate')
                ]
            ])
        )
    
    elif data == "donate":
        await query.message.edit_text(
            text=Txt.DONATE_TXT,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✖️ ᴄʟσꜱє", callback_data="close"),
                    InlineKeyboardButton("🔙 ʙᴧᴄᴋ", callback_data="help")
                ]
            ])
        )
    
    elif data == "file_names":
        format_template = await DvisPappa.get_format_template(user_id)
        await query.message.edit_text(
            text=Txt.FILE_NAME_TXT.format(format_template=format_template),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✖️ ᴄʟσꜱє", callback_data="close"),
                    InlineKeyboardButton("🔙 ʙᴧᴄᴋ", callback_data="help")
                ]
            ])
        )
    
    elif data == "thumbnail":
        await query.message.edit_caption(
            caption=Txt.THUMBNAIL_TXT,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✖️ ᴄʟσꜱє", callback_data="close"),
                    InlineKeyboardButton("🔙 ʙᴧᴄᴋ", callback_data="help")
                ]
            ])
        )
    
    elif data == "about":
        await query.message.edit_text(
            text=Txt.ABOUT_TXT,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✖️ ᴄʟσꜱє", callback_data="close"),
                    InlineKeyboardButton("🔙 ʙᴧᴄᴋ", callback_data="home")
                ]
            ])
        )
    
    elif data == "close":
        try:
            await query.message.delete()
            await query.message.reply_to_message.delete()
            await query.message.continue_propagation()
        except:
            await query.message.delete()
            await query.message.continue_propagation()
