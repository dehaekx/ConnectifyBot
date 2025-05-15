import json
import os

from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from config_data.config import chat_for_save_file_id
from handlers.user_functions import back_to_menu, update_interests_keyboard, send_notification_me
from keyboards import keyboards as K
from keyboards.keyboards import InterestFilter
from utils import states, db_functions as DF
from utils.copy_bot import bot
from utils.image_collage import create_collage
from utils.maps import INTERESTS_MAP, CITIES_RU
from utils.save_skip_users import load_skip_user_id, save_skip_user_id
from utils.scripts import save_user_photo, save_user_video

user = Router()

ADMIN_ID = json.loads(os.getenv('ADMIN_ID'))
last_viewed_user_id = None


@user.message(F.text.lower() == "начать")
async def start_registrate(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    print(user_id)
    is_blocked = await DF.is_user_blocked(user_id)
    if is_blocked:
        await message.answer("❌ Вы были забанены навсегда и больше не можете пользоваться ботом.")
        return
    profile_exists = await DF.check_user_fields_filled(user_id)
    print(profile_exists)
    if profile_exists:
        await message.answer("Вы в главном меню", reply_markup=await K.keyboard_for_user())
    else:
        await message.answer("Введите свое имя", reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(states.RegisterUser.name)


@user.message(states.RegisterUser.name)
async def get_name_handler(message: Message, state: FSMContext):
    name = message.text
    username = message.from_user.username
    await DF.update_user(
        user_id=str(message.chat.id),
        field_name='first_name',
        value=name)
    await DF.update_user(
        user_id=str(message.chat.id),
        field_name='username',
        value=username)
    await message.answer("Отлично! Теперь скажите сколько вам лет")
    await state.set_state(states.RegisterUser.age)


@user.message(states.RegisterUser.age)
async def get_age_handler(message: Message, state: FSMContext):
    try:
        age = int(message.text)
        if age <= 10:
            await message.answer("Возраст должен быть больше 10. Пожалуйста, введите ваш возраст заново.")
            return
        elif age > 80:
            await message.answer("Возраст не должен превышать 80 лет. Пожалуйста, введите ваш возраст заново.")
            return
        elif str(age).startswith('0'):
            await message.answer("Пожалуйста, не указывайте ноль в начале числа. Введите ваш возраст заново.")
            return
    except ValueError:
        await message.answer("Пожалуйста, введите число в качестве возраста.")
        return
    await DF.update_user(
        user_id=str(message.chat.id),
        field_name='age',
        value=age)
    await message.answer("Отлично! Из какого вы города?")  # reply_markup=await K.use_geo()
    await state.set_state(states.RegisterUser.city)


@user.message(states.RegisterUser.city)
async def get_city_handler(message: Message, state: FSMContext):
    city = message.text.lower()
    if len(city) < 2 or city not in CITIES_RU:
        await message.answer("К сожалению, такого города нет в списке. Пожалуйста, введите город еще раз.")
        return

    await DF.update_user(
        user_id=str(message.chat.id),
        field_name='city',
        value=city.title()
    )
    await DF.update_user(
        user_id=str(message.chat.id),
        field_name='search_city',
        value=city.title()
    )
    await message.answer("Отлично! Можешь рассказать о себе?")
    await state.set_state(states.RegisterUser.about_me)


@user.message(states.RegisterUser.about_me)
async def get_about_me(message: Message, state: FSMContext):
    message_text = message.text
    print(message_text)
    await DF.update_user(
        user_id=str(message.chat.id),
        field_name='about_me',
        value=message_text)
    await message.answer("Хорошо, кто ты?", reply_markup=await K.register_gender())
    await state.set_state(states.RegisterUser.gender)


@user.callback_query(F.data == "woman", states.RegisterUser.gender)
async def get_gender(query: CallbackQuery, state: FSMContext):
    await bot.delete_message(chat_id=query.message.chat.id, message_id=query.message.message_id)
    await DF.update_user(
        user_id=str(query.message.chat.id),
        field_name='gender',
        value=query.data)
    await query.message.answer("Отлично! Теперь давай выберем интересы, чтобы легче было находить своих людей",
                               reply_markup=await K.register_interest())

    await state.set_state(states.RegisterUser.interests)


@user.callback_query(F.data == "man", states.RegisterUser.gender)
async def get_gender(query: CallbackQuery, state: FSMContext):
    await bot.delete_message(chat_id=query.message.chat.id, message_id=query.message.message_id)
    await DF.update_user(
        user_id=str(query.message.chat.id),
        field_name='gender',
        value=query.data)
    await query.message.answer("Отлично! Теперь давай выберем интересы, чтобы легче было находить своих людей",
                               reply_markup=await K.register_interest())

    await state.set_state(states.RegisterUser.interests)


@user.callback_query(K.InterestFilter.filter(F.action == "select"), states.RegisterUser.interests)
async def get_interest(query: CallbackQuery, state: FSMContext):
    selected_interest = InterestFilter.unpack(query.data).value

    data = await state.get_data()

    selected_interests = data.get('selected_interests', [])

    if selected_interest in selected_interests:
        selected_interests.remove(selected_interest)
    else:
        selected_interests.append(selected_interest)

    await state.update_data(selected_interests=selected_interests)

    await DF.update_user(
        user_id=str(query.message.chat.id),
        field_name='interests',
        value=', '.join([INTERESTS_MAP[interest] for interest in selected_interests])
    )

    updated_keyboard = await update_interests_keyboard(selected_interests)

    confirm_button = types.InlineKeyboardButton(text="Подтвердить", callback_data="confirm_interests")

    new_row = [confirm_button]

    updated_keyboard.inline_keyboard.append(new_row)

    await query.message.edit_text("Выберите интересы и нажмите на подтвердить",
                                  reply_markup=updated_keyboard)


@user.callback_query(F.data == "confirm_interests")
async def confirm_interests(query: CallbackQuery):
    await bot.delete_message(chat_id=query.message.chat.id, message_id=query.message.message_id)
    await query.message.answer("Выберите кто вам нравится: ", reply_markup=await K.register_likes())


@user.callback_query(F.data == "woman_like")
async def get_interest_person(query: CallbackQuery, state: FSMContext):
    await bot.delete_message(chat_id=query.message.chat.id, message_id=query.message.message_id)
    await DF.update_user(
        user_id=str(query.message.chat.id),
        field_name='who_like',
        value=query.data)
    await query.message.answer("Теперь выберите, что для вас главное в жизни:", reply_markup=await K.register_main_in_life())
    await state.set_state(states.RegisterUser.main_in_life)


@user.callback_query(F.data == "man_like")
async def get_interest_person(query: CallbackQuery, state: FSMContext):
    await bot.delete_message(chat_id=query.message.chat.id, message_id=query.message.message_id)
    await DF.update_user(
        user_id=str(query.message.chat.id),
        field_name='who_like',
        value=query.data)
    await query.message.answer("Теперь выберите, что для вас главное в жизни:", reply_markup=await K.register_main_in_life())
    await state.set_state(states.RegisterUser.main_in_life)


@user.callback_query(F.data == "man_and_woman_like")
async def get_interest_person(query: CallbackQuery, state: FSMContext):
    await bot.delete_message(chat_id=query.message.chat.id, message_id=query.message.message_id)
    await DF.update_user(
        user_id=str(query.message.chat.id),
        field_name='who_like',
        value=query.data)

    await query.message.answer("Теперь выберите, что для вас главное в жизни:", reply_markup=await K.register_main_in_life())
    await state.set_state(states.RegisterUser.main_in_life)


@user.callback_query(F.data.startswith("life_goal"), states.RegisterUser.main_in_life)
async def get_main_in_life(query: CallbackQuery, state: FSMContext):
    selected_value = query.data.split(":")[1]
    await DF.update_user(user_id=str(query.message.chat.id), field_name='main_in_life', value=selected_value)
    if selected_value == "Пропустить":
        await query.answer("Вы пропустили этот шаг")
    else:
        await query.answer(f"Ты выбрал {selected_value}")
    await query.message.edit_text("Что для вас главное в людях?", reply_markup=await K.register_main_in_people())
    await state.set_state(states.RegisterUser.main_in_people)


@user.callback_query(F.data.startswith("main_in_people"), states.RegisterUser.main_in_people)
async def get_main_in_people(query: CallbackQuery, state: FSMContext):
    selected_value = query.data.split(":")[1]
    await DF.update_user(user_id=str(query.message.chat.id), field_name='main_in_people', value=selected_value)
    if selected_value == "Пропустить":
        await query.answer("Вы пропустили этот шаг")
    else:
        await query.answer(f"Ты выбрал {selected_value}")
    await query.message.edit_text("Какое у вас отношение к курению?", reply_markup=await K.register_smoking_attitude())
    await state.set_state(states.RegisterUser.smoking_attitude)


@user.callback_query(F.data.startswith("smoking"), states.RegisterUser.smoking_attitude)
async def get_smoking_attitude(query: CallbackQuery, state: FSMContext):
    selected_value = query.data.split(":")[1]
    await DF.update_user(user_id=str(query.message.chat.id), field_name='smoking_attitude', value=selected_value)
    if selected_value == "Пропустить":
        await query.answer("Вы пропустили этот шаг")
    else:
        await query.answer(f"Ты выбрал {selected_value}")
    await query.message.edit_text("Какое у вас отношение к алкоголю?", reply_markup=await K.register_alcohol_attitude())
    await state.set_state(states.RegisterUser.alcohol_attitude)


@user.callback_query(F.data.startswith("alcohol"), states.RegisterUser.alcohol_attitude)
async def get_alcohol_attitude(query: CallbackQuery, state: FSMContext):
    selected_value = query.data.split(":")[1]
    await DF.update_user(user_id=str(query.message.chat.id), field_name='alcohol_attitude', value=selected_value)
    if selected_value == "Пропустить":
        await query.answer("Вы пропустили этот шаг")
    else:
        await query.answer(f"Ты выбрал {selected_value}")
    await query.message.edit_text("Отлично! Последний шаг. Загрузите фотку или видео.")
    await state.set_state(states.RegisterUser.photo_or_video)


@user.message(states.RegisterUser.photo_or_video)
async def get_photo_or_video(message: Message, state: FSMContext):
    username = message.from_user.username
    if message.content_type not in ['photo', 'video']:
        await message.answer("Извините, вы можете загружать только фото или видео.")
        return
    if message.photo:
        self_photo_file_id = message.photo[-1].file_id
        new_self_photo_file_id = await save_user_photo(
            message.chat.id, message.message_id, self_photo_file_id)

        # Сохраняем file_id от фото пользователя в базе
        await DF.update_user(str(message.chat.id), 'profile_photo_file_id', new_self_photo_file_id)
        button = [
            [
                types.InlineKeyboardButton(text="Загрузить еще фото", callback_data="add_photo"),
                types.InlineKeyboardButton(text="Завершить", callback_data="finish")
            ]
        ]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=button)
        await message.answer("Хотите загрузить еще фото?", reply_markup=keyboard)
        await state.set_state(states.RegisterUser.additional_photo)
    if message.video:
        self_video_file_id = message.video.file_id
        new_self_video_file_id = await save_user_video(
            str(message.chat.id), message.message_id, self_video_file_id
        )

        await DF.update_user(str(message.chat.id), 'profile_video_file_id', new_self_video_file_id)
        await state.clear()
        await DF.update_user(str(message.chat.id), 'username', username)


@user.callback_query(F.data == "add_photo")
async def add_photo(query: CallbackQuery, state: FSMContext):
    await bot.delete_message(chat_id=query.message.chat.id, message_id=query.message.message_id)
    await query.message.answer("Загрузите следующую фото")
    await state.set_state(states.RegisterUser.additional_photo)


@user.message(states.RegisterUser.additional_photo)
async def additional_photo(message: Message, state: FSMContext):
    user_id = message.chat.id
    await DF.insert_user_id_additional_photo(str(user_id))
    if message.content_type not in ['photo']:
        await message.answer("Извините, вы можете загружать только фото.")
        return
    if message.photo:
        self_photo_file_id = message.photo[-1].file_id
        new_self_photo_file_id = await save_user_photo(
            message.chat.id, message.message_id, self_photo_file_id)

        # Сохраняем file_id от фото пользователя в базе
        profile_photo_file_id_2 = await DF.get_additional_photo_by_column(str(message.chat.id),
                                                                          'profile_photo_file_id_2')
        if profile_photo_file_id_2:
            await DF.update_additional_photo(str(message.chat.id), 'profile_photo_file_id_3', new_self_photo_file_id)
            await bot.send_message(user_id, "Ваш профиль успешно создан.",
                                   reply_markup=await K.keyboard_for_user())
            await state.clear()
        else:
            await DF.update_additional_photo(str(message.chat.id), 'profile_photo_file_id_2', new_self_photo_file_id)
            button = [
                [
                    types.InlineKeyboardButton(text="Загрузить еще фото", callback_data="add_photo"),
                    types.InlineKeyboardButton(text="Завершить", callback_data="finish")
                ]
            ]
            keyboard = types.InlineKeyboardMarkup(inline_keyboard=button)
            await message.answer("Фотография успешно загружена. Хотите загрузить еще одну фото?", reply_markup=keyboard)


@user.callback_query(F.data == "finish")
async def finish(query: CallbackQuery, state: FSMContext):
    user_id = query.message.chat.id
    await bot.delete_message(chat_id=query.message.chat.id, message_id=query.message.message_id)
    await bot.send_message(user_id, "Ваш профиль успешно создан.",
                           reply_markup=await K.keyboard_for_user())
    await state.clear()


@user.message(F.text.lower() == "посмотреть профиль")
async def look_profile_handler_for_key(message: Message):
    user_id = message.chat.id
    print(user_id)
    is_blocked = await DF.is_user_blocked(str(user_id))
    if is_blocked:
        await message.answer("❌ Вы были забанены навсегда и больше не можете пользоваться ботом.")
        return
    # Достаем инфу из БД
    about_me = await DF.get_about_me(str(user_id))
    name = await DF.get_first_name_info(str(user_id))
    age = await DF.get_age_info(str(user_id))
    city = await DF.get_city_info(str(user_id))
    main_in_life = await DF.get_main_in_life(str(user_id))
    main_in_people = await DF.get_main_in_people(str(user_id))
    smoking_attitude = await DF.get_smoking_attitude(str(user_id))
    alcohol_attitude = await DF.get_alcohol_attitude(str(user_id))

    photo_file_id = await DF.get_photo_file_id(str(user_id))
    photos = await DF.get_all_additional_photos(str(user_id))
    print(f'photos {photos}')

    # Проверка, есть ли данные для раздела "Жизненные позиции"
    life_positions = []
    if main_in_life and main_in_life.lower() != "пропустить":
        life_positions.append(f"🔹 Главное в жизни: {main_in_life}")
    if main_in_people and main_in_people.lower() != "пропустить":
        life_positions.append(f"🔹 Главное в людях: {main_in_people}")
    if smoking_attitude and smoking_attitude.lower() != "пропустить":
        life_positions.append(f"🚬 Отношение к курению: {smoking_attitude}")
    if alcohol_attitude and alcohol_attitude.lower() != "пропустить":
        life_positions.append(f"🍷 Отношение к алкоголю: {alcohol_attitude}")

    # Формируем описание профиля
    caption_text = (f"📌 *Ваш профиль*\n"
                    f"👤 Имя: {name}\n"
                    f"🎂 Возраст: {age}\n"
                    f"📍 Город: {city}\n"
                    f"📖 О себе: {about_me}\n")

    # Если есть жизненные позиции, добавляем их в описание
    if life_positions:
        caption_text += "\n🌟 *Жизненные позиции:*\n" + "\n".join(life_positions)

    collage_buffer = await DF.get_collage_file_id(str(user_id))
    if photos.get('profile_photo_file_id_2') or photos.get('profile_photo_file_id_3'):
        if collage_buffer:
            await message.answer_photo(photo=collage_buffer, caption=caption_text, parse_mode="Markdown",
                                       reply_markup=await K.profile_edit())
        else:
            collage_buffer = await create_collage([photos.get('profile_photo_file_id'),
                                                   photos.get('profile_photo_file_id_2'),
                                                   photos.get('profile_photo_file_id_3')],
                                                  chat_for_save_file_id)
            await DF.save_collage_file_id(str(user_id), collage_buffer)
            await message.answer_photo(photo=collage_buffer, caption=caption_text, parse_mode="Markdown",
                                       reply_markup=await K.profile_edit())
    elif photo_file_id:
        await message.answer_photo(photo=photo_file_id, caption=caption_text, parse_mode="Markdown",
                                   reply_markup=await K.profile_edit())
    else:
        video_file_id = await DF.get_video_file_id(str(user_id))
        if video_file_id:
            await message.answer_video(video=video_file_id, caption=caption_text, parse_mode="Markdown",
                                       reply_markup=await K.profile_edit())


@user.message(Command("myprofile"))
async def command_profile(message: Message):
    await look_profile_handler_for_key(message)


@user.message(Command("complaint"))
async def command_complaint(message: Message):
    user_id = message.from_user.id
    global last_viewed_user_id
    if last_viewed_user_id is None:
        await message.answer("Вы еще не просматривали анкеты других пользователей.")
        return

    await bot.send_message(
        user_id,
        "Выберите тип жалобы:",
        reply_markup=await K.complaint_keyboard(str(last_viewed_user_id))
    )


@user.message(Command("help"))
async def command_help(message: Message):
    await message.answer("Вы находитесь в разделе помощи.\n\nПожалуйста, укажите ваш юзернейм в Телеграмме, чтобы мы "
                         "могли легко вас найти.\n Будем благодарны, если вы будете придерживаться этого правила!")


@user.callback_query(F.data == "look_my_all_friends")
async def look_my_all_friends_handler(query: CallbackQuery):
    user_id = query.message.chat.id
    friends = await DF.get_friends_all(str(user_id))

    if friends:
        # Формируем строку для отображения информации о друзьях
        message = "Ваши друзья:\n"
        for friend in friends:
            first_name, username = friend
            first_name = first_name.strip()
            username = username.strip() if username else None

            message += f"{first_name} - "
            if username:
                message += f" @{username}\n"
            else:
                message += "\n"

        await query.message.answer(message, reply_markup=await K.quit_key())
    else:
        await query.message.answer("У вас нет друзей", reply_markup=await K.keyboard_for_user())


@user.callback_query(F.data == "delete_friends")
async def delete_friends_handler(query: CallbackQuery):
    print('delete_friends')
    user_id = str(query.message.chat.id)

    # Получаем список друзей
    friends = await DF.get_friends_all(user_id)
    print('friends:', friends)  # Логируем список друзей

    if not friends:
        await query.message.answer("У вас нет друзей.", reply_markup=await K.keyboard_for_user())
        return

    # Создаем клавиатуру (НОВЫЙ синтаксис)
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[])

    for friend in friends:
        first_name, username = friend
        first_name = first_name.strip()
        username = username.strip() if username else "Неизвестный"

        callback_data = f"erase:{user_id}:{username}"
        button = types.InlineKeyboardButton(
            text=f"{first_name} - @{username}" if username != "Неизвестный" else first_name,
            callback_data=callback_data
        )

        keyboard.inline_keyboard.append([button])  # Добавляем кнопку в список

    await query.message.answer("Выберите друга, которого хотите удалить:", reply_markup=keyboard)



