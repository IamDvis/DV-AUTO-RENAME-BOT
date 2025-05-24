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

    LOGGER.info("Attempting to load sudoers...")
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
        LOGGER.info(f"Fetched {len(sudoers_list_from_db)} sudoers from database.")

        updated_sudoers_list_for_db = list(sudoers_list_from_db)
        
        changes_made_to_db_list = False
        for admin_id in Config.ADMIN:
            if isinstance(admin_id, int) and admin_id not in updated_sudoers_list_for_db:
                LOGGER.info(f"Configured ADMIN ID {admin_id} not in database sudoers list. Adding now.")
                updated_sudoers_list_for_db.append(admin_id)
                changes_made_to_db_list = True
        
        if changes_made_to_db_list:
            await DvisPappa.sudoers_col.update_one(
                {"sudo": "sudo"},
                {"$set": {"sudoers": updated_sudoers_list_for_db}},
                upsert=True,
            )
            LOGGER.info("Database sudoers list updated with configured ADMIN IDs.")
            sudoers_list_from_db = await DvisPappa.get_sudoers()


        if sudoers_list_from_db:
            for user_id in sudoers_list_from_db:
                if isinstance(user_id, int):
                    SUDOERS.add(user_id)
                else:
                    LOGGER.warning(f"Skipping non-integer sudoer ID from database: {user_id} (Type: {type(user_id)})")
            LOGGER.info(f"Final SUDOERS set populated with {len(SUDOERS)} users after database sync.")

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

