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


@admin.message(F.text.lower() == "посмотреть заявки")
async def look_all_forms_handler(message: Message):
    users = await DF.get_unverified_users()
    if not users:
        await message.answer("Нет неверифицированных аккаунтов")
        return

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[], row_width=1)
    for user_id, name in users:
        button = [
            [types.InlineKeyboardButton(text=name, callback_data=f"opinion_:{user_id}")]
        ]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=button)

    await message.answer("Вот все неверифицированные аккаунты:", reply_markup=keyboard)


@admin.callback_query(lambda callback_query: callback_query.data.startswith("opinion_:"))
async def opinion_handler(query: CallbackQuery):
    opinion_id = int(query.data.split(":")[1])
    print(opinion_id)
    opinion = await DF.get_user_by_id(str(opinion_id))
    if not opinion:
        await query.answer("Пользователь не найден", show_alert=True)
        return

    photo_file_id = opinion.get('profile_photo_file_id')
    video_file_id = opinion.get('profile_video_file_id')
    photos = await DF.get_all_additional_photos(str(opinion_id))
    collage_buffer = await DF.get_collage_file_id(str(opinion_id))
    print(f'photo {photo_file_id}')
    print(f'video {video_file_id}')

    # Формируем сообщение с информацией о жалобе и профиле
    message_text = f"<b>Информация о профиле:</b>\n" \
                   f"<b>Имя:</b> {opinion['first_name']}\n" \
                   f"<b>Возраст:</b> {opinion['age']}\n" \
                   f"<b>Пол:</b> {opinion['gender']}\n" \
                   f"<b>Город:</b> {opinion['city']}\n" \
                   f"<b>О себе:</b> {opinion['about_me']}"
    if photos.get('profile_photo_file_id_2') or photos.get('profile_photo_file_id_3'):
        if collage_buffer:
            print(collage_buffer)
            await bot.send_photo(chat_id=query.message.chat.id,
                                 photo=collage_buffer, caption=message_text,
                                 reply_markup=await K.admin_keyboard_notification_with_user_id(
                                     str(opinion_id)),
                                 parse_mode="HTML")
        else:
            collage_buffer = await create_collage([photos.get('profile_photo_file_id'),
                                                   photos.get('profile_photo_file_id_2'),
                                                   photos.get('profile_photo_file_id_3')],
                                                  chat_for_save_file_id)
            await DF.save_collage_file_id(str(opinion_id), collage_buffer)
            await bot.send_photo(chat_id=query.message.chat.id,
                                 photo=collage_buffer, caption=message_text,
                                 reply_markup=await K.admin_keyboard_notification_with_user_id(
                                     str(opinion_id)),
                                 parse_mode="HTML"
                                 )
    elif photos.get('profile_photo_file_id_2') and photos.get('profile_photo_file_id_3'):
        if collage_buffer:
            print(collage_buffer)
            await bot.send_photo(chat_id=query.message.chat.id,
                                 photo=collage_buffer, caption=message_text,
                                 reply_markup=await K.admin_keyboard_notification_with_user_id(str(opinion_id)),
                                 parse_mode="HTML")
        else:
            collage_buffer = await create_collage([photos.get('profile_photo_file_id'),
                                                   photos.get('profile_photo_file_id_2'),
                                                   photos.get('profile_photo_file_id_3')],
                                                  chat_for_save_file_id)
            await DF.save_collage_file_id(str(opinion_id), collage_buffer)
            await bot.send_photo(chat_id=query.message.chat.id,
                                 photo=collage_buffer, caption=message_text,
                                 reply_markup=await K.admin_keyboard_notification_with_user_id(str(opinion_id)),
                                 parse_mode="HTML")
    elif photo_file_id:
        await query.bot.send_photo(
            chat_id=query.message.chat.id,
            photo=photo_file_id,
            caption=message_text,
            parse_mode="HTML",
            reply_markup=await K.admin_keyboard_notification_with_user_id(str(opinion_id))
        )
    elif video_file_id:
        await query.bot.send_video(
            chat_id=query.message.chat.id,
            video=video_file_id,
            caption=message_text,
            parse_mode="HTML",
            reply_markup=await K.admin_keyboard_notification_with_user_id(str(opinion_id))
        )
    else:
        await query.message.answer(message_text, parse_mode="HTML",
                                   reply_markup=await K.admin_keyboard_notification_with_user_id(str(opinion_id)))


