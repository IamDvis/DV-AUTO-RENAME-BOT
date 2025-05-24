import logging
from config import Config
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from functools import wraps

from .database import DvisPappa

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
        LOGGER.error("DvisPappa client is None. Database connection failed earlier. Cannot load sudoers.")
        return

    try:
        SUDOERS.clear()

        for admin_id in Config.ADMIN:
            if isinstance(admin_id, int):
                SUDOERS.add(admin_id)
            else:
                LOGGER.warning(f"Skipping non-integer ADMIN ID from Config: {admin_id} (Type: {type(admin_id)})")

        sudoers_list_from_db = await DvisPappa.get_sudoers()

        combined_sudoers_for_db = set(SUDOERS)
        for user_id in sudoers_list_from_db:
            if isinstance(user_id, int):
                combined_sudoers_for_db.add(user_id)
            else:
                LOGGER.warning(f"Skipping non-integer sudoer ID from database during combine: {user_id} (Type: {type(user_id)})")
        
        await DvisPappa.sudoers_col.update_one(
            {"sudo": "sudo"},
            {"$set": {"sudoers": list(combined_sudoers_for_db)}},
            upsert=True,
        )

        SUDOERS.update(user_id for user_id in combined_sudoers_for_db if isinstance(user_id, int))

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
            await message.reply_text(
                UNAUTHORIZED_MESSAGE_TEXT,
                reply_markup=UNAUTHORIZED_MESSAGE_MARKUP
            )
            return
        
        return await func(client, message, *args, **kwargs)
    return wrapper

