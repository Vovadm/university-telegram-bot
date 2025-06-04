from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


main = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Начать поиск")],
        [KeyboardButton(text="Внести данные")],
        [KeyboardButton(text="Что делать?"), KeyboardButton(text="О нас")],
        [KeyboardButton(text="Просмотреть данные")],
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите пункт меню...",
)


def city_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Москва")],
            [KeyboardButton(text="Санкт-Петербург")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите город...",
    )
    return keyboard


def subjects_keyboard():
    subjects = {
        "Русский": "rus",
        "Математика": "math",
        "Математика профильная": "math_prof",
        "Физика": "phy",
        "Химия": "chem",
        "История": "hist",
        "Обществознание": "soc",
        "Информатика": "inf",
        "Биология": "bio",
        "География": "geo",
        "Английский": "eng",
        "Немецкий": "ger",
        "Французский": "fren",
        "Испанский": "span",
        "Китайский": "chi",
        "Литература": "lit",
    }
    buttons = [
        InlineKeyboardButton(text=rus_name, callback_data=f"sub_{eng_name}")
        for rus_name, eng_name in subjects.items()
    ]

    grouped_buttons = [buttons[i : i + 2] for i in range(0, len(buttons), 2)]
    grouped_buttons.append(
        [InlineKeyboardButton(text="Сохранить данные", callback_data="save")]
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=grouped_buttons)
    return keyboard


clear_data_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Да, удалить старые данные")],
        [KeyboardButton(text="Нет, оставить старые данные")],
        [KeyboardButton(text="Просмотреть данные")],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
)


change_data_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Город"), KeyboardButton(text="Баллы ЕГЭ")],
        [
            KeyboardButton(text="Специальность вуза"),
            KeyboardButton(text="Вернуться в начало"),
        ],
    ],
    resize_keyboard=True,
    input_field_placeholder="Что хотите изменить?",
)

specialization_mapping = {
    "Авиационные": "spec_aviacionnye",
    "Аграрные": "spec_agrarnye",
    "Архитектурные": "spec_arkhitekturnye",
    "Биологические": "spec_biologicheskie",
    "Военные": "spec_voennye",
    "Вузовской культуры": "spec_vuzykultury",
    "Географические": "spec_geograficheskie",
    "Гуманитарные": "spec_gumanitarnye",
    "Дизайна": "spec_dizayna",
    "Информационные": "spec_informacionnye",
    "МВД": "spec_mvd",
    "Медицинские": "spec_medicinckie",
    "МЧС": "spec_mchs",
    "Нефтяные": "spec_neftyanye",
    "Педагогические": "spec_pedagogicheskie",
    "Психологические": "spec_psihologicheskie",
    "Пищевые": "spec_pishevye",
    "Сервис": "spec_servic",
    "Спортивные": "spec_sportivnye",
    "Строительные": "spec_stroitelnye",
    "Технические": "spec_tekhnicheskie",
    "Транспортные": "spec_transportnye",
    "Экономические": "spec_ekonomicheskie",
    "Юридические": "spec_yuridicheskie",
}


def get_clear_data_keyboard():

    buttons = [
        InlineKeyboardButton(
            text="Удалить данные", callback_data="clear_data"
        ),
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
    return keyboard


def generate_budget_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Бюджет"), KeyboardButton(text="Платное")]
        ],
        resize_keyboard=True,
    )
    return keyboard
