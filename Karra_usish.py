from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery, FSInputFile, BufferedInputFile
from states import Registration, Rs, Mailing
from utils import *
from keyboards import contact_button, question1, question2, question3
from config import *
import asyncio
from db_setting import database
from io import StringIO

bot = Bot(token=token)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()

# Семафор для ограничения параллельных операций
BROADCAST_SEMAPHORE = asyncio.Semaphore(30)  # Максимум 30 одновременных отправок
API_SEMAPHORE = asyncio.Semaphore(5)  # Максимум 5 параллельных API запросов


async def on_startup_notify():
    try:
        await bot.send_message(827950639, "Бот Запущен")
    except Exception as err:
        await bot.send_message(827950639, text=f"{err}")


async def on_startup():
    await database.create_table()
    await on_startup_notify()


@router.message(Command("rs"))
async def broadcast(message: Message, state: FSMContext):
    if message.from_user.id in [3325847, 6287458105, 827950639, 1150929995, 2104263081]:
        await state.set_state(Mailing.waiting_for_content)
        await message.reply("Введите текст для рассылки.")
    else:
        await message.reply("Вы не админ.")


@router.message(Command("all"))
async def get_all(message: Message):
    users = await database.get_all_users()

    buffer = StringIO()
    for i in users:
        buffer.write(f"ID == {i[0]} -- Name == {i[1]} -- Number == {i[2]}\n")

    file_content = buffer.getvalue().encode('utf-8')
    buffer.close()

    await message.answer_document(
        BufferedInputFile(file_content, filename="users.txt")
    )


@router.message(Command("rs_text"))
async def rs_withtext(message: Message, state: FSMContext):
    if message.from_user.id in [3325847, 6287458105, 827950639]:
        await state.set_state(Rs.photo)
        await message.reply("Пришли фото для рассылки")


@router.message(Rs.photo, F.photo)
async def get_file(message: Message, state: FSMContext):
    await state.update_data(photo=message.photo[-1].file_id)
    await state.set_state(Rs.text)
    await message.reply("Теперь отправь текст")


@router.message(Rs.text, F.text)
async def get_text(message: Message, state: FSMContext):
    data = await state.get_data()
    users = await database.get_all_users()

    # Запускаем рассылку в фоне
    asyncio.create_task(
        broadcast_background(
            admin_chat_id=message.chat.id,
            users=users,
            content_type="photo",
            content=data['photo'],
            caption=message.html_text
        )
    )

    await message.answer("⏳ Рассылка запущена в фоновом режиме...")
    await state.clear()


@router.message(Command("add"))
async def add_user(message: Message, state: FSMContext):
    await state.set_state("add")
    await message.reply("Отправь пользователя")


# ✅ КРИТИЧЕСКАЯ ОПТИМИЗАЦИЯ: Рассылка с батчингом и семафором
async def send_one_message(user_id, content_type, content, caption=None):
    """Отправка одного сообщения с ограничением по семафору"""
    async with BROADCAST_SEMAPHORE:
        try:
            if content_type == "text":
                await bot.send_message(chat_id=user_id, text=content)
            elif content_type == "photo":
                await bot.send_photo(chat_id=user_id, photo=content, caption=caption or "")
            elif content_type == "document":
                await bot.send_document(chat_id=user_id, document=content)
            elif content_type == "video_note":
                await bot.send_video_note(chat_id=user_id, video_note=content)
            return None  # Успешно
        except Exception as e:
            return user_id  # Ошибка


async def broadcast_background(admin_chat_id, users, content_type, content, caption=None):
    """Фоновая рассылка с максимальной скоростью"""

    # Создаем все задачи сразу (семафор ограничит параллелизм)
    tasks = [
        send_one_message(user[0], content_type, content, caption)
        for user in users
    ]

    # Выполняем все параллельно (но с ограничением через семафор)
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Собираем ошибки
    failed_ids = [r for r in results if r is not None]

    if failed_ids:
        # Получаем данные о пользователях с ошибками
        buffer = StringIO()
        for user_id in failed_ids:
            user = await database.get_user_by_id(user_id)
            if user:
                buffer.write(f"id = {user[0]} -- name = {user[1]} -- number = {user[2]}\n")

        file_content = buffer.getvalue().encode('utf-8')
        buffer.close()

        await bot.send_document(
            chat_id=admin_chat_id,
            document=BufferedInputFile(file_content, filename="rs.txt"),
            caption=f"❌ Не доставлено: {len(failed_ids)} из {len(users)}"
        )

    await bot.send_message(
        admin_chat_id,
        f"✅ Рассылка завершена!\n📊 Всего: {len(users)}\n✅ Доставлено: {len(users) - len(failed_ids)}\n❌ Ошибок: {len(failed_ids)}"
    )


@router.message(F.text | F.photo | F.document | F.video_note, Mailing.waiting_for_content)
async def broadcast_handler(message: Message, state: FSMContext):
    users = await database.get_all_users()

    # Определяем тип контента
    if message.document:
        content_type, content, caption = "document", message.document.file_id, None
    elif message.video_note:
        content_type, content, caption = "video_note", message.video_note.file_id, None
    elif message.photo:
        content_type, content, caption = "photo", message.photo[-1].file_id, message.caption
    elif message.text:
        content_type, content, caption = "text", message.html_text, None
    else:
        await message.answer("Неподдерживаемый тип контента")
        return

    asyncio.create_task(
        broadcast_background(message.chat.id, users, content_type, content, caption)
    )

    await message.answer(f"⏳ Рассылка запущена для {len(users)} пользователей...")
    await state.clear()


