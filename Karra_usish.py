from aiogram import types, Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.utils import executor
from aiogram.dispatcher.filters import CommandStart
from states import Registration, Rs
from utils import contact_save, create_contact, lead_create_without_landing, create_lead, contact_new_data
from keyboards import contact_button, question1, question2, question3
from config import *
import asyncio
from aiogram.types import InputFile
import aiogram
from db_setting import database

bot = Bot(token=token, parse_mode="HTML")
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
# voronka_id = 9317886


async def on_startup_notify(dispatcher: Dispatcher):
    try:
        await dispatcher.bot.send_message(827950639, "Бот Запущен")

    except Exception as err:
        await dispatcher.bot.send_message(827950639, text=f"{err}")


async def on_startup(dispatcher):
    database.create_table()
    await on_startup_notify(dispatcher)


@dp.message_handler(commands=['rs'])
async def broadcast(message: types.Message, state: FSMContext):
    if message.from_user.id in [3325847, 6287458105, 827950639]:
        await state.set_state("broadcast")
        await message.reply("Введите текст для рассылки.")
    else:
        await message.reply("Вы не админ.")


@dp.message_handler(commands=['all'])
async def get_all(message: types.Message):
    # slot = message.text.split(" ")[1]
    users = database.get_all_users()
    msg = ""
    file_path = "users.txt"
    for i in users:
        msg += f"ID == {i[0]} -- Name == {i[1]} -- Number == {i[2]}\n"
    with open("users.txt", "w") as f:
        f.write(msg)
    await message.answer_document(InputFile(file_path))


@dp.message_handler(commands=['rs_text'])
async def rs_withtext(message: types.Message, state: FSMContext):
    if message.from_user.id in [3325847, 6287458105, 827950639]:
        await Rs.photo.set()
        await message.reply("Пришли текст для рассылки")


