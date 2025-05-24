from pyrogram import filters, Client
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message, User

from helper.misc import SUDOERS
from helper.database import DvisPappa
from config import Config

def language(func):
    async def wrapper(client, message, *args, **kwargs):
        _ = {
            "general_1": "Please reply to a user's message or provide a user ID/username.",
            "sudo_1": "{} already a sudo user.",
            "sudo_2": "{} added to sudo users.",
            "sudo_3": "{} is not a sudo user.",
            "sudo_4": "{} removed from sudo users.",
            "sudo_5": "Sudo Users List:\n\nOwner:\n",
            "sudo_6": "\n\nOther Sudo Users:\n",
            "sudo_7": "No other sudo users found.",
            "sudo_8": "Failed to update sudo user status in database."
        }
        return await func(client, message, _, *args, **kwargs)
    return wrapper

def close_markup(_):
    from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    return InlineKeyboardMarkup([[InlineKeyboardButton("Close", callback_data="close_panel")]])


async def extract_user(m: Message, client: Client) -> User:
    if m.reply_to_message:
        return m.reply_to_message.from_user
    
    if m.entities and len(m.entities) > (1 if m.text.startswith("/") else 0):
        msg_entities = m.entities[1] if m.text.startswith("/") else m.entities[0]
        if msg_entities.type == MessageEntityType.TEXT_MENTION and msg_entities.user:
            return msg_entities.user
    
    if len(m.command) > 1:
        arg = m.command[1]
        try:
            if arg.isdecimal():
                return await client.get_users(int(arg))
            else:
                return await client.get_users(arg)
        except Exception:
            pass
    
    return None


@Client.on_message(filters.command(["addsudo"]) & filters.user(Config.ADMIN))
@language
async def useradd(client: Client, message: Message, _):
    user = None
    if message.reply_to_message:
        user = message.reply_to_message.from_user
    elif len(message.command) > 1:
        user = await extract_user(message, client)

    if not user:
        return await message.reply_text(_["general_1"])

    if user.id in SUDOERS:
        return await message.reply_text(_["sudo_1"].format(user.mention))
    
    added = await DvisPappa.add_sudo(user.id)
    if added:
        SUDOERS.add(user.id)
        await message.reply_text(_["sudo_2"].format(user.mention))
    else:
        await message.reply_text(_["sudo_8"])


@Client.on_message(filters.command(["delsudo", "rmsudo"]) & filters.user(Config.ADMIN))
@language
async def userdel(client: Client, message: Message, _):
    user = None
    if message.reply_to_message:
        user = message.reply_to_message.from_user
    elif len(message.command) > 1:
        user = await extract_user(message, client)

    if not user:
        return await message.reply_text(_["general_1"])

    if user.id not in SUDOERS:
        return await message.reply_text(_["sudo_3"].format(user.mention))
    
    removed = await DvisPappa.remove_sudo(user.id)
    if removed:
        SUDOERS.remove(user.id)
        await message.reply_text(_["sudo_4"].format(user.mention))
    else:
        await message.reply_text(_["sudo_8"])


@Client.on_message(filters.command(["sudolist", "listsudo", "sudoers"]) & ~filters.user(Config.ADMIN))
@language
async def sudoers_list(client: Client, message: Message, _):
    text = _["sudo_5"]
    
    owner_user = await client.get_users(Config.ADMIN)
    owner_mention = owner_user.first_name if not owner_user.mention else owner_user.mention
    text += f"❖ {owner_mention}\n"
    
    count = 0
    smex = 0
    
    for user_id in SUDOERS:
        if user_id != Config.ADMIN:
            try:
                user = await client.get_users(user_id)
                user_mention = user.first_name if not user.mention else user.mention
                
                if smex == 0:
                    smex += 1
                    text += _["sudo_6"]
                
                count += 1
                text += f"❖ {count} ➥ {user_mention}\n"
            except Exception:
                continue
    
    if count == 0 and smex == 0:
        await message.reply_text(_["sudo_7"], reply_markup=close_markup(_))
    else:
        await message.reply_text(text, reply_markup=close_markup(_))