# ✅ ОПТИМИЗАЦИЯ: Параллельные API вызовы с семафором
async def safe_api_call(func, *args):
    """Безопасный вызов внешнего API с ограничением параллелизма"""
    async with API_SEMAPHORE:
        return await asyncio.to_thread(func, *args)


@router.message(CommandStart())
async def get_start(message: Message, state: FSMContext):
    args = message.text.split()[1] if len(message.text.split()) > 1 else None

    if args:
        greet = """📢 Рўйхатдан ўтганингиз учун рахмат! Муҳим маълумотларни йўқотиб қўймаслик учун, илтимос, бизнинг Telegram гуруҳимизга қўшилинг: 🔗 https://t.me/+3u2_R1E7JcE1MzFi"""

        # ✅ Все отправки параллельно
        # await asyncio.gather(
        #     message.answer_document(
        #         document="BQACAgIAAxkDAAIjTGjDuGP3F5b6Dx5K5cCjG-TgkxE8AAKjcAACOcMhStd_qMZXLyqeNgQ",
        #         caption="Чек-лист"
        #     ),
        #     message.answer(greet)
        # )

        await message.answer(
            " Бизнинг вебинарга яхшироқ "
            "тайёргарлик кўриш учун, компаниянгизда нечта ходим ишлайди?",
            reply_markup=question1
        )

        await state.set_state(Registration.num_emploeyes)

        d = args.split("--")

        await database.insert_into(message.from_user.id, d[0], f"+{d[1]}")
        contact_id = await create_lead(d[0], f"+{d[1]}")

        await state.update_data({
            "name": d[0],
            "number": f"+{d[1]}",
            "from_landing": 1,
            "contact_id": contact_id
        })
    else:
        text = """📢 Ассалому алайкум! Сотувлар камайган, жамоа сустлашган. Қандай қилиб Кучли жамоа ва Янги ўсиш тизими орқали бизнесингизни қайта жонлантиришингиз мумкин?

31-июль куни соат 19:00 да Барно ва Шерзод Турсуновлар ҳамда Бекзод Камилов билан ўтказиладиган вебинарга рўйхатдан ўтиш учун, илтимос, маълумотларингизни юборинг."""

        await message.answer(text=text)
        await message.answer(text="👤 Илтимос, исм ва фамилиянгизни киритинг.")
        await state.set_state(Registration.name)


@router.message(Registration.name, F.text)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    data = await state.get_data()

    await message.answer(
        f"📞 Раҳмат, {data['name']}! Енди, илтимос, "
        f"телефон рақамингизни пастдаги тугма орқали улашинг.",
        reply_markup=contact_button
    )
    await state.set_state(Registration.phone)


@router.message(Registration.phone)
async def get_number(message: Message, state: FSMContext):
    phone = message.text or message.contact.phone_number
    data = await state.get_data()

    # ✅ ВСЕ операции параллельно (БД + 2 API)
    await database.insert_into(message.from_user.id, data['name'], phone)
    await create_lead(data['name'], phone)

    await state.update_data(number=phone, from_landing=0)

    await message.answer(
        "📢 Рўйхатдан ўтганингиз учун рахмат, "
        "Муҳим маълумотларни йўқотиб қўймаслик учун, илтимос, бизнинг Telegram гуруҳимизга қўшилинг: 🔗 https://t.me/+SloaN4FmJ54zMjBi."
    )
    await message.answer(
        "Бизнинг вебинарга яхшироқ тайёргарлик кўриш учун, компаниянгизда нечта ходим ишлайди?",
        reply_markup=question1
    )
    await state.set_state(Registration.num_emploeyes)


@router.callback_query(F.data.startswith("q_"), Registration.num_emploeyes)
async def get_num_emploeyes(call: CallbackQuery, state: FSMContext):
    ans = call.data.split("_")[1]
    await state.update_data(num_emploeyes=ans)

    await call.message.answer(
        "Раҳмат! Сизнинг компаниянгизнинг йиллик обороти қанча? "
        "Бу маълумот вебинарга яхшироқ тайёргарлик кўриш учун керак.",
        reply_markup=question2
    )
    await state.set_state(Registration.turnover)
    await call.answer()


@router.callback_query(F.data.startswith("q_"), Registration.turnover)
async def get_turnover(call: CallbackQuery, state: FSMContext):
    ans = call.data.split("_")[1]
    await state.update_data(turnover=ans)

    await call.message.answer(
        'Биз сизга ёрдам беришга деярли тайёрмиз. '
        'Компанияда қандай ролни бажараётганингизни аниқлаб беринг 🌟',
        reply_markup=question3
    )
    await state.set_state(Registration.role)
    await call.answer()


@router.callback_query(F.data.startswith("q_"), Registration.role)
async def get_role(call: CallbackQuery, state: FSMContext):
    ans = call.data.split("_")[1]
    await state.update_data(role=ans)
    data = await state.get_data()

    await contact_new_data(
        data['contact_id'],
        data['num_emploeyes'],
        data['turnover'],
        data['role']
    )

    await call.message.answer(
        "Жавобларингиз учун раҳмат! Биз ишонамизки, "
        "вебинаримиз айнан сиз учун мос. Вебинарда кўришгунча! "
        "Муҳим маълумотларни йўқотиб қўймаслик учун, илтимос, бизнинг Telegram гуруҳимизга қўшилинг: 🔗 https://t.me/+3u2_R1E7JcE1MzFi"
    )

    await state.clear()
    await call.answer()


async def main():
    dp.include_router(router)
    await on_startup()

    try:
        await dp.start_polling(bot, skip_updates=True)
    finally:
        await close_http_client()


if __name__ == "__main__":
    asyncio.run(main())
