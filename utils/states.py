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
    main_in_life = State()
    main_in_people = State()
    smoking_attitude = State()
    alcohol_attitude = State()


class EditUser(StatesGroup):
    edited_name = State()


class EditAge(StatesGroup):
    edited_age = State()


class EditPhoto(StatesGroup):
    edited_photo = State()
    additional_photo = State()


class EditAboutMe(StatesGroup):
    edited_about_me = State()


class EditCity(StatesGroup):
    edited_city = State()


class EditCitySearch(StatesGroup):
    edited_city = State()


class EditMainInLife(StatesGroup):
    edited_main_in_life = State()


class EditMainInPeople(StatesGroup):
    edited_main_in_people = State()


class EditSmokingAttitude(StatesGroup):
    edited_smoking_attitude = State()


class EditAlcoholAttitude(StatesGroup):
    edited_alcohol_attitude = State()


class PutSms(StatesGroup):
    send_message = State()


class EditInterests(StatesGroup):
    interest = State()