@user.callback_query(F.data.startswith("erase:"))
async def delete_friend_confirmation_handler(query: CallbackQuery):
    print('lf')
    user_id, friend_username = query.data.split(":")[1:3]

    message = f"Вы уверены, что хотите удалить {friend_username} из ваших друзей?"
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text="✅ Да", callback_data=f"confirm_delete_friend:{user_id}:{friend_username}"),
                types.InlineKeyboardButton(text="❌ Нет", callback_data="back_to_menu")
            ]
        ]
    )

    await query.message.answer(message, reply_markup=keyboard)


@user.callback_query(F.data.startswith("confirm_delete_friend:"))
async def confirm_delete_friend_handler(query: CallbackQuery):
    user_id, friend_username = query.data.split(":")[1:3]

    success = await DF.delete_friend(user_id, friend_username)

    if success:
        await query.message.answer(f"✅ {friend_username} был удален из ваших друзей.",
                                   reply_markup=await K.keyboard_for_user())
    else:
        await query.message.answer("⚠ Ошибка: пользователь не найден или уже удален.",
                                   reply_markup=await K.keyboard_for_user())


@user.callback_query(F.data == "edit_name")
async def edit_name_handler(query: CallbackQuery, state: FSMContext):
    await query.message.answer("Введите новое имя")
    await state.set_state(states.EditUser.edited_name)


