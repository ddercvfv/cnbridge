import logging
import random
import string
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command, Text

from states import PromoStates
from db import init_db, save_user

API_TOKEN = "7879820560:AAFckNCfRBBJuE_RpfQkhySItt7ACM_y2Lk"
MANAGER_ID = 7657798402

logging.basicConfig(level=logging.INFO, filename="bot.log", filemode="a", format="%(asctime)s - %(levelname)s - %(message)s")

bot = Bot(token=API_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot, storage=MemoryStorage())

# Храним ID пользователей, получивших промокод
issued_promos = set()

# Клавиатура под /start
start_kb = InlineKeyboardMarkup(row_width=1).add(
    InlineKeyboardButton("Получить промокод", callback_data="get_promo"),
    InlineKeyboardButton("Сайт", url="https://cnbridge.ru/"),
    InlineKeyboardButton("Написать менеджеру", url="tg://user?id=7657798402")
)

@dp.message_handler(commands=["start"])
async def start_cmd(message: types.Message):
    await message.answer(
        "Вас приветствует команда CN Bridge! 👋🏻\n\n"
        "Наша команда уже более 3-х лет быстро и надежно доставляет товары из Китая в Россию и страны СНГ.\n\n"
        "Мы берём на себя все аспекты логистики — от поиска надёжного поставщика до транспортировки товара на Ваш склад.",
        reply_markup=start_kb
    )

@dp.message_handler(commands=["cancel"], state="*")
async def cancel_cmd(message: types.Message, state: FSMContext):
    await state.finish()
    await message.reply("Действие отменено. Введите /start, чтобы начать заново.")

@dp.callback_query_handler(Text(equals="get_promo"))
async def get_promo_start(call: types.CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    if user_id in issued_promos:
        await call.message.answer(
            "❗Вы уже получали промокод. Повторно получить его нельзя.",
            reply_markup=start_kb
        )
        await call.answer()
        return

    await call.message.answer("Напишите ваше имя:")
    await PromoStates.waiting_for_name.set()
    await call.answer()

@dp.message_handler(state=PromoStates.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Укажите ваш номер телефона:")
    await PromoStates.waiting_for_phone.set()

@dp.message_handler(state=PromoStates.waiting_for_phone)
async def process_phone(message: types.Message, state: FSMContext):
    phone = message.text.strip()
    digits = [c for c in phone if c.isdigit()]
    if len(digits) < 10:
        await message.reply("❌ Номер должен содержать минимум 10 цифр. Попробуйте снова:")
        return
    await state.update_data(phone=phone)

    kb = InlineKeyboardMarkup().add(
        InlineKeyboardButton("Сгенерировать промокод", callback_data="generate_promo")
    )
    await message.answer("Нажмите кнопку ниже, чтобы сгенерировать промокод:", reply_markup=kb)

@dp.callback_query_handler(Text(equals="generate_promo"), state="*")
async def generate_promo(call: types.CallbackQuery, state: FSMContext):
    user_id = call.from_user.id

    if user_id in issued_promos:
        await call.message.answer("❗Вы уже получали промокод. Повторно получить его нельзя.", reply_markup=start_kb)
        await call.answer()
        return

    data = await state.get_data()
    name = data.get("name")
    phone = data.get("phone")
    code = f"CNB-{''.join(random.choices(string.ascii_uppercase + string.digits, k=4))}"

    save_user(name, phone, code)
    issued_promos.add(user_id)

    back_kb = InlineKeyboardMarkup().add(
        InlineKeyboardButton("🔙 Назад в главное меню", callback_data="back_to_menu")
    )

    await call.message.answer(
        f"Поздравляем, Ваш промокод готов! 🥳\n\n"
        f"<b>Номер промокода:</b> <code>{code}</code>\n\n"
        "Использовать промокод можно на первую поставку вместе с командой CN Bridge — "
        "для этого назовите его менеджеру @ripsat во время консультации.\n\n"
        "Узнать подробнее о нас: https://cnbridge.ru/",
        reply_markup=back_kb
    )

    await bot.send_message(
        chat_id=MANAGER_ID,
        text=f"🔥 Новый лид из бота:\n\n👤 Имя: {name}\n📞 Телефон: {phone}\n🎁 Промокод: {code}"
    )

    await state.finish()
    await call.answer()

@dp.callback_query_handler(Text(equals="back_to_menu"))
async def back_to_menu(call: types.CallbackQuery):
    await call.message.edit_text(
        "Вы вернулись в главное меню.",
        reply_markup=start_kb
    )
    await call.answer()

if __name__ == "__main__":
    init_db()
    executor.start_polling(dp, skip_updates=True)
