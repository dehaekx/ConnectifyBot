from aiogram import types
from aiogram.fsm.context import FSMContext

from keyboards import keyboards as K
from keyboards.keyboards import InterestFilter
from utils.copy_bot import bot
from utils.maps import INTERESTS_MAP
from utils import db_functions as DF


async def back_to_menu(query):
    await query.message.answer(text="Вы в главном меню", reply_markup=await K.keyboard_for_user())

"""После нажатия на любой интерес появляется значок ГАЛОЧКИ"""
async def update_interests_keyboard(selected_interests): 
    inline_buttons = []
    row = []
    for key, value in INTERESTS_MAP.items():
        callback_data = InterestFilter(action="select", value=key).pack()
        if key in selected_interests:
            text = f"{value} ✅"
        else:
            text = value
        button = types.InlineKeyboardButton(text=text, callback_data=callback_data)
        row.append(button)
        if len(row) == 2:
            inline_buttons.append(row)
            row = []
    if row:
        inline_buttons.append(row)
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=inline_buttons)
    return keyboard


async def send_notification_me(liked_id: str, message: str, state: FSMContext):
    """Отправляет уведомление пользователю. Тогда когда лайкнули его"""
    try:
        user = await DF.get_user_by_id(liked_id)
        liker_id = user["user_id"]
        # data = await state.get_data()
        # liker_id = data.get("liker_id")
        await bot.send_message(liker_id, message, reply_markup=await K.questionnaire_look_me(liked_id))
        await state.update_data(liked_id=liked_id)
    except Exception as e:
        print(f"Failed to send notification to user {liked_id}: {e}")