@user.message(states.EditUser.edited_name)
async def get_edited_name(message: Message, state: FSMContext):
    name = message.text
    await DF.update_user(
        user_id=str(message.chat.id),
        field_name='first_name',
        value=name)
    await state.clear()
    await look_profile_handler_for_key(message)


@user.callback_query(F.data == "edit_age")
async def edit_page_handler(query: CallbackQuery, state: FSMContext):
    await query.message.answer("Введите свой возраст")
    await state.set_state(states.EditAge.edited_age)


@user.message(states.EditAge.edited_age)
async def get_edited_age(message: Message, state: FSMContext):
    try:
        age = int(message.text)
        if age < 10:
            await message.answer("Извините, но вы должны быть старше 10 лет для использования этого сервиса.")
            return
        elif age > 80:
            await message.answer("Извините, но мы принимаем пользователей только до 80 лет.")
            return
        await DF.update_user(
            user_id=str(message.chat.id),
            field_name='age',
            value=age)
        await state.clear()
        await look_profile_handler_for_key(message)
    except ValueError:
        await message.answer("Некорректный формат возраста. Введите ваш возраст числом.")


@user.callback_query(F.data == "edit_photo")
async def edit_photo_handler(query: CallbackQuery, state: FSMContext):
    user_id = str(query.message.chat.id)
    await DF.clear_user_photo_file_id(user_id)
    await DF.clear_additional_photo_file_ids(user_id)
    await query.message.answer("Пришлите новое фото или же видео")
    await state.set_state(states.EditPhoto.edited_photo)


