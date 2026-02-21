from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery, FSInputFile, BufferedInputFile
from states import Registration, Rs, Mailing
from utils import *
from keyboards import contact_button, question1, question2, question3
from datetime import datetime, timedelta, timezone
from config import *
import asyncio
from db_setting import database
from zoneinfo import ZoneInfo
from io import StringIO

bot = Bot(token=token)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()
TASHKENT_TZ = ZoneInfo("Asia/Tashkent")

# Семафор для ограничения параллельных операций
BROADCAST_SEMAPHORE = asyncio.Semaphore(30)  # Максимум 30 одновременных отправок
API_SEMAPHORE = asyncio.Semaphore(5)  # Максимум 5 параллельных API запросов


async def on_startup_notify():
    try:
        await bot.send_message(827950639, "Бот Запущен")
    except Exception as err:
        await bot.send_message(827950639, text=f"{err}")


async def on_startup():
    await bot.send_message(827950639, text="Бот запущен")
    await database.connect()
    await database.create_table()


async def on_shutdown():
    await database.close()


@dp.message(Command("checkpoint"))
async def cmd_checkpoint(message: Message):
    await database.checkpoint()
    await message.answer("Готово, можно скачивать")


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


# ✅ КРИТИЧЕСКАЯ ОПТИМИЗАЦИЯ: Рассылка с батчингом и семафором
async def send_one_message(user_id, content_type, content, enteties, caption=None):
    """Отправка одного сообщения с ограничением по семафору"""
    async with BROADCAST_SEMAPHORE:
        try:
            if content_type == "text":
                await bot.send_message(chat_id=user_id, text=content, parse_mode="MarkdownV2", entities=enteties)
            elif content_type == "photo":
                await bot.send_photo(chat_id=user_id, photo=content, caption=caption or "", caption_entities=enteties)
            elif content_type == "document":
                await bot.send_document(chat_id=user_id, document=content, caption=caption, caption_entities=enteties)
            elif content_type == "video_note":
                await bot.send_video_note(chat_id=user_id, video_note=content)
            return None  # Успешно
        except Exception as e:
            notify_admin(
                function_name=notify_admin.__name__,
                message_error=str(e),
                user_id=user_id,
                traceback=traceback.format_exc()
            )
            return user_id  # Ошибка


