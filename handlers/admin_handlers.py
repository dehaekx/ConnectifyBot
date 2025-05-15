from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery, InputMediaPhoto

from config_data.config import chat_for_save_file_id
from keyboards import keyboards as K
from utils import db_functions as DF
from utils.copy_bot import bot
from utils.image_collage import create_collage

admin = Router()


@admin.message(F.text.lower() == "админ-панель")
async def admin_panel_handler(message: Message):
    await message.answer("Добро пожаловать в Админ-панель", reply_markup=await K.admin_keyboard())


@admin.message(F.text.lower() == "посмотреть жалобы")
async def look_all_complaint_handler(message: Message):
    complaints = await DF.get_unchecked_complaints()
    if not complaints:
        await message.answer("Нет непроверенных жалоб")
        return

    keyboard = types.InlineKeyboardMarkup(row_width=1, inline_keyboard=[])
    for complaint_id, user_id, complained_user_id, reason in complaints:
        button = [
            [types.InlineKeyboardButton(text=f"Жалоба от {user_id} на {complained_user_id}",
                                        callback_data=f"view_:{complaint_id}")]
        ]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=button)

    await message.answer("Вот все непроверенные жалобы:", reply_markup=keyboard)


@admin.callback_query(lambda callback_query: callback_query.data.startswith("view_:"))
async def view_complaint_handler(query: CallbackQuery):
    complaint_id = int(query.data.split(":")[1])

    # Получаем информацию о жалобе из базы данных
    complaint = await DF.get_complaint_by_id(complaint_id)
    if not complaint:
        await query.answer("Жалоба не найдена", show_alert=True)
        return
    print(complaint_id)
    # Получаем информацию о профиле того, на кого жаловались
    complained_user = await DF.get_user_by_id(complaint["complained_user_id"])
    print(complained_user)
    if not complained_user:
        await query.answer("Пользователь не найден", show_alert=True)
        return

    photo_file_id = complained_user.get('profile_photo_file_id')
    video_file_id = complained_user.get('profile_video_file_id')
    photos = await DF.get_all_additional_photos(complaint["complained_user_id"])
    collage_buffer = await DF.get_collage_file_id(complaint["complained_user_id"])
    print(f'photo {photo_file_id}')
    print(f'video {video_file_id}')

    # Формируем сообщение с информацией о жалобе и профиле
    message_text = f"<b>Жалоба от:</b> {complaint['user_id']}\n" \
                   f"<b>На:</b> {complaint['complained_user_id']}\n" \
                   f"<b>Причина:</b> {complaint['reason']}\n\n" \
                   f"<b>Информация о профиле:</b>\n" \
                   f"<b>Имя:</b> {complained_user['first_name']}\n" \
                   f"<b>Возраст:</b> {complained_user['age']}\n" \
                   f"<b>Пол:</b> {complained_user['gender']}\n" \
                   f"<b>Город:</b> {complained_user['city']}\n" \
                   f"<b>О себе:</b> {complained_user['about_me']}"

    if photos.get('profile_photo_file_id_2') or photos.get('profile_photo_file_id_3'):
        if collage_buffer:
            print(collage_buffer)
            await query.message.answer_photo(photo=collage_buffer, caption=message_text,
                                             reply_markup=await K.admin_keyboard_ban_decision(
                                                 str({complaint['complained_user_id']})))
        else:
            collage_buffer = await create_collage([photos.get('profile_photo_file_id'),
                                                   photos.get('profile_photo_file_id_2'),
                                                   photos.get('profile_photo_file_id_3')],
                                                  chat_for_save_file_id)
            await DF.save_collage_file_id(complaint["complained_user_id"], collage_buffer)
            await query.message.answer_photo(photo=collage_buffer, caption=message_text,
                                             reply_markup=await K.admin_keyboard_ban_decision(
                                                 str({complaint['complained_user_id']})))
    elif photos.get('profile_photo_file_id_2') and photos.get('profile_photo_file_id_3'):
        if collage_buffer:
            print(collage_buffer)
            await query.message.answer_photo(photo=collage_buffer, caption=message_text,
                                             reply_markup=await K.admin_keyboard_ban_decision(
                                                 str({complaint['complained_user_id']})))
        else:
            collage_buffer = await create_collage([photos.get('profile_photo_file_id'),
                                                   photos.get('profile_photo_file_id_2'),
                                                   photos.get('profile_photo_file_id_3')],
                                                  chat_for_save_file_id)
            await DF.save_collage_file_id(complaint["complained_user_id"], collage_buffer)
            await query.message.answer_photo(photo=collage_buffer, caption=message_text,
                                             reply_markup=await K.admin_keyboard_ban_decision(
                                                 str({complaint['complained_user_id']})))
    elif photo_file_id:
        await query.bot.send_photo(
            chat_id=query.message.chat.id,
            photo=photo_file_id,
            caption=message_text,
            parse_mode="HTML",
            reply_markup=await K.admin_keyboard_ban_decision(str({complaint['complained_user_id']}))
        )
    elif video_file_id:
        await query.bot.send_video(
            chat_id=query.message.chat.id,
            video=video_file_id,
            caption=message_text,
            parse_mode="HTML",
            reply_markup=await K.admin_keyboard_ban_decision(str({complaint['complained_user_id']}))
        )
    else:
        await query.message.answer(message_text, parse_mode="HTML",
                                   reply_markup=await K.admin_keyboard_ban_decision(
                                       str({complaint['complained_user_id']})))


@admin.callback_query(F.data.startswith("ban:"))
async def ban_handler(query: CallbackQuery):
    blocker_id = query.message.chat.id
    blocked_id = query.data.split(":")[1].strip().replace("{", "").replace("}", "").replace("'", "").strip()

    try:
        user = await bot.get_chat(int(blocked_id))
        username = user.username
    except Exception as e:
        print(f"Error while getting user data: {e}")
        username = "Unknown"

    try:
        await DF.insert_block(str(blocker_id), str(blocked_id))
        await query.message.answer(f"Пользователь @{username} забанен.")
    except Exception as e:
        print(f"Error while banning user: {e}")
        await query.message.answer("Не удалось забанить пользователя.")


@admin.callback_query(F.data.startswith("dont_ban:"))
async def dont_ban_handler(query: CallbackQuery):
    user_id = query.data.split(":")[1]

    try:
        user = await bot.get_chat(int(user_id))
        username = user.username
    except Exception as e:
        print(f"Error while getting user data: {e}")
        username = "Unknown"

    await query.message.answer(f"Не блокировать пользователя @{username}.")