@user.message(states.EditPhoto.edited_photo)
async def get_edited_photo(message: Message, state: FSMContext):
    if message.photo:
        self_photo_file_id = message.photo[-1].file_id
        new_self_photo_file_id = await save_user_photo(
            message.chat.id, message.message_id, self_photo_file_id)

        # Сохраняем file_id от фото пользователя в базе
        await DF.update_user(str(message.chat.id), 'profile_photo_file_id', new_self_photo_file_id)
        button = [
            [
                types.InlineKeyboardButton(text="Загрузить еще фото", callback_data="add_new_photo"),
                types.InlineKeyboardButton(text="Завершить", callback_data="complete")
            ]
        ]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=button)
        await message.answer("Хотите загрузить еще фото?", reply_markup=keyboard)
        await state.clear()
    if message.video:
        self_video_file_id = message.video.file_id
        new_self_video_file_id = await save_user_video(
            str(message.chat.id), message.message_id, self_video_file_id
        )

        await DF.update_user(str(message.chat.id), 'profile_video_file_id', new_self_video_file_id)
        await message.answer("Видео сохранено.", reply_markup=await K.profile_edit())
        await state.clear()


@user.callback_query(F.data == "add_new_photo")
async def add_new_photo_handler(query: CallbackQuery, state: FSMContext):
    await bot.delete_message(chat_id=query.message.chat.id, message_id=query.message.message_id)
    await query.message.answer("Загрузите следующую фото")
    await state.set_state(states.EditPhoto.additional_photo)


@user.message(states.EditPhoto.additional_photo)
async def add_additional_photo_new_handler(message: Message, state: FSMContext):
    user_id = message.chat.id
    await DF.insert_user_id_additional_photo(str(user_id))
    collage_buffer = await DF.get_collage_file_id(str(user_id))
    photos = await DF.get_all_additional_photos(str(user_id))
    if message.content_type not in ['photo']:
        await message.answer("Извините, вы можете загружать только фото.")
        return
    if message.photo:
        self_photo_file_id = message.photo[-1].file_id
        new_self_photo_file_id = await save_user_photo(
            message.chat.id, message.message_id, self_photo_file_id)

        # Сохраняем file_id от фото пользователя в базе
        profile_photo_file_id_2 = await DF.get_additional_photo_by_column(str(message.chat.id),
                                                                          'profile_photo_file_id_2')
        if profile_photo_file_id_2:
            await DF.update_additional_photo(str(message.chat.id), 'profile_photo_file_id_3', new_self_photo_file_id)
            if photos.get('profile_photo_file_id_2') or photos.get('profile_photo_file_id_3'):
                if collage_buffer:
                    print(collage_buffer)
                    await message.answer_photo(photo=collage_buffer, caption="Фотография сохранена",
                                               reply_markup=await K.profile_edit())
                else:
                    collage_buffer = await create_collage([photos.get('profile_photo_file_id'),
                                                           photos.get('profile_photo_file_id_2'),
                                                           photos.get('profile_photo_file_id_3')],
                                                          chat_for_save_file_id)
                    await DF.save_collage_file_id(str(user_id), collage_buffer)
                    await message.answer_photo(photo=collage_buffer, caption=f"Фотография сохранена",
                                               reply_markup=await K.profile_edit())
            await state.clear()
        else:
            await DF.update_additional_photo(str(message.chat.id), 'profile_photo_file_id_2', new_self_photo_file_id)
            button = [
                [
                    types.InlineKeyboardButton(text="Загрузить еще одну фото", callback_data="add_new_photo"),
                    types.InlineKeyboardButton(text="Завершить", callback_data="complete")
                ]
            ]
            keyboard = types.InlineKeyboardMarkup(inline_keyboard=button)
            await message.answer("Фотография успешно загружена. Хотите загрузить еще одну фото?", reply_markup=keyboard)


