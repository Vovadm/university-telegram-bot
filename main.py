import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
from sqlalchemy import text

from app.handlers import router
from db.universiries import SessionLocalUniversity
from db.users import async_main, create_tables, SessionLocalUsers


async def keep_db_connection_alive():
    while True:
        async with SessionLocalUsers() as session:
            await session.execute(text("SELECT 1"))
            print("reconnect to users")
        async with SessionLocalUniversity as session:
            await session.execute(text("SELECT 1"))
            print("reconnect to univ")
        await asyncio.sleep(300)


async def main():
    await create_tables()
    load_dotenv()
    await async_main()
    bot = Bot(token=os.getenv("TOKEN"))
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)
    asyncio.create_task(keep_db_connection_alive())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exit")
