import os

from aiogram.types import FSInputFile

from config_data.config import chat_for_save_file_id
from utils.copy_bot import bot


async def save_user_photo(user_id, message_id, user_photo_file_id):
    """ Скачивает фото пользователя и сохраняем file_id """
    user_photo_file = await bot.get_file(user_photo_file_id)
    user_photo_file_path = user_photo_file.file_path

    user_photo_path = f'user_photo_{user_id}.jpg'
    await bot.download_file(file_path=user_photo_file_path, destination=user_photo_path)
    await bot.delete_message(user_id, message_id)

    image = FSInputFile(user_photo_path)
    result = await bot.send_photo(chat_for_save_file_id, photo=image)
    file_id = result.photo[-1].file_id
    os.remove(user_photo_path)
    return file_id


async def save_user_video(user_id, message_id, user_video_file_id):
    """ Скачивает video пользователя и сохраняем file_id """
    user_video_file = await bot.get_file(user_video_file_id)
    user_video_file_path = user_video_file.file_path

    user_video_path = f'user_video_{user_id}.mp4'
    await bot.download_file(file_path=user_video_file_path, destination=user_video_path)
    await bot.delete_message(user_id, message_id)

    video = FSInputFile(user_video_path)
    result = await bot.send_video(chat_for_save_file_id, video=video)
    file_id = result.video.file_id
    os.remove(user_video_path)
    return file_id
