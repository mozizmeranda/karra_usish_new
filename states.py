from aiogram.fsm.state import StatesGroup, State
# from aiogram.fsm.state import State, StatesGroup


class Registration(StatesGroup):
    name = State()
    phone = State()
    num_emploeyes = State()
    turnover = State()
    role = State()


class Rs(StatesGroup):
    photo = State()
    text = State()


class Mailing(StatesGroup):
    waiting_for_content = State()
