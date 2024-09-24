import os

from PIL import Image
from aiogram.types import FSInputFile

from utils.copy_bot import bot


async def create_collage(file_ids, chat_for_save_file_id):
    images = []
    image_paths = []

    for file_id in file_ids:
        if not file_id:
            continue

        file = await bot.get_file(file_id)
        file_path = file.file_path

        image_path = f'image_{file_id}.jpg'
        await bot.download_file(file_path=file_path, destination=image_path)
        images.append(Image.open(image_path))
        image_paths.append(image_path)

    if not images:
        return None

    widths, heights = zip(*(img.size for img in images))
    total_width = sum(widths)
    max_height = max(heights)
    collage = Image.new('RGB', (total_width, max_height))

    x_offset = 0
    for img in images:
        collage.paste(img, (x_offset, 0))
        x_offset += img.size[0]

    collage_path = 'collage.jpg'
    collage.save(collage_path, format='JPEG')

    photo = FSInputFile(collage_path)
    result = await bot.send_photo(chat_id=chat_for_save_file_id, photo=photo)
    file_id = result.photo[-1].file_id

    os.remove(collage_path)

    for image_path in image_paths:
        os.remove(image_path)

    return file_id
