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

    # Проверяем, заблокирован ли пользователь
    is_blocked = await DF.is_user_blocked(user_id)
    if is_blocked:
        await message.answer("❌ Вы были забанены навсегда и больше не можете пользоваться ботом.")
        return  # Останавливаем выполнение

    # Проверяем, есть ли пользователь в базе
    user_exists = await DF.check_user_exists(user_id)

    if not user_exists:
        is_admin = user_id in ADMIN_ID
        await DF.insert_user_id(user_id)
        if is_admin:
            await message.answer("Привет! Этот бот предназначен для знакомств\n"
                                 "Давай начнем знакомиться и начать общаться",
                                 reply_markup=await K.start_key_with_admin_not_register())
        else:
            await message.answer("Привет! Этот бот предназначен для знакомств\n"
                                 "Давай начнем знакомиться и начать общаться",
                                 reply_markup=await K.start_key())
    else:
        is_admin = user_id in ADMIN_ID
        user_filled = await DF.check_user_fields_filled(user_id)

        if not user_filled:
            if is_admin:
                await message.answer("Привет! Этот бот предназначен для знакомств\n"
                                     "Давай начнем знакомиться и начать общаться",
                                     reply_markup=await K.start_key_with_admin_not_register())
            else:
                await message.answer("Привет! Этот бот предназначен для знакомств\n"
                                     "Давай начнем знакомиться и начать общаться",
                                     reply_markup=await K.start_key())
            return

        if is_admin:
            await message.answer("Привет! Этот бот предназначен для знакомств\n"
                                 "Давай начнем знакомиться и начать общаться",
                                 reply_markup=await K.start_key_with_admin())
        else:
            await message.answer("Вы уже зарегистрированы!\n"
                                 "Привет! Этот бот предназначен для знакомств\n"
                                 "Давай начнем знакомиться и начать общаться",
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