@dp.message_handler(content_types=types.ContentTypes.ANY, state=Rs.photo)
async def get_file(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['photo'] = message.photo[-1].file_id
    await Rs.text.set()
    await message.reply("Send a text")


@dp.message_handler(content_types=types.ContentTypes.ANY, state=Rs.text)
async def get_text(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        users = set(database.get_all_users())
        msg = ""
        cap = message.text
        for i in users:
            try:
                await bot.send_photo(
                    chat_id=i[0],
                    photo=data['photo'],
                    caption=message.html_text
                )
            except Exception as e:
                user = database.get_user_by_id(int(i[0]))
                msg += f"id = {user[0]} -- name = {user[1]} -- number = {user[2]}\n"
    await state.finish()






@dp.message_handler(commands=['add'])
async def add_user(message: types.Message, state: FSMContext):
    await state.set_state("add")
    await message.reply("Отправь пользователя")


@dp.message_handler(state="add")
async def insert(message: types.Message, state: FSMContext):
    if message.text == "stop":
        await state.finish()
        return 1
    lst = message.text.split(" ")
    print(lst)
    database.insert_into(lst[0], lst[1], lst[2])
    await message.reply("Добавилось")


@dp.message_handler(content_types=types.ContentTypes.ANY, state="broadcast")
async def broadcast_handler(message: types.Message, state: FSMContext):

    users = set(database.get_all_users())
    msg = ""
    if message.document:
        for i in users:
            try:
                await bot.send_document(
                    chat_id=i[0],
                    document=message.document.file_id
                )
            except Exception as e:
                user = database.get_user_by_id(int(i[0]))
                msg += f"id = {user[0]} -- name = {user[1]} -- number = {user[2]}\n"

    if message.video_note:
        for i in users:
            try:

                await bot.send_video_note(
                    chat_id=i[0],
                    video_note=message.video_note.file_id
                )
            except Exception as e:
                user = database.get_user_by_id(int(i[0]))
                msg += f"id = {user[0]} -- name = {user[1]} -- number = {user[2]}\n"

    if message.photo:
        for i in users:
            try:
                await bot.send_photo(
                    chat_id=i[0],
                    photo=message.photo[-1].file_id,
                    caption=message.caption or "",
                )
            except Exception as e:
                user = database.get_user_by_id(int(i[0]))
                msg += f"id = {user[0]} -- name = {user[1]} -- number = {user[2]}\n"
    if message.text:
        for i in users:
            try:
                await bot.send_message(
                    chat_id=i[0],
                    text=message.html_text
                )
            except Exception as e:
                user = database.get_user_by_id(int(i[0]))
                msg += f"id = {user[0]} -- name = {user[1]} -- number = {user[2]}\n"

    with open("rs.txt", "w") as f:
        f.write(msg)
    await message.answer_document(InputFile("rs.txt"), caption="Те до которых не дошла рассылка.")

    await message.answer("Рассылка завершена!")

    await state.finish()


@dp.message_handler(CommandStart())
async def get_start(message: types.Message, state: FSMContext):
    args = message.get_args()
    if args:
        # print(args)
        greet = """📢 Рўйхатдан ўтганингиз учун рахмат! Муҳим маълумотларни йўқотиб қўймаслик учун, илтимос, бизнинг Telegram гуруҳимизга қўшилинг: 🔗 https://t.me/+3u2_R1E7JcE1MzFi"""
        await message.answer_document("BQACAgIAAxkDAAIjTGjDuGP3F5b6Dx5K5cCjG-TgkxE8AAKjcAACOcMhStd_qMZXLyqeNgQ",
                                      caption="Чек-лист")
        # await bot.send_document(chat_id=message.from_user.id, document="BQACAgIAAxkDAAM-aK2dVGpzjy8d0t16_0OrFfsCHe0AAvCFAAKUt3BJnvhn9u1OxUc2BA")
        await message.answer(greet)
        await message.answer(
            " Бизнинг вебинарга яхшироқ "
            "тайёргарлик кўриш учун, компаниянгизда нечта ходим ишлайди?",
            reply_markup=question1
        )
        msg = await message.answer("Илтимос, бироз кутинг ......")

        await Registration.num_emploeyes.set()
        # print(args)
        d = args.split("--")
        # print("d 3- ", d)
        # database.insert_into(message.from_user.id, d[0], f"+{d[1]}", d[2], d[3], d[4])
        database.insert_into_two_params(message.from_user.id, d[0], f"+{d[1]}")
        contact_id = create_lead(d[0], f'+{d[1]}')
        l = {
            "name": d[0],
            "number": f"+{d[1]}",
            "from_landing": 1,
            "contact_id": contact_id
        }



        # create_contact(d[0], d[1])
        # lead_create_without_landing(d[0], d[1])
        await bot.delete_message(message.from_user.id, msg.message_id)
        await state.set_data(l)
    else:
        text = """📢 Ассалому алайкум! Сотувлар камайган, жамоа сустлашган. Қандай қилиб Кучли жамоа ва Янги ўсиш тизими орқали бизнесингизни қайта жонлантиришингиз мумкин?

31-июль куни соат 19:00 да Барно ва Шерзод Турсуновлар ҳамда Бекзод Камилов билан ўтказиладиган вебинарга рўйхатдан ўтиш учун, илтимос, маълумотларингизни юборинг."""
        await message.answer(text=text)
        await message.answer(text="👤 Илтимос, исм ва фамилиянгизни киритинг.")
        await Registration.name.set()


@dp.message_handler(content_types=types.ContentTypes.TEXT, state=Registration.name)
async def get_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text
        await message.answer(f"📞 Раҳмат, {data['name']}! Енди, илтимос, "
                             f"телефон рақамингизни пастдаги тугма орқали улашинг.", reply_markup=contact_button)
    await Registration.next()


@dp.message_handler(content_types=types.ContentTypes.ANY, state=Registration.phone)
async def get_number(message: types.Message, state: FSMContext):
    msg = await message.answer("Илтимос, бироз кутинг ......")
    async with state.proxy() as data:
        data['number'] = message.text or message.contact.phone_number
        data['from_landing'] = 0
        create_contact(data['name'], data['number'])
        lead_create_without_landing(data['name'], data['number'])
        database.insert_into(message.from_user.id, data['name'], data['number'])
    await bot.delete_message(message.from_user.id, msg.message_id)
    await message.answer("📢 Рўйхатдан ўтганингиз учун рахмат, "
                         "Муҳим маълумотларни йўқотиб қўймаслик учун, илтимос, бизнинг Telegram гуруҳимизга қўшилинг: 🔗 https://t.me/+SloaN4FmJ54zMjBi.")
    await message.answer("Бизнинг вебинарга яхшироқ тайёргарлик кўриш учун, компаниянгизда нечта ходим ишлайди?",
                         reply_markup=question1)
    await Registration.next()


@dp.callback_query_handler(lambda x: x.data and x.data.startswith("q_"), state=Registration.num_emploeyes)
async def get_num_emploeyes(call: types.CallbackQuery, state: FSMContext):
    ans = call.data.split("_")[1]
    async with state.proxy() as data:
        data['num_emploeyes'] = ans

    await call.message.answer("Раҳмат! Сизнинг компаниянгизнинг йиллик обороти қанча? "
                              "Бу маълумот вебинарга яхшироқ тайёргарлик кўриш учун керак.",
                              reply_markup=question2)
    await Registration.turnover.set()


@dp.callback_query_handler(lambda x: x.data and x.data.startswith("q_"), state=Registration.turnover)
async def get_turnover(call: types.CallbackQuery, state: FSMContext):
    ans = call.data.split("_")[1]
    async with state.proxy() as data:
        data['turnover'] = ans
    await call.message.answer('Биз сизга ёрдам беришга деярли тайёрмиз. '
                              'Компанияда қандай ролни бажараётганингизни аниқлаб беринг 🌟',
                              reply_markup=question3)
    await Registration.role.set()


@dp.callback_query_handler(lambda x: x.data and x.data.startswith("q_"), state=Registration.role)
async def get_(call: types.CallbackQuery, state: FSMContext):
    ans = call.data.split("_")[1]

    async with state.proxy() as data:
        data['role'] = ans
        msg = await call.answer("Илтимос, бироз кутинг ......", show_alert=True)
        # contact_save(
        #     num_emploeyes=data['num_emploeyes'],
        #     turnover=data['turnover'],
        #     role=data['role'],
        #     number=data['number']
        # )
        contact_new_data(data['contact_id'], data['num_emploeyes'], data['turnover'], data['role'])

        # if data['from_landing'] == 0:
        #     lead_create_without_landing(data['number'], data['name'])
        # await bot.delete_message(call.message.from_user.id, msg.message_id)
        await call.message.answer("Жавобларингиз учун раҳмат! Биз ишонамизки, "
                                  "вебинаримиз айнан сиз учун мос. Вебинарда кўришгунча!"
                                  "Муҳим маълумотларни йўқотиб қўймаслик учун, илтимос, бизнинг Telegram гуруҳимизга қўшилинг: 🔗 https://t.me/+3u2_R1E7JcE1MzFi")

    await state.finish()

    # await state.finish()


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