@user.callback_query(F.data == "complete")
async def complete_handler(query: CallbackQuery, state: FSMContext):
    user_id = query.message.chat.id
    await bot.delete_message(chat_id=query.message.chat.id, message_id=query.message.message_id)
    collage_buffer = await DF.get_collage_file_id(str(user_id))
    photos = await DF.get_all_additional_photos(str(user_id))
    if photos.get('profile_photo_file_id_2') or photos.get('profile_photo_file_id_3'):
        if collage_buffer:
            print(collage_buffer)
            await query.message.answer_photo(photo=collage_buffer, caption="Фотография сохранена",
                                             reply_markup=await K.profile_edit())
        else:
            collage_buffer = await create_collage([photos.get('profile_photo_file_id'),
                                                   photos.get('profile_photo_file_id_2'),
                                                   photos.get('profile_photo_file_id_3')],
                                                  chat_for_save_file_id)
            await DF.save_collage_file_id(str(user_id), collage_buffer)
            await query.message.answer_photo(photo=collage_buffer, caption=f"Фотография сохранена",
                                             reply_markup=await K.profile_edit())
    await state.clear()


@user.callback_query(F.data == "edit_text")
async def edit_text_handler(query: CallbackQuery, state: FSMContext):
    await query.message.answer("Напиши новый текст о себе")
    await state.set_state(states.EditAboutMe.edited_about_me)


@user.message(states.EditAboutMe.edited_about_me)
async def get_edited_about_me(message: Message, state: FSMContext):
    about_me_message = message.text
    await DF.update_user(
        user_id=str(message.chat.id),
        field_name='about_me',
        value=about_me_message)
    await state.clear()
    await look_profile_handler_for_key(message)


@user.callback_query(F.data == "edit_city")
async def edit_text_handler(query: CallbackQuery, state: FSMContext):
    await query.message.answer("Напиши город")
    await state.set_state(states.EditCity.edited_city)


@user.message(states.EditCity.edited_city)
async def get_edited_about_me(message: Message, state: FSMContext):
    city = message.text.lower()
    if len(city) < 2 or city not in CITIES_RU:
        await message.answer("К сожалению, такого города нет в списке. Пожалуйста, введите город еще раз.")
        return

    await DF.update_user(
        user_id=str(message.chat.id),
        field_name='city',
        value=city.title()
    )
    await state.clear()
    await message.answer("Город изменен",
                         reply_markup=await K.keyboard_for_user())


@user.callback_query(F.data == "edit_search_city")
async def edit_text_handler(query: CallbackQuery, state: FSMContext):
    await query.message.answer("Напиши город, где хочешь, чтобы показывались анкеты, или выбери 'Все города' 👇",
                               reply_markup=await K.city_choice_keyboard())
    await state.set_state(states.EditCitySearch.edited_city)


@user.callback_query(F.data == "all_cities")
async def set_all_cities(query: CallbackQuery, state: FSMContext):
    """Если нажата кнопка 'Все города', записываем 'all' в базу"""
    await DF.update_user(
        user_id=str(query.from_user.id),
        field_name='search_city',
        value='all'
    )
    await state.clear()
    await query.message.answer("Поиск теперь будет по всем городам!",
                               reply_markup=await K.keyboard_for_user())


@user.message(states.EditCitySearch.edited_city)
async def get_edited_about_me(message: Message, state: FSMContext):
    """Обрабатываем ввод города"""
    city = message.text.lower()

    if len(city) < 2 or city not in CITIES_RU:
        await message.answer("К сожалению, такого города нет в списке. Пожалуйста, введите город еще раз.")
        return

    await DF.update_user(
        user_id=str(message.chat.id),
        field_name='search_city',
        value=city.title()
    )
    await state.clear()
    await look_profile_handler_for_key(message)


@user.callback_query(F.data == "edit_life")
async def edit_life_handler(query: CallbackQuery, state: FSMContext):
    await query.message.answer("Выберите, что для вас главное в жизни:", reply_markup=await K.register_main_in_life())
    await state.set_state(states.EditMainInLife.edited_main_in_life)


@user.callback_query(F.data.startswith("life_goal"), states.EditMainInLife.edited_main_in_life)
async def edit_main_in_life(query: CallbackQuery, state: FSMContext):
    selected_value = query.data.split(":")[1]
    await DF.update_user(user_id=str(query.message.chat.id), field_name='main_in_life', value=selected_value)
    if selected_value == "Пропустить":
        await query.answer("Вы пропустили этот шаг")
    else:
        await query.answer(f"Ты выбрал {selected_value}")
    await query.message.edit_text("Что для вас главное в людях?", reply_markup=await K.register_main_in_people())
    await state.set_state(states.EditMainInPeople.edited_main_in_people)


@user.callback_query(F.data.startswith("main_in_people"), states.EditMainInPeople.edited_main_in_people)
async def edit_main_in_people(query: CallbackQuery, state: FSMContext):
    selected_value = query.data.split(":")[1]
    await DF.update_user(user_id=str(query.message.chat.id), field_name='main_in_people', value=selected_value)
    if selected_value == "Пропустить":
        await query.answer("Вы пропустили этот шаг")
    else:
        await query.answer(f"Ты выбрал {selected_value}")
    await query.message.edit_text("Какое у вас отношение к курению?", reply_markup=await K.register_smoking_attitude())
    await state.set_state(states.EditSmokingAttitude.edited_smoking_attitude)


@user.callback_query(F.data.startswith("smoking"), states.EditSmokingAttitude.edited_smoking_attitude)
async def edit_smoking_attitude(query: CallbackQuery, state: FSMContext):
    selected_value = query.data.split(":")[1]
    await DF.update_user(user_id=str(query.message.chat.id), field_name='smoking_attitude', value=selected_value)
    if selected_value == "Пропустить":
        await query.answer("Вы пропустили этот шаг")
    else:
        await query.answer(f"Ты выбрал {selected_value}")
    await query.message.edit_text("Какое у вас отношение к алкоголю?", reply_markup=await K.register_alcohol_attitude())
    await state.set_state(states.EditAlcoholAttitude.edited_alcohol_attitude)


@user.callback_query(F.data.startswith("alcohol"), states.EditAlcoholAttitude.edited_alcohol_attitude)
async def edit_alcohol_attitude(query: CallbackQuery, state: FSMContext):
    selected_value = query.data.split(":")[1]
    await DF.update_user(user_id=str(query.message.chat.id), field_name='alcohol_attitude', value=selected_value)
    if selected_value == "Пропустить":
        await query.answer("Вы пропустили этот шаг")
    else:
        await query.answer(f"Ты выбрал {selected_value}")
    await state.clear()
    await look_profile_handler_for_key(query.message)



@user.callback_query(F.data == "edit_interests")
async def edit_interests(query: CallbackQuery, state: FSMContext):
    # Отправляем сообщение с клавиатурой для выбора новых интересов
    await query.message.answer("Выберите интересы и нажмите на подтвердить",
                               reply_markup=await K.register_interest())

    # Устанавливаем состояние машины состояний для выбора интересов
    await state.set_state(states.EditInterests.interest)


