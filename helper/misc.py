import logging
from config import Config
from .database import DvisPappa
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from functools import wraps

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

    LOGGER.info("Attempting to load sudoers...")
    if DvisPappa._client is None:
        LOGGER.error("DvisPappa client is None. Database connection failed earlier. Cannot load sudoers.")
        return

    try:
        if not isinstance(Config.ADMIN, int):
            LOGGER.error(f"Config.ADMIN is not an integer: {type(Config.ADMIN)}. Please check config.py.")
            try:
                converted_admin_id = int(Config.ADMIN)
                SUDOERS.add(converted_admin_id)
                LOGGER.warning(f"Converted Config.ADMIN to integer: {converted_admin_id}")
            except ValueError:
                LOGGER.error("Config.ADMIN cannot be converted to an integer. Sudoers loading will be incomplete.")
                return
        else:
            SUDOERS.add(Config.ADMIN)
        LOGGER.info(f"Owner ID {Config.ADMIN} added to SUDOERS set temporarily.")


        sudoers_list = await DvisPappa.get_sudoers()
        LOGGER.info(f"Fetched {len(sudoers_list)} sudoers from database.")

        if Config.ADMIN not in sudoers_list:
            LOGGER.info(f"Owner ID {Config.ADMIN} not in database sudoers list. Adding now.")
            await DvisPappa.add_sudo(Config.ADMIN)
            sudoers_list = await DvisPappa.get_sudoers()
            LOGGER.info("Owner ID added to database sudoers.")

        if sudoers_list:
            for user_id in sudoers_list:
                if isinstance(user_id, int):
                    SUDOERS.add(user_id)
                else:
                    LOGGER.warning(f"Skipping non-integer sudoer ID from database: {user_id} (Type: {type(user_id)})")
            LOGGER.info(f"Final SUDOERS set populated with {len(SUDOERS)} users.")

        LOGGER.info(f"✦ Sudoers Loaded successfully. Total: {len(SUDOERS)} users. ❤️")

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
            LOGGER.info(f"Non-sudo user {user_id} tried to use a sudo-only command.")
            await message.reply_text(
                UNAUTHORIZED_MESSAGE_TEXT,
                reply_markup=UNAUTHORIZED_MESSAGE_MARKUP
            )
            return
        
        return await func(client, message, *args, **kwargs)
    return wrapper

