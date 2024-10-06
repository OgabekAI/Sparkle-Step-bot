import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.session.middlewares.request_logging import logger
from aiogram.client.default import DefaultBotProperties
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from handlers.users.main_hand import router
from handlers.users.admin_private import routerAD
from database.models import async_main
from aiogram.methods import DeleteWebhook
from settings import BOT_TOKEN



def setup_middlewares(dispatcher: Dispatcher, bot: Bot) -> None:
    """MIDDLEWARE"""
    from middlewares.throttling import ThrottlingMiddleware

    dispatcher.message.middleware(ThrottlingMiddleware(slow_mode_delay=1))

async def aiogram_on_startup_polling(dispatcher: Dispatcher, bot: Bot) -> None:
    from utils.set_bot_commands import set_default_commands
    from utils.notify_admins import on_startup_notify

    logger.info("Database connected")
    logger.info("Starting polling")
    await bot.delete_webhook(drop_pending_updates=True)
    await on_startup_notify(bot=bot)
    await set_default_commands(bot=bot)


async def setup_aiogram(dispatcher: Dispatcher, bot: Bot) -> None:
    logger.info("Configuring aiogram")
    setup_middlewares(dispatcher=dispatcher, bot=bot)
    logger.info("Configured aiogram")


async def aiogram_on_shutdown_polling(dispatcher: Dispatcher, bot: Bot):
    logger.info("Stopping polling")
    await bot.session.close()
    await dispatcher.storage.close()


async def main():
    """CONFIG"""

    bot = Bot(token=BOT_TOKEN,  default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dispatcher = Dispatcher()

    dispatcher.include_router(routerAD)
    dispatcher.include_router(router)

    dispatcher.startup.register(aiogram_on_startup_polling)
    dispatcher.shutdown.register(aiogram_on_shutdown_polling)
    await bot(DeleteWebhook(drop_pending_updates=True))
    await async_main()
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped!")
