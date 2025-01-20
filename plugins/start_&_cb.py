from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    CallbackQuery,
)

from helper.database import DvisPappa
from config import Config, Txt
from helper.utils import verify_user, check_token


@Client.on_message(filters.private & filters.command("start"))
async def start(client, message):
    user = message.from_user
    await DvisPappa.add_user(client, message)
    button = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📢 Updates", url="https://t.me/net_pro_max"),
                InlineKeyboardButton(
                    "💬 Support", url="https://t.me/+cXIPgHSuJnxiNjU1"
                ),
            ],
            [
                InlineKeyboardButton("⚙️ Help", callback_data="help"),
                InlineKeyboardButton("💙 About", callback_data="about"),
            ],
            [InlineKeyboardButton("🧑‍💻 Developer 🧑‍💻", url="https://t.me/DvisDmBot")],
        ]
    )
    if Config.START_PIC:
        await message.reply_photo(
            Config.START_PIC,
            caption=Txt.START_TXT.format(user.mention),
            reply_markup=button,
        )
    else:
        await message.reply_text(
            text=Txt.START_TXT.format(user.mention),
            reply_markup=button,
            disable_web_page_preview=True,
        )

    # Token Verification
    if len(message.command) > 1:  # Check if there are additional arguments
        data = message.command[1]
        if data.split("-", 1)[0] == "verify":  # set if or elif it depend on your code
            userid = data.split("-", 2)[1]
            token = data.split("-", 3)[2]
            if str(message.from_user.id) != str(userid):
                return await message.reply_text(
                    text="<b>Invalid link or Expired link !</b>", protect_content=True
                )
            is_valid = await check_token(client, userid, token)
            if is_valid is True:
                await message.reply_text(
                    text=f"<b>Hey {message.from_user.mention}, You are successfully verified !\nNow you have unlimited access for all files till today midnight.</b>",
                    protect_content=True,
                )
                await verify_user(client, userid, token)
            else:
                return await message.reply_text(
                    text="<b>Invalid link or Expired link !</b>", protect_content=True
                )


@Client.on_callback_query()
async def cb_handler(client, query: CallbackQuery):
    data = query.data
    user_id = query.from_user.id

    if data == "home":
        await query.message.edit_text(
            text=Txt.START_TXT.format(query.from_user.mention),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "📢 Updates", url="https://t.me/net_pro_max"
                        ),
                        InlineKeyboardButton(
                            "💬 Support", url="https://t.me/+cXIPgHSuJnxiNjU1"
                        ),
                    ],
                    [
                        InlineKeyboardButton("⚙️ Help", callback_data="help"),
                        InlineKeyboardButton("💙 About", callback_data="about"),
                    ],
                    [
                        InlineKeyboardButton(
                            "🧑‍💻 Developer 🧑‍💻", url="https://t.me/DvisDmBot"
                        )
                    ],
                ]
            ),
        )
    elif data == "caption":
        await query.message.edit_text(
            text=Txt.CAPTION_TXT,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("✖️ Close", callback_data="close"),
                        InlineKeyboardButton("🔙 Back", callback_data="help"),
                    ]
                ]
            ),
        )
    elif data == "help":
        await query.message.edit_text(
            text=Txt.HELP_TXT.format(client.mention),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "⚙️ Setup AutoRename Format ⚙️", callback_data="file_names"
                        )
                    ],
                    [
                        InlineKeyboardButton("🖼️ Thumbnail", callback_data="thumbnail"),
                        InlineKeyboardButton("✏️ Caption", callback_data="caption"),
                    ],
                    [
                        InlineKeyboardButton("🏠 Home", callback_data="home"),
                        InlineKeyboardButton("💰 Donate", callback_data="donate"),
                    ],
                ]
            ),
        )
    elif data == "donate":
        await query.message.edit_text(
            text=Txt.DONATE_TXT,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("✖️ Close", callback_data="close"),
                        InlineKeyboardButton("🔙 Back", callback_data="help"),
                    ]
                ]
            ),
        )

    elif data == "file_names":
        format_template = await DvisPappa.get_format_template(user_id)
        await query.message.edit_text(
            text=Txt.FILE_NAME_TXT.format(format_template=format_template),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("✖️ Close", callback_data="close"),
                        InlineKeyboardButton("🔙 Back", callback_data="help"),
                    ]
                ]
            ),
        )

    elif data == "thumbnail":
        await query.message.edit_caption(
            caption=Txt.THUMBNAIL_TXT,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("✖️ Close", callback_data="close"),
                        InlineKeyboardButton("🔙 Back", callback_data="help"),
                    ]
                ]
            ),
        )

    elif data == "about":
        await query.message.edit_text(
            text=Txt.ABOUT_TXT,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("✖️ Close", callback_data="close"),
                        InlineKeyboardButton("🔙 Back", callback_data="home"),
                    ]
                ]
            ),
        )

    elif data == "close":
        try:
            await query.message.delete()
            await query.message.reply_to_message.delete()
            await query.message.continue_propagation()
        except:
            await query.message.delete()
            await query.message.continue_propagation()
