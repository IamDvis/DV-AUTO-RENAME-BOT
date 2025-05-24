import logging
from config import Config
from .database import DvisPappa
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from functools import wraps

OWNER_ID = Config.ADMIN

SUDOERS = set()

LOGGER = logging.getLogger(__name__)

UNAUTHORIZED_MESSAGE_TEXT = (
    "🚫 ᴀᴘ ɪꜱ ʙσᴛ ᴋσ ᴜꜱє ᴋᴧʀηє ᴋє ʟᴧʏᴧᴋ ηᴧʜɪη ʜᴧɪη. ǫ ηʜɪ ʜ ᴊᴧηηє ᴋє ʟɪʏє.\n"
    "ᴋʀɪᴘᴧʏᴧ σᴡηєʀ ꜱє ꜱᴧϻᴘᴧʀᴋ ᴋᴧʀєɪη."
)

UNAUTHORIZED_MESSAGE_MARKUP = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton(
                "✿ σᴡηєʀ ✿",
                url="https://t.me/DvisDmBot?start"
            )
        ]
    ]
)

async def sudo():
    global SUDOERS

    if DvisPappa._client is None:
        LOGGER.error("Database client is not initialized in DvisPappa. Cannot load sudoers.")
        return

    try:
        SUDOERS.add(OWNER_ID)

        sudoers_list = await DvisPappa.get_sudoers()

        if OWNER_ID not in sudoers_list:
            await DvisPappa.add_sudo(OWNER_ID)
            sudoers_list = await DvisPappa.get_sudoers()

        if sudoers_list:
            for user_id in sudoers_list:
                SUDOERS.add(user_id)

        LOGGER.info(f"✦ Sudoers Loaded: {len(SUDOERS)} users. ❤️")

    except Exception as e:
        LOGGER.error(f"Error loading sudoers: {e}")

async def is_user_sudo(user_id: int) -> bool:
    return user_id in SUDOERS

def chksudo(func):
    @wraps(func)
    async def wrapper(client, message, *args, **kwargs):
        if not message.from_user:
            return
        
        user_id = message.from_user.id
        
        if not await is_user_sudo(user_id):
            await message.reply_text(
                UNAUTHORIZED_MESSAGE_TEXT,
                reply_markup=UNAUTHORIZED_MESSAGE_MARKUP
            )
            return
        
        return await func(client, message, *args, **kwargs)
    return wrapper

