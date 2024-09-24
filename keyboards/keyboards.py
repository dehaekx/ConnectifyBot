from aiogram import types
from aiogram.filters.callback_data import CallbackData

from utils.maps import INTERESTS_MAP


class InterestFilter(CallbackData, prefix='interest'):
    action: str
    value: str


# Клавиатуры для пользователей(регистрация)
async def register_gender():
    inline_buttons = [
        [types.InlineKeyboardButton(text='Парень ⚦', callback_data='man'),
         types.InlineKeyboardButton(text='Девушка ♀', callback_data='woman')],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=inline_buttons)
    return keyboard


async def register_likes():
    """Кнопки с выборкой кто нравится"""
    inline_buttons = [
        [types.InlineKeyboardButton(text='Девушки', callback_data='woman_like'), types.InlineKeyboardButton(text='Парни', callback_data='man_like')],
        [types.InlineKeyboardButton(text='Все равно', callback_data='man_and_woman_like')],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=inline_buttons)
    return keyboard


async def register_interest():
    inline_buttons = []
    row = []
    for key, value in INTERESTS_MAP.items():
        callback_data = InterestFilter(action="select", value=key).pack()
        button = types.InlineKeyboardButton(text=value, callback_data=callback_data)
        row.append(button)
        if len(row) == 2:
            inline_buttons.append(row)
            row = []
    if row:
        inline_buttons.append(row)
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=inline_buttons)
    return keyboard


async def skip_step():
    """Клавиатура, которая переходит к другому этапу, пропуская блок о себе"""
    kb = [
        [
            types.KeyboardButton(text="Пропустить"),
        ],
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True
    )

    return keyboard


async def use_geo():
    kb = [
        [
            types.KeyboardButton(text="Использовать геолокацию", request_location=True),
        ],
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True
    )

    return keyboard


async def use_contact():
    kb = [
        [
            types.KeyboardButton(text="Использовать контакт")
        ],
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True
    )

    return keyboard


# Клавиатуры для пользователей(авторизированные)
async def profile():
    inline_buttons = [
        [types.InlineKeyboardButton(text='Посмотреть профиль', callback_data='look_profile')],
        [types.InlineKeyboardButton(text='Смотреть анкеты', callback_data='look_questionnaire')],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=inline_buttons)
    return keyboard


async def profile_edit():
    inline_buttons = [
        [
            types.InlineKeyboardButton(text='Мои друзья', callback_data='look_my_all_friends'),
            types.InlineKeyboardButton(text='Изменить имя', callback_data='edit_name')
        ],
        [
            types.InlineKeyboardButton(text='Изменить возраст', callback_data='edit_age'),
            types.InlineKeyboardButton(text='Изменить фото/видео', callback_data='edit_photo')
        ],
        [
            types.InlineKeyboardButton(text='Изменить текст обо мне', callback_data='edit_text'),
            types.InlineKeyboardButton(text='Изменить интересы', callback_data='edit_interests')
        ],
        [
            types.InlineKeyboardButton(text='Удалить профиль', callback_data='delete_profile'),
            # types.InlineKeyboardButton(text='Назад', callback_data='back_to_menu')
        ],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=inline_buttons)
    return keyboard


