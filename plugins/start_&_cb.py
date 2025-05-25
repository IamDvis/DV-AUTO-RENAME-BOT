import random
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallʙᴧᴄᴋQuery

from ʜєʟᴘer.database import DvisPappa
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
            InlineKeyboardButton('⚙️ ʜєʟᴘ', callʙᴧᴄᴋ_data='ʜєʟᴘ'),
            InlineKeyboardButton('💙 ᴧʙσᴜᴛ', callʙᴧᴄᴋ_data='ᴧʙσᴜᴛ')
        ],
        [
            InlineKeyboardButton("🧑‍💻 ᴅєᴠєʟσᴘєʀ 🧑‍💻", url='https://t.me/DvisDmBot')
        ]
    ])
    
    if Config.START_PIC:
        await message.reply_photo(
            Config.START_PIC, 
            ᴄᴧᴘᴛɪση=Txt.START_TXT.format(user.mention), 
            reply_markup=button
        )
    else:
        await message.reply_text(
            text=Txt.START_TXT.format(user.mention), 
            reply_markup=button, 
            disable_web_page_preview=True
        )

@Client.on_callʙᴧᴄᴋ_query()
async def cb_handler(client, query: CallʙᴧᴄᴋQuery):
    data = query.data 
    user_id = query.from_user.id  
    
    if data == "ʜσϻє":
        await query.message.edit_text(
            text=Txt.START_TXT.format(query.from_user.mention),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton('📢 ᴜᴘᴅᴧᴛєꜱ', url='https://t.me/net_pro_max'),
                    InlineKeyboardButton('💬 ꜱᴜᴘᴘσʀᴛ', url='https://t.me/+cXIPgHSuJnxiNjU1')
                ],
                [
                    InlineKeyboardButton('⚙️ ʜєʟᴘ', callʙᴧᴄᴋ_data='ʜєʟᴘ'),
                    InlineKeyboardButton('💙 ᴧʙσᴜᴛ', callʙᴧᴄᴋ_data='ᴧʙσᴜᴛ')
                ],
                [
                    InlineKeyboardButton("🧑‍💻 ᴅєᴠєʟσᴘєʀ 🧑‍💻", url='https://t.me/DvisDmBot')
                ]
            ])
        )
    
    elif data == "ᴄᴧᴘᴛɪση":
        await query.message.edit_text(
            text=Txt.ᴄᴧᴘᴛɪση_TXT,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✖️ ᴄʟσꜱє", callʙᴧᴄᴋ_data="ᴄʟσꜱє"),
                    InlineKeyboardButton("🔙 ʙᴧᴄᴋ", callʙᴧᴄᴋ_data="ʜєʟᴘ")
                ]
            ])
        )
    
    elif data == "ʜєʟᴘ":
        await query.message.edit_text(
            text=Txt.ʜєʟᴘ_TXT.format(client.mention),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("⚙️ ꜱєᴛᴜᴘ ᴧᴜᴛσʀєηᴧϻє ꜰσʀϻᴧᴛ ⚙️", callʙᴧᴄᴋ_data='file_names')
                ],
                [
                    InlineKeyboardButton('🖼️ ᴛʜᴜϻʙηᴧɪʟ', callʙᴧᴄᴋ_data='ᴛʜᴜϻʙηᴧɪʟ'),
                    InlineKeyboardButton('✏️ ᴄᴧᴘᴛɪση', callʙᴧᴄᴋ_data='ᴄᴧᴘᴛɪση')
                ],
                [
                    InlineKeyboardButton('🏠 ʜσϻє', callʙᴧᴄᴋ_data='ʜσϻє'),
                    InlineKeyboardButton('💰 ᴅσηᴧᴛє', callʙᴧᴄᴋ_data='ᴅσηᴧᴛє')
                ]
            ])
        )
    
    elif data == "ᴅσηᴧᴛє":
        await query.message.edit_text(
            text=Txt.ᴅσηᴧᴛє_TXT,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✖️ ᴄʟσꜱє", callʙᴧᴄᴋ_data="ᴄʟσꜱє"),
                    InlineKeyboardButton("🔙 ʙᴧᴄᴋ", callʙᴧᴄᴋ_data="ʜєʟᴘ")
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
                    InlineKeyboardButton("✖️ ᴄʟσꜱє", callʙᴧᴄᴋ_data="ᴄʟσꜱє"),
                    InlineKeyboardButton("🔙 ʙᴧᴄᴋ", callʙᴧᴄᴋ_data="ʜєʟᴘ")
                ]
            ])
        )
    
    elif data == "ᴛʜᴜϻʙηᴧɪʟ":
        await query.message.edit_ᴄᴧᴘᴛɪση(
            ᴄᴧᴘᴛɪση=Txt.ᴛʜᴜϻʙηᴧɪʟ_TXT,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✖️ ᴄʟσꜱє", callʙᴧᴄᴋ_data="ᴄʟσꜱє"),
                    InlineKeyboardButton("🔙 ʙᴧᴄᴋ", callʙᴧᴄᴋ_data="ʜєʟᴘ")
                ]
            ])
        )
    
    elif data == "ᴧʙσᴜᴛ":
        await query.message.edit_text(
            text=Txt.ᴧʙσᴜᴛ_TXT,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✖️ ᴄʟσꜱє", callʙᴧᴄᴋ_data="ᴄʟσꜱє"),
                    InlineKeyboardButton("🔙 ʙᴧᴄᴋ", callʙᴧᴄᴋ_data="ʜσϻє")
                ]
            ])
        )
    
    elif data == "ᴄʟσꜱє":
        try:
            await query.message.delete()
            await query.message.reply_to_message.delete()
            await query.message.continue_propagation()
        except:
            await query.message.delete()
            await query.message.continue_propagation()