@user.callback_query(K.InterestFilter.filter(F.action == "select"), states.EditInterests.interest)
async def interest_handler(query: CallbackQuery, state: FSMContext):
    selected_interest = InterestFilter.unpack(query.data).value

    data = await state.get_data()

    selected_interests = data.get('selected_interests', [])

    if selected_interest in selected_interests:
        selected_interests.remove(selected_interest)
    else:
        selected_interests.append(selected_interest)

    await state.update_data(selected_interests=selected_interests)

    await DF.update_user(
        user_id=str(query.message.chat.id),
        field_name='interests',
        value=', '.join([INTERESTS_MAP[interest] for interest in selected_interests])
    )

    updated_keyboard = await update_interests_keyboard(selected_interests)

    confirm_button = types.InlineKeyboardButton(text="Подтвердить", callback_data="edit_confirm_interests")

    new_row = [confirm_button]

    updated_keyboard.inline_keyboard.append(new_row)

    await query.message.edit_text("Выберите интересы и нажмите на подтвердить",
                                  reply_markup=updated_keyboard)


@user.callback_query(F.data == "edit_confirm_interests")
async def last_edit_interests_handler(query: CallbackQuery, state: FSMContext):
    await state.clear()
    await bot.delete_message(chat_id=query.message.chat.id, message_id=query.message.message_id)


@user.callback_query(F.data == "delete_profile")
async def delete_profile_handler(query: CallbackQuery):
    await query.message.answer("Вы точно хотите удалить профиль?", reply_markup=await K.delete_keyboard())


@user.callback_query(F.data == "yes_delete")
async def yes_delete_handler(query: CallbackQuery):
    user_id = query.message.chat.id
    await DF.clear_user_columns(str(user_id))
    await query.message.edit_text("Аккаунт удален. Вы сможете заново заполнить анкету.\n"
                                  "Нажмите просто /start")


@user.callback_query(F.data == "no_delete")
async def yes_delete_handler(query: CallbackQuery):
    await query.message.answer("Спасибо, что остаетесь с нами! ",
                                  reply_markup=await K.keyboard_for_user())


async def look_questionnaire_handler(query: CallbackQuery):
    global last_viewed_user_id
    user_id = query.message.chat.id

    # Получаем список пользователей, отсортированных по количеству совпадений
    similar_users = await DF.find_similar_users(str(user_id))
    print(f'Подходящие пользователи: {similar_users}')

    if similar_users:
        liked_users = []
        disliked_users = []
        for user in similar_users:
            liked = await DF.check_like(str(user_id), str(user))
            disliked = await DF.check_dislike(str(user_id), str(user))

            if liked:
                liked_users.append(user)
            elif disliked:
                disliked_users.append(user)
            else:
                last_viewed_user_id = user

                # Загружаем информацию о пользователе
                name = await DF.get_first_name_info(str(user))
                age = await DF.get_age_info(str(user))
                about_me = await DF.get_about_me(str(user))
                photo_file_id = await DF.get_photo_file_id(str(user))
                video_file_id = await DF.get_video_file_id(str(user))
                city = await DF.get_city_info(str(user))
                photos = await DF.get_all_additional_photos(str(user))
                collage_buffer = await DF.get_collage_file_id(str(user))

                message_text = f"🟢 {name.strip()}, {age}\n{about_me}\n🌎 {city}"

                # Отправка фото или видео
                if photos.get('profile_photo_file_id_2') or photos.get('profile_photo_file_id_3'):
                    if collage_buffer:
                        await query.message.answer_photo(photo=collage_buffer, caption=message_text,
                                                         reply_markup=await K.questionnaire(str(user)))
                    else:
                        collage_buffer = await create_collage([
                            photos.get('profile_photo_file_id'),
                            photos.get('profile_photo_file_id_2'),
                            photos.get('profile_photo_file_id_3')
                        ], chat_for_save_file_id)
                        await DF.save_collage_file_id(str(user), collage_buffer)
                        await query.message.answer_photo(photo=collage_buffer, caption=message_text,
                                                         reply_markup=await K.questionnaire(str(user)))
                elif photo_file_id:
                    await query.message.answer_photo(photo=photo_file_id, caption=message_text,
                                                     reply_markup=await K.questionnaire(str(user)))
                elif video_file_id:
                    await query.message.answer_video(video=video_file_id, caption=message_text,
                                                     reply_markup=await K.questionnaire(str(user)))
                else:
                    await query.message.answer(message_text, reply_markup=await K.questionnaire(str(user)))

                return

        await query.message.answer("Новых анкет пока что нет. Приходите попозже!")
    else:
        await query.message.answer("Не найдено пользователей с совпадающими интересами.")


@user.message(F.text.lower() == "анкеты")
async def look_questionnaire_handler_for_kb(message: Message):
    global last_viewed_user_id
    user_id = message.chat.id

    is_blocked = await DF.is_user_blocked(str(user_id))
    if is_blocked:
        await message.answer("❌ Вы были забанены навсегда и больше не можете пользоваться ботом.")
        return

    # Получаем список пользователей, отсортированных по количеству совпадающих интересов
    similar_users = await DF.find_similar_users(str(user_id))
    print(f'Подходящие пользователи: {similar_users}')

    if similar_users:
        liked_users = []
        disliked_users = []
        for user in similar_users:
            liked = await DF.check_like(str(user_id), str(user))
            disliked = await DF.check_dislike(str(user_id), str(user))

            if liked:
                liked_users.append(user)
            elif disliked:
                disliked_users.append(user)
            else:
                last_viewed_user_id = user

                # Загружаем информацию о пользователе
                name = await DF.get_first_name_info(str(user))
                age = await DF.get_age_info(str(user))
                about_me = await DF.get_about_me(str(user))
                photo_file_id = await DF.get_photo_file_id(str(user))
                video_file_id = await DF.get_video_file_id(str(user))
                city = await DF.get_city_info(str(user))
                photos = await DF.get_all_additional_photos(str(user))
                collage_buffer = await DF.get_collage_file_id(str(user))

                message_text = f"🟢 {name.strip()}, {age}\n{about_me}\n🌎 {city}"

                # Отправка фото или видео
                if photos.get('profile_photo_file_id_2') or photos.get('profile_photo_file_id_3'):
                    if collage_buffer:
                        await message.answer_photo(photo=collage_buffer, caption=message_text, reply_markup=await K.questionnaire(str(user)))
                    else:
                        collage_buffer = await create_collage([
                            photos.get('profile_photo_file_id'),
                            photos.get('profile_photo_file_id_2'),
                            photos.get('profile_photo_file_id_3')
                        ], chat_for_save_file_id)
                        await DF.save_collage_file_id(str(user), collage_buffer)
                        await message.answer_photo(photo=collage_buffer, caption=message_text, reply_markup=await K.questionnaire(str(user)))
                elif photo_file_id:
                    await message.answer_photo(photo=photo_file_id, caption=message_text, reply_markup=await K.questionnaire(str(user)))
                elif video_file_id:
                    await message.answer_video(video=video_file_id, caption=message_text, reply_markup=await K.questionnaire(str(user)))
                else:
                    await message.answer(message_text, reply_markup=await K.questionnaire(str(user)))

                return

        await message.answer("Новых анкет пока что нет. Приходите попозже!")
    else:
        await message.answer("Не найдено пользователей с совпадающими интересами.")