async def broadcast_background(admin_chat_id, users, content_type, content, enteties, caption=None):
    """Фоновая рассылка с максимальной скоростью"""

    # Создаем все задачи сразу (семафор ограничит параллелизм)
    tasks = [
        send_one_message(user[0], content_type, content, enteties, caption)
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
        content_type, content, caption, entities = "document", message.document.file_id, None, message.caption_entities
    elif message.video_note:
        content_type, content, enteties, caption = "video_note", message.video_note.file_id, None, None
    elif message.photo:
        content_type, content, caption, entities = "photo", message.photo[-1].file_id, message.caption, message.caption_entities
    elif message.text:
        content_type, content, caption, enteties = "text", message.text, None, message.entities
    else:
        await message.answer("Неподдерживаемый тип контента")
        return

    asyncio.create_task(
        broadcast_background(message.chat.id, users, content_type, content, entities, caption)
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
        greet = """Ўзбекистон бозори сиз ўйлагандан ҳам тезроқ ўзгаряпти. Бугун бизнесида тизим қуришга улгурмаганлар, эртага кучли ўйинчилар билан рақобатга тайёр бўлолмай қолади.

Айнан шунинг учун биз "Барқарор бизнесга 5 қадам" реалити лойиҳасини бошлаяпмиз.

Ичида — айланмаси юз миллионлаб долларга етган бизнесларда шахсан ўзимиз қўллаг синовлардан ўтган 5 та инструмент бор. Улар сизга бизнесингизда тизим қуриш, рақобатбардош бўлиш ва бозорда нима бўлишидан қатъи назар, ишонч билан ҳаракат қилишга ёрдам беради.

Каналга қўшилиш учун қуйидаги қисқа саволларга жавоб беринг 👇"""

        if message.from_user.username:
            username = message.from_user.username
        else:
            username = "Отсутствует"

        await message.answer(greet)
        await message.answer(
            "Компаниянгизда нечта ходим ишлайди?",
            reply_markup=question1
        )
        now_tashkent = datetime.now(TASHKENT_TZ)
        next_time = now_tashkent + timedelta(minutes=10)
        next_time_str = next_time.strftime("%Y-%m-%d %H:%M:%S")

        await state.set_state(Registration.num_emploeyes)

        d = args.split("--")

        await database.insert_into(
            telegram_id=message.from_user.id,
            name=d[0],
            number=f"+{d[1]}",
            reminder_step=0,
            next_reminder_at=next_time_str
        )

        # await database.insert_into(message.from_user.id, d[0], f"+{d[1]}")
        contact_id = await create_lead(d[0], f"+{d[1]}", username)

        await state.update_data({
            "name": d[0],
            "number": f"+{d[1]}",
            "from_landing": 1,
            "contact_id": contact_id
        })
    else:
        text = """Ассалому алайкум!

Сиз “Барқарор бизнесга 5 қадам” реалити лойиҳасига қўшиляпсиз.

Бу ерда сиз:
— бизнесда тизим қуриш,
— рақобатбардошликни ошириш,
— бозор қандай ўзгаришидан қатъи назар барқарор ўсишни таъминлаш учун амалда синовдан ўтган 5 та инструментни оласиз.

Барчаси реал бизнес тажрибасига асосланган.
Аввало, танишиб олайлик.
"""

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
    # await database.insert_into(message.from_user.id, data['name'], phone)
    now_tashkent = datetime.now(TASHKENT_TZ)
    next_time = now_tashkent + timedelta(minutes=10)
    next_time_str = next_time.strftime("%Y-%m-%d %H:%M:%S")

    await database.insert_into(
        telegram_id=message.from_user.id,
        name=data['name'],
        number=phone,
        reminder_step=0,
        next_reminder_at=next_time_str
    )
    username = message.from_user.username or "Отсутсвует"
    # await create_lead(data['name'], phone, username)
    contact_id = await create_lead(data['name'], phone, username)

    await state.update_data({
        "name": data['name'],
        "number": phone,
        "from_landing": 1,
        "contact_id": contact_id
    })

    await state.update_data(number=phone, from_landing=0)

    await message.answer(
        "📢 Рўйхатдан ўтганингиз учун рахмат. "
    )
    greet = """Ўзбекистон бозори сиз ўйлагандан ҳам тезроқ ўзгаряпти. Бугун бизнесида тизим қуришга улгурмаганлар, эртага кучли ўйинчилар билан рақобатга тайёр бўлолмай қолади.

    Айнан шунинг учун биз "Барқарор бизнесга 5 қадам" реалити лойиҳасини бошлаяпмиз.

    Ичида — айланмаси юз миллионлаб долларга етган бизнесларда шахсан ўзимиз қўллаг синовлардан ўтган 5 та инструмент бор. Улар сизга бизнесингизда тизим қуриш, рақобатбардош бўлиш ва бозорда нима бўлишидан қатъи назар, ишонч билан ҳаракат қилишга ёрдам беради.

    Каналга қўшилиш учун қуйидаги қисқа саволларга жавоб беринг 👇"""
    await message.answer(
        greet
    )
    await message.answer(
        "Компаниянгизда нечта ходим ишлайди?",
        reply_markup=question1
    )
    await state.set_state(Registration.num_emploeyes)


@router.callback_query(F.data.startswith("q_"), Registration.num_emploeyes)
async def get_num_emploeyes(call: CallbackQuery, state: FSMContext):
    ans = call.data.split("_")[1]
    await state.update_data(num_emploeyes=ans)

    await call.message.answer(
        "Раҳмат! Сизнинг компаниянгизнинг йиллик обороти қанча?",
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
    await call.answer("Илтимос озгина кутинг....")
    await contact_new_data(
        data['contact_id'],
        data['num_emploeyes'],
        data['turnover'],
        data['role']
    )

    await database.stop_reminders(call.from_user.id)

    msg = """Жавобларингиз учун раҳмат!

Энди энг муҳим босқич бошланади.

Барча жараёнлар, жонли эфирлар ва амалий иш жараёнлари
«Кучли бизнес» каналида давом этади.

Бу ерда биз:

— Барқарор ўсишнинг 5 та асосини очиб берамиз
— Уларни ўз бизнесимизда қандай қўллаётганимизни кўрсатамиз
— Шерзод Турсунов билан жонли эфирлар ўтказамиз
— Барно Турсунова билан алоҳида стратегик эфирлар қиламиз
— Қарорлар, хатолар ва натижаларни яширмаймиз

Бу назария эмас.
Бу — реал бизнес.
Ҳаммаси очиқ. Ҳаммаси ичкаридан.

Агарда кучли бизнес қуришни истасангиз, каналга қўшилинг:

👉 https://t.me/+otDpW2c34tI1NTQy"""

    await call.message.answer(msg)

    await state.clear()
    await call.answer()


async def main():
    dp.include_router(router)
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    try:
        await dp.start_polling(bot, skip_updates=True)
    finally:
        await close_http_client()


if __name__ == "__main__":
    asyncio.run(main())
