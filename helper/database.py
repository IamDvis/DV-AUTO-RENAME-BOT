import logging
import motor.motor_asyncio
from config import Config
from .utils import send_log

LOGGER = logging.getLogger(__name__)

class Database:
    def __init__(self, uri: str, database_name: str):
        try:
            self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
            self.DvisPappa = self._client[database_name]

            self.col = self.DvisPappa.user
            self.sudoers_col = self.DvisPappa.sudoers
            self.settings_col = self.DvisPappa.user_settings

            self._client.admin.command('ping')
            LOGGER.info("Database initialized successfully.")
        except Exception as e:
            LOGGER.error(f"Failed to initialize database: {e}")
            self._client = None
            raise

    def new_user(self, id: int) -> dict:
        return dict(
            _id=int(id),
            file_id=None,
            caption=None,
            format_template=None,
            media_type=None
        )

    async def add_user(self, b, m):
        u = m.from_user
        if not await self.is_user_exist(u.id):
            user = self.new_user(u.id)
            await self.col.insert_one(user)
            await send_log(b, u)
            LOGGER.info(f"New user added: {u.id}")

    async def is_user_exist(self, user_id: int) -> bool:
        user = await self.col.find_one({'_id': int(user_id)})
        return bool(user)

    async def total_users_count(self) -> int:
        count = await self.col.count_documents({})
        return count

    async def get_all_users(self):
        all_users = self.col.find({})
        return all_users

    async def delete_user(self, user_id: int):
        await self.col.delete_many({'_id': int(user_id)})
        LOGGER.info(f"User {user_id} deleted from database.")

    async def set_thumbnail(self, user_id: int, file_id: str):
        await self.col.update_one({'_id': int(user_id)}, {'$set': {'file_id': file_id}}, upsert=True)
        LOGGER.debug(f"Thumbnail set for user {user_id}.")

    async def get_thumbnail(self, user_id: int):
        user = await self.col.find_one({'_id': int(user_id)})
        return user.get('file_id', None)

    async def set_caption(self, user_id: int, caption: str):
        await self.col.update_one({'_id': int(user_id)}, {'$set': {'caption': caption}}, upsert=True)
        LOGGER.debug(f"Caption set for user {user_id}.")

    async def get_caption(self, user_id: int):
        user = await self.col.find_one({'_id': int(user_id)})
        return user.get('caption', None)

    async def set_format_template(self, user_id: int, format_template: str):
        await self.col.update_one({'_id': int(user_id)}, {'$set': {'format_template': format_template}}, upsert=True)
        LOGGER.debug(f"Format template set for user {user_id}.")

    async def get_format_template(self, user_id: int):
        user = await self.col.find_one({'_id': int(user_id)})
        return user.get('format_template', None)

    async def set_media_preference(self, user_id: int, media_type: str):
        await self.col.update_one({'_id': int(user_id)}, {'$set': {'media_type': media_type}}, upsert=True)
        LOGGER.debug(f"Media preference set for user {user_id}.")

    async def get_media_preference(self, user_id: int):
        user = await self.col.find_one({'_id': int(user_id)})
        return user.get('media_type', None)

    async def get_sudoers(self) -> list:
        sudoers_doc = await self.sudoers_col.find_one({"sudo": "sudo"})
        return sudoers_doc.get("sudoers", []) if sudoers_doc else []

    async def add_sudo(self, user_id: int) -> bool:
        sudoers = await self.get_sudoers()
        if user_id not in sudoers:
            sudoers.append(user_id)
            await self.sudoers_col.update_one(
                {"sudo": "sudo"}, {"$set": {"sudoers": sudoers}}, upsert=True
            )
            LOGGER.info(f"User {user_id} added to sudoers.")
            return True
        LOGGER.info(f"User {user_id} is already a sudoer.")
        return False

    async def remove_sudo(self, user_id: int) -> bool:
        sudoers = await self.get_sudoers()
        if user_id in sudoers:
            sudoers.remove(user_id)
            await self.sudoers_col.update_one(
                {"sudo": "sudo"}, {"$set": {"sudoers": sudoers}}, upsert=True
            )
            LOGGER.info(f"User {user_id} removed from sudoers.")
            return True
        LOGGER.info(f"User {user_id} is not a sudoer.")
        return False

DvisPappa = Database(Config.DB_URL, Config.DB_NAME)