@user.callback_query(lambda callback_query: callback_query.data.startswith("put_like:"))
async def put_like_handler(query: CallbackQuery, state: FSMContext):
    user_id = query.from_user.id
    liked_user_id = query.data.split(":")[1]

    # Поставить лайк в базу данных
    await DF.put_like(str(user_id), str(liked_user_id))

    # Сохранить ID пользователя, которому был поставлен лайк, в состоянии
    await state.update_data(liker_id=user_id)
    # Отправить уведомление пользователю, которому был поставлен лайк
    await send_notification_me(liked_user_id, f"Вам поставил лайк пользователь. Показать его?", state)

    # Показать новую анкету после постановки лайка
    await look_questionnaire_handler(query)


@user.callback_query(lambda callback_query: callback_query.data.startswith("put_sms:"))
async def put_sms_handler(query: CallbackQuery, state: FSMContext):
    user_id = query.from_user.id
    liked_user_id = query.data.split(":")[1]
    await state.update_data(liked_user_id_sms=liked_user_id)
    # Поставить лайк в базу данных
    await DF.put_like(str(user_id), str(liked_user_id))
    await query.message.answer('Напишите сообщение, которое хотите отправить пользователю')
    await state.set_state(states.PutSms.send_message)


@user.message(states.PutSms.send_message)
async def send_message_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    liked_user_id = data.get("liked_user_id_sms")
    print(f'liked_user_id_sms {liked_user_id}')
    message_for_user = message.text
    await DF.save_message(str(user_id), str(liked_user_id), message_for_user)
    await bot.send_message(liked_user_id, "Вам написали сообщение!",
                           reply_markup=await K.questionnaire_look_me(liked_user_id))
    await message.answer("Вы отправили сообщение")
    await look_questionnaire_handler_for_kb(message)


@user.callback_query(lambda callback_query: callback_query.data.startswith("put_dislike:"))
async def put_dislike_handler(query: CallbackQuery):
    disliked_user_id = int(query.data.split(":")[1])
    skip_user_id = load_skip_user_id()
    # Проверяем, есть ли уже disliked_user_id в списке skip_user_id
    if disliked_user_id not in skip_user_id:
        skip_user_id.append(disliked_user_id)
        save_skip_user_id(skip_user_id)
    # Показать новую анкету после постановки дизлайка
    await look_questionnaire_handler(query)


@user.callback_query(lambda callback_query: callback_query.data.startswith("confirm_never_seen:"))
async def confirm_never_seen_profile_handler(query: CallbackQuery):
    disliked_user_id = query.data.split(":")[1]

    # Create a new confirmation message and keyboard
    message = "Вы уверены, что больше не хотите видеть этого пользователя?"
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text="Да", callback_data=f"never_seen:{disliked_user_id}"),
                types.InlineKeyboardButton(text="Нет", callback_data="back_to_menu")
            ]
        ]
    )

    # Ask for confirmation before marking a user as "never seen"
    await query.message.answer(message, reply_markup=keyboard)


@user.callback_query(lambda callback_query: callback_query.data.startswith("additional_information:"))
async def confirm_never_seen_profile_handler(query: CallbackQuery):
    liked_user_id = query.data.split(":")[1]
    main_in_life = await DF.get_main_in_life(str(liked_user_id))
    main_in_people = await DF.get_main_in_people(str(liked_user_id))
    smoking_attitude = await DF.get_smoking_attitude(str(liked_user_id))
    alcohol_attitude = await DF.get_alcohol_attitude(str(liked_user_id))

    # Проверка, есть ли данные для раздела "Жизненные позиции"
    life_positions = []
    if main_in_life and main_in_life.lower() != "пропустить":
        life_positions.append(f"🔹 Главное в жизни: {main_in_life}")
    if main_in_people and main_in_people.lower() != "пропустить":
        life_positions.append(f"🔹 Главное в людях: {main_in_people}")
    if smoking_attitude and smoking_attitude.lower() != "пропустить":
        life_positions.append(f"🚬 Отношение к курению: {smoking_attitude}")
    if alcohol_attitude and alcohol_attitude.lower() != "пропустить":
        life_positions.append(f"🍷 Отношение к алкоголю: {alcohol_attitude}")

    caption_text = ""

    if life_positions:
        caption_text += "\n🌟 Жизненные позиции:\n" + "\n".join(life_positions)

    await query.answer(caption_text, show_alert=True)


@user.callback_query(lambda callback_query: callback_query.data.startswith("never_seen:"))
async def never_seen_profile_handler(query: CallbackQuery):
    print('я в never_seen_profile_handler')
    user_id = query.message.chat.id
    disliked_user_id = query.data.split(":")[1]

    await DF.put_dislike(str(user_id), str(disliked_user_id))

    # Показать новую анкету после постановки дизлайка
    await look_questionnaire_handler(query)


@user.callback_query(lambda callback_query: callback_query.data.startswith("look_me:"))
async def look_me_form_handler(query: CallbackQuery, state: FSMContext):
    """Обработчик, который показывается тогда, когда лайкнули меня(look me)"""
    user_id = query.message.chat.id
    user = await DF.get_liker_user_id(str(user_id))

    if user is not None:
        message = f"🟢 {user['first_name'].strip()}, {user['age']}\n" \
                  f"🌎 {user['city']}"
        user_message = await DF.get_message_between_users(str(user_id), str(user['user_id']))
        if user_message:
            message += f"\nСообщение от пользователя: {user_message}"

        photo_file_id = await DF.get_photo_file_id(str(user['user_id']))
        video_file_id = await DF.get_video_file_id(str(user['user_id']))

        if photo_file_id:
            await bot.send_photo(query.from_user.id, caption=message, photo=photo_file_id,
                                 reply_markup=await K.questionnaire_look_me_step_second(user['user_id']))
        elif video_file_id:
            await bot.send_video(query.from_user.id, caption=message, video=video_file_id,
                                 reply_markup=await K.questionnaire_look_me_step_second(user['user_id']))
        else:
            await bot.send_message(query.from_user.id, message,
                                   reply_markup=await K.questionnaire_look_me_step_second(user['user_id']))
    else:
        await bot.send_message(query.from_user.id, "Пользователь не найден")


