import logging
from config import Config
from database import DvisPappa

OWNER_ID = Config.ADMIN

SUDOERS = set()

LOGGER = logging.getLogger(__name__)

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