@admin.callback_query(lambda callback_query: callback_query.data.startswith("confirm_opinion:"))
async def confirm_opinion_handler(query: CallbackQuery):
    opinion_id = str(query.data.split(":")[1])

    if opinion_id:
        await DF.update_user_verify_status(opinion_id, True)

        await bot.send_message(opinion_id, "Ваш профиль успешно подтвержден. "
                                           "Теперь вы можете получить доступ к этой функции.",
                               reply_markup=await K.keyboard_for_user())
        await query.message.answer("Аккаунт успешно подтвержден ")
    else:
        await query.message.answer("Ошибка: Не удалось найти запрос на верификацию.")


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
                                             reply_markup=await K.admin_keyboard_notification_complaint(
                                                 str({complaint['complained_user_id']})))
        else:
            collage_buffer = await create_collage([photos.get('profile_photo_file_id'),
                                                   photos.get('profile_photo_file_id_2'),
                                                   photos.get('profile_photo_file_id_3')],
                                                  chat_for_save_file_id)
            await DF.save_collage_file_id(complaint["complained_user_id"], collage_buffer)
            await query.message.answer_photo(photo=collage_buffer, caption=message_text,
                                             reply_markup=await K.admin_keyboard_notification_complaint(
                                                 str({complaint['complained_user_id']})))
    elif photos.get('profile_photo_file_id_2') and photos.get('profile_photo_file_id_3'):
        if collage_buffer:
            print(collage_buffer)
            await query.message.answer_photo(photo=collage_buffer, caption=message_text,
                                             reply_markup=await K.admin_keyboard_notification_complaint(
                                                 str({complaint['complained_user_id']})))
        else:
            collage_buffer = await create_collage([photos.get('profile_photo_file_id'),
                                                   photos.get('profile_photo_file_id_2'),
                                                   photos.get('profile_photo_file_id_3')],
                                                  chat_for_save_file_id)
            await DF.save_collage_file_id(complaint["complained_user_id"], collage_buffer)
            await query.message.answer_photo(photo=collage_buffer, caption=message_text,
                                             reply_markup=await K.admin_keyboard_notification_complaint(
                                                 str({complaint['complained_user_id']})))
    elif photo_file_id:
        await query.bot.send_photo(
            chat_id=query.message.chat.id,
            photo=photo_file_id,
            caption=message_text,
            parse_mode="HTML",
            reply_markup=await K.admin_keyboard_notification_complaint(str({complaint['complained_user_id']}))
        )
    elif video_file_id:
        await query.bot.send_video(
            chat_id=query.message.chat.id,
            video=video_file_id,
            caption=message_text,
            parse_mode="HTML",
            reply_markup=await K.admin_keyboard_notification_complaint(str({complaint['complained_user_id']}))
        )
    else:
        await query.message.answer(message_text, parse_mode="HTML",
                                   reply_markup=await K.admin_keyboard_notification_complaint(
                                       str({complaint['complained_user_id']})))


@admin.callback_query(F.data == "confirm_form")
async def confirm_form_handler(query: CallbackQuery):
    user_id = await DF.get_verification_request_user_id()

    if user_id:
        await DF.update_user_verify_status(user_id, True)

        await bot.send_message(user_id, "Ваш профиль успешно подтвержден. "
                                        "Теперь вы можете получить доступ к этой функции.",
                               reply_markup=await K.keyboard_for_user())
        await query.message.answer("Аккаунт успешно подтвержден ")
    else:
        await query.message.answer("Ошибка: Не удалось найти запрос на верификацию.")


@admin.callback_query(F.data == "send_for_editing")
async def send_for_editing_handler(query: CallbackQuery):
    user_id = await DF.get_verification_request_user_id()

    if user_id:
        await DF.clear_user_columns(user_id)
        await bot.send_message(int(user_id), "Ваш профиль нуждается в редактировании."
                                             " Пожалуйста, проверьте и обновите при необходимости.",
                               reply_markup=await K.start_key())
        await query.message.answer("Сообщение отправлено пользователю")
    else:
        await query.message.answer("Ошибка: Не удалось найти запрос на верификацию."
                                   "Попробуйте через админ-панель")


@admin.callback_query(lambda callback_query: callback_query.data.startswith("confirm_block"))
async def confirm_complaint_handler(query: CallbackQuery):
    complaint_user_id = query.data.split(":")[1]
    complaint_user_id = complaint_user_id.replace("{", "").replace("}", "")
    complaint_user_id = complaint_user_id.replace("'", "")
    print(complaint_user_id)

    await DF.update_complaint_status_by_user_id(str(complaint_user_id), 'TRUE')

    complaint = await DF.get_complaint_by_user_id(str(complaint_user_id))
    if complaint is None:
        print("Complaint not found.")
        await query.answer("Ошибка при получении жалобы.")
        return

    try:
        user = await bot.get_chat(int(complaint['user_id']))
        complained_user = await bot.get_chat(int(complaint['complained_user_id']))
    except Exception as e:
        print(f"Error while getting user data: {e}")
        await query.answer("Ошибка при получении данных пользователей.")
        return

    await bot.send_message(
        complaint['complained_user_id'],
        f"Жалоба от @{user.username} была рассмотрена.",
        reply_markup=await K.keyboard_for_user()
    )

    await query.answer("Жалоба рассмотрена. Отправлено пользователю.")


@admin.callback_query(lambda callback_query: callback_query.data.startswith("block_reject"))
async def reject_complaint_handler(query: CallbackQuery):
    print('Я В BLOCK REJECT')
    complaint_id = query.data.split(":")[1]
    complaint_id = complaint_id.replace("{", "").replace("}", "")
    complaint_id = complaint_id.replace("'", "")
    print(complaint_id)

    await DF.update_complaint_status_by_user_id(str(complaint_id), 'REJECTED')

    complaint = await DF.get_complaint_by_user_id(str(complaint_id))
    if complaint is None:
        print("Complaint not found.")
        await query.answer("Ошибка при получении жалобы.")
        return

    try:
        user = await bot.get_chat(int(complaint['user_id']))
        complained_user = await bot.get_chat(int(complaint['complained_user_id']))
    except Exception as e:
        print(f"Error while getting user data: {e}")
        await query.answer("Ошибка при получении данных пользователей.")
        return
    print(complaint_id)
    print(complaint['user_id'])

    await bot.send_message(
        complaint['complained_user_id'],
        f"Жалоба от @{user.username} была отклонена.",
        reply_markup=await K.keyboard_for_user()
    )

    await query.answer("Жалоба отклонена. Отправлено пользователю.")


@admin.callback_query(F.data.startswith("ban:"))
async def ban_handler(query: CallbackQuery):
    blocker_id = query.message.chat.id
    blocked_id = query.data.split(":")[1]

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
