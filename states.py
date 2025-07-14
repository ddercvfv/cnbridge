from aiogram.dispatcher.filters.state import State, StatesGroup

class PromoStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()