async def questionnaire(liked_user_id: str):
    """Взаимодействие с анкетой пользователя"""
    inline_buttons = [
        [
            types.InlineKeyboardButton(text='❤', callback_data=f'put_like:{liked_user_id}'),
            types.InlineKeyboardButton(text='💌/📹', callback_data=f'put_sms:{liked_user_id}'),
            types.InlineKeyboardButton(text='👎', callback_data=f'put_dislike:{liked_user_id}')
        ],
        [
            types.InlineKeyboardButton(text='Больше не показывать этого человека',
                                       callback_data=f'confirm_never_seen:{liked_user_id}')
        ],
        # [
        #     types.InlineKeyboardButton(text='Выйти в главное меню', callback_data='back_to_menu')
        # ],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=inline_buttons)
    return keyboard


async def questionnaire_look():
    """Клавиатура, которая показывается тогда, когда лайкнул я, а после и другой"""
    inline_buttons = [
        [types.InlineKeyboardButton(text='Посмотреть', callback_data='look')],
        [types.InlineKeyboardButton(text='Пропустить', callback_data='skip')],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=inline_buttons)
    return keyboard


async def questionnaire_look_step_second(user_id: str):
    """Клавиатура, которая показывается тогда, когда лайкнули меня и мы нажали на кнопку Посмотреть"""
    inline_buttons = [
        [types.InlineKeyboardButton(text='Добавить в друзья', callback_data=f'add_to_friends:{user_id}')],
        [types.InlineKeyboardButton(text='Кинуть жалобу', callback_data=f'make_a_complaint:{user_id}')],
        # [types.InlineKeyboardButton(text='Выйти в главное меню', callback_data='back_to_menu')],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=inline_buttons)
    return keyboard


async def friends_keyboard(user_id: str):
    """Клавиатура с заявкой в друзья"""
    inline_buttons = [
        [types.InlineKeyboardButton(text='Принять', callback_data=f'accept:{user_id}')],
        [types.InlineKeyboardButton(text='Отклонить', callback_data=f'reject:{user_id}')],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=inline_buttons)
    return keyboard


async def questionnaire_look_me(liked_user_id: str):
    """Клавиатура, которая показывается тогда, когда лайкнули меня"""
    inline_buttons = [
        [types.InlineKeyboardButton(text='Посмотреть', callback_data=f'look_me:{liked_user_id}')],
        [types.InlineKeyboardButton(text='Пропустить', callback_data='skip_me')],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=inline_buttons)
    return keyboard


async def questionnaire_look_me_step_second(liked_user_id: str):
    """Клавиатура, которая показывается тогда, когда лайкнули меня и мы нажали на кнопку Посмотреть(look_me)"""
    inline_buttons = [
        [
            types.InlineKeyboardButton(text='❤', callback_data=f'put_like_after_look_me:{liked_user_id}'),
            types.InlineKeyboardButton(text='👎', callback_data=f'put_dislike_after_look_me:{liked_user_id}')
        ],
        [types.InlineKeyboardButton(text='Кинуть жалобу', callback_data=f'make_a_complaint:{liked_user_id}')],
        [types.InlineKeyboardButton(text='Выйти в главное меню', callback_data='back_to_menu')],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=inline_buttons)
    return keyboard


async def complaint_keyboard(user_id: str):
    """Клавиатура, которая показывается при нажатии на кнопку Кинуть жалобу"""
    inline_buttons = [
        [types.InlineKeyboardButton(text='Материал для взрослых', callback_data=f'adult_material_complaint:{user_id}')],
        [types.InlineKeyboardButton(text='Продажа товаров и услуг', callback_data=f'sell_complaint:{user_id}')],
        [types.InlineKeyboardButton(text='Не отвечает', callback_data=f'dont_answer_complaint:{user_id}')],
        [types.InlineKeyboardButton(text='Другое', callback_data=f'other_complaint:{user_id}')],
        [types.InlineKeyboardButton(text='Отмена', callback_data='cancel_complaint')],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=inline_buttons)
    return keyboard


async def start_key():
    """Кнопка с регистрацией. Первое нажатие на /start и последующие"""
    kb = [
        [
            types.KeyboardButton(text="Начать"),
        ],
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True
    )

    return keyboard


async def keyboard_for_user():
    """Кнопка для тех, кто зарегистрировался в бота"""
    kb = [
        [
            types.KeyboardButton(text="Анкеты"),
            types.KeyboardButton(text="Посмотреть профиль"),
        ],
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True
    )

    return keyboard


async def quit_key():
    inline_buttons = [
        [
            types.InlineKeyboardButton(text="Удалить друзей", callback_data="delete_friends"),
            types.InlineKeyboardButton(text='Выйти', callback_data='back_to_menu')
        ]
    ]

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=inline_buttons)
    return keyboard


async def delete_keyboard():
    inline_buttons = [
        [types.InlineKeyboardButton(text='Да', callback_data='yes_delete')],
        [types.InlineKeyboardButton(text='Нет', callback_data='no_delete')]
    ]

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=inline_buttons)
    return keyboard


# КЛАВИАТУРЫ ДЛЯ АДМИНОВ
async def admin_keyboard():
    """Изначальная клавиатура админа"""
    kb = [
        [
            types.KeyboardButton(text="Посмотреть заявки"),
            types.KeyboardButton(text="Посмотреть жалобы"),
        ],
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True
    )

    return keyboard


async def admin_keyboard_notification():
    """Клавиатура, которая показывается тогда, когда пользователь кинул заявку"""
    inline_buttons = [
        [types.InlineKeyboardButton(text='Подтвердить анкету', callback_data='confirm_form')],
        [types.InlineKeyboardButton(text='Отправить на перезаполнение анкеты', callback_data='send_for_editing')],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=inline_buttons)
    return keyboard


async def admin_keyboard_notification_with_user_id(user_id: str):
    """Клавиатура, которая показывается тогда, когда пользователь кинул заявку"""
    inline_buttons = [
        [types.InlineKeyboardButton(text='Подтвердить анкету', callback_data=f'confirm_opinion:{user_id}')],
        [types.InlineKeyboardButton(text='Отправить на перезаполнение анкеты', callback_data='send_for_editing')],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=inline_buttons)
    return keyboard


async def admin_keyboard_notification_complaint(user_id: str):
    """Клавиатура, которая показывается тогда, когда пользователь кинул заявку"""
    inline_buttons = [
        [types.InlineKeyboardButton(text='Подтвердить жалобу', callback_data=f'confirm_block:{user_id}')],
        [types.InlineKeyboardButton(text='Отклонить жалобу', callback_data=f'block_reject:{user_id}')],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=inline_buttons)
    return keyboard


async def start_key_with_admin():
    """Кнопка с регистрацией.(админ) Первое нажатие на /start и последующие"""
    kb = [
        [
            types.KeyboardButton(text="Анкеты"),
            types.KeyboardButton(text="Посмотреть профиль"),
        ],
        [
            types.KeyboardButton(text="Админ-панель"),
        ],
        [
            types.KeyboardButton(text="Начать")
        ]
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True
    )

    return keyboard


async def start_key_with_admin_not_register():
    """Кнопка с регистрацией.(админ) Это для тех админов, которые незарегистрированные"""
    kb = [
        [
            types.KeyboardButton(text="Начать"),
            types.KeyboardButton(text="Админ-панель"),
        ],
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True
    )

    return keyboard


async def admin_keyboard_ban_decision(user_id: str):
    inline_buttons = [
        [
            types.InlineKeyboardButton(text="Забанить", callback_data=f"ban:{user_id}"),
            types.InlineKeyboardButton(text="Не блокировать", callback_data=f"dont_ban:{user_id}")
        ]
    ]

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=inline_buttons)
    return keyboard
