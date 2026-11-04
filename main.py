import os
import asyncio
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN
import database as db
from handlers import admin, vip, registration, chat

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Bepul serverlar (Render, Koyeb) uchun keep-alive veb-server
async def handle_ping(request):
    return web.Response(text="Bot 24/7 faol ishlamoqda!")

async def start_web_server():
    port = int(os.getenv("PORT", 8080))
    app = web.Application()
    app.router.add_get("/", handle_ping)
    app.router.add_get("/health", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Keep-alive veb-server {port}-portda ishga tushdi.")

async def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN aniqlanmadi! .env faylini tekshiring.")
        return

    # Ma'lumotlar bazasini ishga tushirish
    logger.info("Ma'lumotlar bazasi tayyorlanmoqda...")
    await db.init_db()

    # Veb-serverni fon rejimida ishga tushirish (Render/Koyeb 24/7 ishlashi uchun)
    try:
        await start_web_server()
    except Exception as e:
        logger.warning(f"Veb serverni ishga tushirishda ogohlantirish: {e}")

    # Bot va Dispatcher yaratish
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # Routerlarni ulash
    dp.include_router(admin.router)
    dp.include_router(vip.router)
    dp.include_router(registration.router)
    dp.include_router(chat.router)

    # Eski yangilanishlarni tozalash
    await bot.delete_webhook(drop_pending_updates=True)

    logger.info("Bot muvaffaqiyatli ishga tushdi!")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
