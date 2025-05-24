from datetime import datetime
from pytz import timezone
from pyrogram import Client, __version__
from pyrogram.raw.all import layer
from config import Config
from aiohttp import web
from route import web_server
import pyrogram.utils
import logging
from helper.database import DvisPappa
from helper.misc import sudo

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(name)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
LOGGER = logging.getLogger(__name__)

pyrogram.utils.MIN_CHAT_ID = -999999999999
pyrogram.utils.MIN_CHANNEL_ID = -1009999999999

class Bot(Client):
    def __init__(self):
        super().__init__(
            name="renamer",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            workers=200,
            plugins={"root": "plugins"},
            sleep_threshold=15,
        )
        self.LOGGER = logging.getLogger(f"{__name__}.Bot")

    async def start(self):
        await super().start()
        me = await self.get_me()
        self.mention = me.mention
        self.username = me.username
        self.uptime = datetime.now(timezone("Asia/Kolkata"))
        
        self.LOGGER.info(f"{me.first_name} Is Started.....✨️")

        self.LOGGER.info("Attempting to initialize database and load sudoers...")
        try:
            if DvisPappa._client is None:
                self.LOGGER.error("DvisPappa database client could not be initialized. Check DB_URL and DB_NAME in config.")
            else:
                self.LOGGER.info("Database connection established via DvisPappa instance.")
                await sudo()
                self.LOGGER.info("Sudoers loading process initiated and completed.")
        except Exception as e:
            self.LOGGER.error(f"Error during database or sudoers initialization: {e}")

        if hasattr(Config, 'WEBHOOK') and Config.WEBHOOK:
            try:
                app_runner = web.AppRunner(await web_server())
                await app_runner.setup()
                await web.TCPSite(app_runner, "0.0.0.0", 8080).start()
                self.LOGGER.info("Webhook server started.")
            except Exception as e:
                self.LOGGER.error(f"Error starting webhook server: {e}")

        if hasattr(Config, 'ADMIN') and Config.ADMIN:
            for admin_id in Config.ADMIN:
                try:
                    await self.send_message(admin_id, f"**{me.first_name} Is Started.....✨️**")
                except Exception as e:
                    self.LOGGER.warning(f"Could not send start message to admin {admin_id}: {e}")

        if hasattr(Config, 'LOG_CHANNEL') and Config.LOG_CHANNEL:
            try:
                curr = datetime.now(timezone("Asia/Kolkata"))
                date_str = curr.strftime('%d %B, %Y')
                time_str = curr.strftime('%I:%M:%S %p')
                await self.send_message(
                    Config.LOG_CHANNEL,
                    f"**{me.mention} Is Restarted !!**\n\n Date : `{date_str}`\n⏰ Time : `{time_str}`\n Timezone : `Asia/Kolkata`\n\n Version : `v{__version__} (Layer {layer})`"
                )
            except Exception as e:
                self.LOGGER.error(f"Please Make This Is Admin In Your Log Channel or check LOG_CHANNEL ID: {e}")

    async def stop(self):
        await super().stop()
        self.LOGGER.info("Bot stopped!")

if __name__ == "__main__":
    import asyncio
    Bot().run()