@user.callback_query(F.data == "skip_me")
async def look_me_form_handler(query: CallbackQuery):
    """Обработчик, который показывается тогда, когда лайкнули меня(look me)"""
    await query.message.answer('Хорошо. Не буду показывать этого человека',
                               reply_markup=await K.keyboard_for_user())


@user.callback_query(lambda callback_query: callback_query.data.startswith("add_to_friends"))
async def add_to_friends_handler(query: CallbackQuery):
    """Обработчик, который показывается тогда, когда лайкнули меня и мы нажали на кнопку Посмотреть"""
    # Добавить пользователя в друзья
    user_id = query.from_user.id
    friend_id = query.data.split(":")[1]
    # await DF.add_friend(str(user_id), str(friend_id))

    # Отправить сообщение пользователю, которого добавили в друзья
    await bot.send_message(
        friend_id,
        f"@{query.from_user.username} хочет добавить вас в друзья",
        reply_markup=await K.friends_keyboard(str(user_id))
    )

    # Отправить сообщение пользователю, который добавил в друзья
    await bot.send_message(
        user_id,
        "Вы отправили запрос в друзья.",
        reply_markup=await K.keyboard_for_user()
    )


@user.callback_query(lambda callback_query: callback_query.data.startswith("make_a_complaint"))
async def make_a_complaint_handler(query: CallbackQuery):
    user_id = query.from_user.id
    complaint_user_id = query.data.split(":")[1]
    # Отправить клавиатуру для выбора типа жалобы
    await bot.send_message(
        user_id,
        "Выберите тип жалобы:",
        reply_markup=await K.complaint_keyboard(str(complaint_user_id))
    )


@user.callback_query(lambda callback_query: callback_query.data.startswith("accept"))
async def accept_friend_handler(query: CallbackQuery):
    """Обработчик, который показывается при нажатии на кнопку Принять заявку в друзья"""
    # Получить ID пользователей из callback_data
    user_id = query.message.chat.id
    friend_id = query.data.split(":")[1]
    print(user_id)
    print(friend_id)

    # Обновить статус заявки в друзья в базе данных
    await DF.accept_friend_request(str(user_id), str(friend_id))

    # Отправить сообщение пользователю, который отправил заявку в друзья
    await bot.send_message(
        friend_id,
        f"@{query.from_user.username} принял вашу заявку в друзья.",
    )

    # Отправить сообщение пользователю, который принял заявку в друзья
    await bot.send_message(
        user_id,
        f"Вы подтвердили заявку в друзья от @{query.message.chat.username}.",
    )


@user.callback_query(lambda callback_query: callback_query.data.startswith("reject"))
async def reject_friend_handler(query: CallbackQuery):
    """Обработчик, который показывается при нажатии на кнопку Отклонить заявку в друзья"""
    # Получить ID пользователей из callback_data
    user_id = query.message.chat.id
    friend_id = query.data.split(":")[1:]

    # Отправить сообщение пользователю, который отправил заявку в друзья
    await bot.send_message(
        int(user_id),
        f"{query.from_user.username} отклонил вашу заявку в друзья."
    )

    # Отправить сообщение пользователю, который отклонил заявку в друзья
    await bot.send_message(
        friend_id,
        f"Вы отклонили заявку в друзья от {query.message.chat.username}."
    )


@user.callback_query(lambda callback_query: callback_query.data.startswith("put_like_after_look_me"))
async def put_like_after_look_me_handler(query: CallbackQuery, state: FSMContext):
    user_id = query.from_user.id
    liked_user_id = query.data.split(":")[1]

    print("put_like_after_look_me")
    print(user_id)
    print(liked_user_id)

    # Поставить лайк в базу данных
    await DF.put_like(str(user_id), str(liked_user_id))

    # Проверить, есть ли взаимный лайк
    mutual_like = await DF.check_mutual_like(str(user_id), str(liked_user_id))
    if mutual_like:
        # Если есть взаимный лайк, отправить сообщение об этом
        user = await DF.get_user_by_id(str(user_id))
        liked_user = await DF.get_user_by_id(str(liked_user_id))
        await bot.send_message(
            user_id,
            f"У вас взаимная симпатия с @{liked_user['username']}!\n"
            f"Теперь вы можете общаться в личных сообщениях.",
            reply_markup=await K.questionnaire_look_step_second(str(liked_user_id))
        )
        await bot.send_message(
            liked_user_id,
            f"У вас взаимная симпатия с @{user['username']}!\n"
            f"Теперь вы можете общаться в личных сообщениях.",
            reply_markup=await K.questionnaire_look_step_second(str(user_id))
        )


@user.callback_query(lambda callback_query: callback_query.data.startswith("put_dislike_after_look_me"))
async def put_dislike_after_look_me_handler(query: CallbackQuery):
    """Обработчик, который показывается тогда, когда лайкнули меня и мы нажали на кнопку Посмотреть(look_me)"""
    # user_id = query.from_user.id
    # disliked_user_id = query.data.split(":")[1]
    # await DF.put_dislike(str(user_id), str(disliked_user_id))

    # Показать новую анкету после постановки дизлайка
    await look_questionnaire_handler(query)


@user.callback_query(F.data.contains("_complaint"))
async def complaint_handler(query: CallbackQuery, state: FSMContext):
    """Обработчик, который показывается при нажатии на кнопку с типом жалобы"""
    complaint_type = query.data.split("_")[0] + "_complaint"

    # Записать жалобу в базу данных
    user_id = query.from_user.id
    complained_user_id = query.data.split(":")[1]
    try:
        complained_user = await bot.get_chat(int(complained_user_id))
        complained_username = complained_user.username
    except Exception as e:
        print(f"Error while getting user data: {e}")
        complained_username = "Unknown"
    await DF.put_complaint(str(user_id), str(complained_user_id), complaint_type, complained_username)

    # Отправить сообщение администратору с жалобой
    for admin_id in ADMIN_ID:
        print(admin_id)
        await bot.send_message(
            admin_id,
            f"Новая жалоба от @{query.from_user.username} на @{complained_username}:\n\n"
            f"Тип жалобы: {complaint_type}",
            reply_markup=await K.admin_keyboard()
        )

    # Отправить сообщение пользователю, который пожаловался
    await bot.send_message(
        user_id,
        "Ваша жалоба записана. Мы рассмотрим ее в ближайшее время.",
    )


@user.callback_query(F.data == "cancel_complaint")
async def put_dislike_after_look_me_handler(query: CallbackQuery):
    """Обработчик, который показывается при нажатии на кнопку Кинуть жалобу"""
    await back_to_menu(query)


@user.callback_query(F.data == "back_to_menu")
async def back_to_menu_handler(query: CallbackQuery):
    await back_to_menu(query)
