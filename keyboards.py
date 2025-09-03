from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup

contact = KeyboardButton(text="Telefon raqam", request_contact=True)
contact_button = ReplyKeyboardMarkup(keyboard=[[contact]], resize_keyboard=True, one_time_keyboard=True)


question1 = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="1-10", callback_data="q_1-10"),
            InlineKeyboardButton(text="10-25", callback_data="q_10-25"),
            InlineKeyboardButton(text="25-50", callback_data="q_25-50"),
            InlineKeyboardButton(text="50-100", callback_data="q_50-100")
        ]
    ]
)
# question1.add(
#     InlineKeyboardButton(text="1-10", callback_data="q_1-10"),
#     InlineKeyboardButton(text="10-25", callback_data="q_10-25"),
#     InlineKeyboardButton(text="25-50", callback_data="q_25-50"),
#     InlineKeyboardButton(text="50-100", callback_data="q_50-100")
# )


question2 = InlineKeyboardMarkup(
    inline_keyboard=
    [
        [
            InlineKeyboardButton(text="$5 000-50 000", callback_data="q_$5000-50000"),
            InlineKeyboardButton(text="$50 000-500 000", callback_data="q_$50000-500000"),
            InlineKeyboardButton(text="$1 млн", callback_data="q_$1mln"),
            InlineKeyboardButton(text="$2 млн", callback_data="q_$2mln")
        ]
    ]
)
# question2.add(
#     InlineKeyboardButton(text="$5 000-50 000", callback_data="q_$5000-50000"),
#     InlineKeyboardButton(text="$50 000-500 000", callback_data="q_$50000-500000"),
#     InlineKeyboardButton(text="$1 млн", callback_data="q_$1mln"),
#     InlineKeyboardButton(text="$2 млн", callback_data="q_$2mln")
# )

question3 = InlineKeyboardMarkup(
    inline_keyboard=
    [
        [
            InlineKeyboardButton(text="Ходим", callback_data="q_xodim"),
            InlineKeyboardButton(text="Бизнес эгаси", callback_data="q_biznes-egasi"),
            InlineKeyboardButton(text="Топ менеджер", callback_data="q_top-menejer"),
        ]
    ]
)
# question3.add(
#     InlineKeyboardButton(text="Ходим", callback_data="q_xodim"),
#     InlineKeyboardButton(text="Бизнес эгаси", callback_data="q_biznes-egasi"),
#     InlineKeyboardButton(text="Топ менеджер", callback_data="q_top-menejer"),
#
# )

# ha = InlineKeyboardMarkup()
# ha.add(
#     InlineKeyboardButton(
#         text="Ha!", callback_data="ha"
#     )
# )
