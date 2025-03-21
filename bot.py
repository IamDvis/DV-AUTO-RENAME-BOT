from datetime import datetime
from pytz import timezone
from pyrogram import Client, __version__
from pyrogram.raw.all import layer
from config import Config
from aiohttp import web
from route import web_server
import pyrogram.utils

# Kuch utility values set kar rahe hain
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

    async def start(self):
        await super().start()
        me = await self.get_me()
        self.mention = me.mention
        self.username = me.username
        self.uptime = Config.BOT_UPTIME
        if Config.WEBHOOK:
            # Webhook setup
            app_runner = web.AppRunner(await web_server())
            await app_runner.setup()
            await web.TCPSite(app_runner, "0.0.0.0", 8080).start()
        print(f"{me.first_name} Is Started.....✨️")
        for admin_id in Config.ADMIN:
            try:
                await self.send_message(Config.LOG_CHANNEL, f"**{me.first_name} Is Started.....✨️**")
            except Exception:
                pass
        if Config.LOG_CHANNEL:
            try:
                curr = datetime.now(timezone("Asia/Kolkata"))
                date_str = curr.strftime('%d %B, %Y')
                time_str = curr.strftime('%I:%M:%S %p')
                await self.send_message(
                    Config.LOG_CHANNEL,
                    f"**{me.mention} Is Restarted !!**\n\n Date : `{date_str}`\n⏰ Time : `{time_str}`\n Timezone : `Asia/Kolkata`\n\n Version : `v{__version__} (Layer {layer})`"
                )
            except Exception:
                print("Please Make This Is Admin In Your Log Channel")

    async def stop(self):
        # Override stop() to ensure ye async coroutine return kare
        await super().stop()

if __name__ == "__main__":
    Bot().run()
