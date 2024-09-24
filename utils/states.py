from aiogram.fsm.state import StatesGroup, State


class RegisterUser(StatesGroup):
    name = State()
    age = State()
    city = State()
    about_me = State()
    gender = State()
    interests = State()
    photo_or_video = State()
    additional_photo = State()


class EditUser(StatesGroup):
    edited_name = State()


class EditAge(StatesGroup):
    edited_age = State()


class EditPhoto(StatesGroup):
    edited_photo = State()
    additional_photo = State()


class EditAboutMe(StatesGroup):
    edited_about_me = State()


class PutSms(StatesGroup):
    send_message = State()


class EditInterests(StatesGroup):
    interest = State()
