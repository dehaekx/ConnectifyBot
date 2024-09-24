import json
import os
import sys

import asyncio
import logging

import asyncpg
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.utils.markdown import hbold
from aiogram.fsm.storage.memory import MemoryStorage

from config_data.config import TOKEN
from handlers import user_handlers
from handlers import admin_handlers
from keyboards import keyboards as K

from utils import db_functions as DF

bot = Bot(TOKEN)

storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Подключаем роутеры
dp.include_router(user_handlers.user)
dp.include_router(admin_handlers.admin)

ADMIN_ID = str(json.loads(os.getenv('ADMIN_ID')))


@dp.message(CommandStart())
async def command_start_handler(message: Message):
    user_id = str(message.from_user.id)
    print(user_id)
    block_users = await DF.get_all_blocked_users()

    if user_id in block_users:
        return

    # Check if the user already exists in the database
    user_exists = await DF.check_user_exists(user_id)

    if not user_exists:
        print('not')
        is_admin = user_id in ADMIN_ID
        await DF.insert_user_id(user_id)
        if is_admin:
            await message.answer("Привет! Мы рады привествовать вас в нашем боте для знакомств 🤝\n\n"
                                 "Давайте начнем заполнять профиль, чтобы другие пользователи могли лучше узнать тебя ▶",
                                 reply_markup=await K.start_key_with_admin_not_register())
        else:
            await message.answer("Привет! Мы рады привествовать вас в нашем боте для знакомств 🤝\n\n"
                                 "Давайте начнем заполнять профиль, чтобы другие пользователи могли лучше узнать тебя ▶",
                                 reply_markup=await K.start_key())
    else:
        print('yes')
        is_admin = user_id in ADMIN_ID
        if is_admin:
            await message.answer("Привет! Мы рады привествовать вас в нашем боте для знакомств 🤝\n\n"
                                 "Давайте начнем заполнять профиль, чтобы другие пользователи могли лучше узнать тебя ▶",
                                 reply_markup=await K.start_key_with_admin())
        else:
            await message.answer("Привет! Мы рады привествовать вас в нашем боте для знакомств 🤝\n\n"
                                 "Давайте начнем заполнять профиль, чтобы другие пользователи могли лучше узнать тебя ▶",
                                 reply_markup=await K.keyboard_for_user())


async def main() -> None:
    # Создание БД & таблиц
    await DF.db_create()
    await DF.tables_create()
    DF.db_pool = await asyncpg.create_pool(DF.DATABASE_URL)
    # Запуск бота
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
