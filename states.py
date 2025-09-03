from aiogram.dispatcher.filters.state import State, StatesGroup
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