from aiogram import Bot
from aiogram.enums.parse_mode import ParseMode
from settings import BOT_TOKEN

from aiogram.client.default import DefaultBotProperties


bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
