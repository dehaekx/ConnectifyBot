""" Второй экземпляр бота для работы со скриптами"""


from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config_data.config import TOKEN

bot = Bot(TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
