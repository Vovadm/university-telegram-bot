import logging

from aiogram import F, Router, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy import delete, text
from sqlalchemy.future import select

import app.keyboards as kb
from app.keyboards import specialization_mapping
from db.universiries import SessionLocalUniversity
from db.users import SessionLocalUsers, Specialization, Subject, User


class Form(StatesGroup):
    city = State()
    subject = State()
    change_data = State()
    spec = State()
    search_universities = State()


router = Router()
logger = logging.getLogger(__name__)


@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    welcome_message = (
        "Добро пожаловать, здесь мы поможем тебе найти университет по твоим "
        "баллам ЕГЭ.\nВоспользуйся /help если что-то непонятно!"
    )
    await message.answer(welcome_message, reply_markup=kb.main)


@router.message(F.text == "/help")
@router.message(F.text == "Что делать?")
async def help(message: types.Message):
    text = (
        "1. Воспользуйся коммандой /change_data, чтобы внести или "
        "изменить свои баллы по ЕГЭ\n"
        "2. Теперь нажми на кнопку Начать поиск и ожидай результата"
    )
    await message.answer(text=text, reply_markup=kb.main)


@router.message(F.text == "/about")
@router.message(F.text == "О нас")
async def about(message: types.Message):
    text = (
        "В случае технических сбоев, либо некорректности данных "
        "обращайтесь к @rRaild\n\n"
        "Данные о ВУЗах были взяты с сайта vuzopedia.com\n"
        "Автор не преследует цели присвоить себе какие-либо данные!\n\n"
        "Приятного пользования!"
    )
    await message.answer(text=text, reply_markup=kb.main)


@router.message(F.text == "/change_data")
@router.message(F.text == "Внести данные")
async def ask_to_clear_data(message: Message, state: FSMContext):
    await state.clear()
    async with SessionLocalUsers() as session:
        async with session.begin():

            user_data = (
                (
                    await session.execute(
                        select(Subject).filter_by(
                            tg_id=str(message.from_user.id)
                        )
                    )
                )
                .scalars()
                .first()
            )

            specialization_query = text(
                "SELECT * FROM specializations WHERE tg_id = :tg_id"
            )
            specialization_data = await session.execute(
                specialization_query, {"tg_id": str(message.from_user.id)}
            )
            specialization_values = specialization_data.fetchone()

            has_specializations = False
            if specialization_values is not None:
                for column_name, value in zip(
                    specialization_data.keys(), specialization_values
                ):
                    if column_name.startswith("spec_") and value:
                        has_specializations = True
                        break

            if user_data or has_specializations:
                await message.answer(
                    "Хотите удалить старые данные?",
                    reply_markup=kb.clear_data_keyboard,
                )
            else:
                await message.answer(
                    "Старые данные не найдены.",
                    reply_markup=kb.change_data_keyboard,
                )
                await state.set_state(Form.change_data)


@router.message(Form.change_data)
async def process_change_data(message: Message, state: FSMContext):
    if message.text == "Город":
        await state.set_state(Form.city)
        await message.answer(
            "Введите ваш город:", reply_markup=kb.city_keyboard()
        )
    elif message.text == "Баллы ЕГЭ":
        await list_subjects(message)
        await state.set_state(Form.subject)
    elif message.text == "Специальность вуза":
        await send_specialization_keyboard(message)
        await state.set_state(Form.spec)
    elif message.text == "Вернуться в начало":
        await message.answer(
            "Вы вернулись в главное меню.", reply_markup=kb.main
        )
        await state.clear()


@router.message(Form.city)
async def process_city(message: types.Message, state: FSMContext):
    await state.update_data(city=message.text)
    async with SessionLocalUsers() as session:
        async with session.begin():
            user = (
                (
                    await session.execute(
                        select(User).filter_by(tg_id=str(message.from_user.id))
                    )
                )
                .scalars()
                .first()
            )
            if user:
                user.city = message.text
            else:
                user = User(tg_id=str(message.from_user.id), city=message.text)
                session.add(user)
            await session.commit()
    await state.set_state(Form.change_data)
    await message.answer(
        "Вы успешно сохранили свой город", reply_markup=kb.change_data_keyboard
    )


@router.callback_query(F.data and F.data.startswith("sub_"))
async def process_subject(
    callback_query: types.CallbackQuery, state: FSMContext
):
    subject = callback_query.data[len("sub_") :]
    await state.update_data(current_subject=subject)
    subjects_map = {
        "rus": "Русский",
        "math": "Математика",
        "math_prof": "Математика профильная",
        "phy": "Физика",
        "chem": "Химия",
        "hist": "История",
        "soc": "Обществознание",
        "inf": "Информатика",
        "bio": "Биология",
        "geo": "География",
        "eng": "Английский",
        "ger": "Немецкий",
        "fren": "Французский",
        "span": "Испанский",
        "chi": "Китайский",
        "lit": "Литература",
    }
    rus_subject = subjects_map.get(subject, "Неизвестный предмет")
    await state.update_data(rus_subject=rus_subject)
    await callback_query.message.answer(
        f"Введите баллы для предмета {rus_subject}:"
    )
    await callback_query.answer()


@router.message(Form.subject)
async def process_score(message: types.Message, state: FSMContext):

    try:
        score = int(message.text)
        if score <= 100:
            data = await state.get_data()
            async with SessionLocalUsers() as session:
                async with session.begin():
                    user = (
                        (
                            await session.execute(
                                select(Subject).filter_by(
                                    tg_id=str(message.from_user.id)
                                )
                            )
                        )
                        .scalars()
                        .first()
                    )
                    if not user:
                        user = Subject(tg_id=str(message.from_user.id))
                        session.add(user)
                    current_subject = data["current_subject"]
                    rus_subject = data["rus_subject"]
                    setattr(user, f"sub_{current_subject}", score)
                    await session.commit()
                    logging.info(
                        f"User {message.from_user.id} updated "
                        f"{current_subject} with score {score}"
                    )
                    await message.answer(
                        f"Баллы для предмета {rus_subject} сохранены.\n"
                        "Выберите следующий предмет."
                    )

            await list_subjects(message)
        else:
            await message.answer(
                "Пожалуйста, введите числовое значение, не превышающее 100."
            )
    except ValueError:
        await message.answer(
            "Пожалуйста, введите корректное числовое значение."
        )

    async with SessionLocalUsers() as session:
        async with session.begin():
            subject_data = (
                (
                    await session.execute(
                        select(Subject).filter_by(
                            tg_id=str(message.from_user.id)
                        )
                    )
                )
                .scalars()
                .first()
            )

            scores = [
                subject_data.sub_rus,
                subject_data.sub_math,
                subject_data.sub_math_prof,
                subject_data.sub_phy,
                subject_data.sub_chem,
                subject_data.sub_hist,
                subject_data.sub_soc,
                subject_data.sub_inf,
                subject_data.sub_bio,
                subject_data.sub_geo,
                subject_data.sub_eng,
                subject_data.sub_ger,
                subject_data.sub_fren,
                subject_data.sub_span,
                subject_data.sub_chi,
                subject_data.sub_lit,
            ]
            valid_scores = [score for score in scores if score is not None]
            mean_value = (
                (sum(valid_scores) / len(valid_scores)) * 3
                if valid_scores
                else None
            )

            subject_data.mean_value = mean_value
            session.add(subject_data)


async def list_subjects(message: types.Message):
    await message.reply(
        "Выберите предмет для ввода баллов:",
        reply_markup=kb.subjects_keyboard(),
    )


@router.message(F.text == "Да, удалить старые данные")
async def clear_old_data(message: Message, state: FSMContext):
    async with SessionLocalUsers() as session:
        async with session.begin():
            tg_id = str(message.from_user.id)

            result = await session.execute(
                text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name='specializations'"
                )
            )
            columns = result.scalars().all()

            spec_columns = [col for col in columns if col.startswith("spec_")]

            if spec_columns:
                set_clause = ", ".join(
                    [f"{col} = False" for col in spec_columns]
                )
                update_stmt = (
                    f"UPDATE specializations SET {set_clause} "
                    "WHERE tg_id = :tg_id"
                )

                await session.execute(text(update_stmt), {"tg_id": tg_id})

            await session.execute(
                delete(Subject).where(Subject.tg_id == tg_id)
            )
            await session.execute(delete(User).where(User.tg_id == tg_id))

            await session.commit()

    await state.set_state(Form.change_data)
    await message.answer(
        "Старые данные удалены. Что вы хотите изменить?",
        reply_markup=kb.change_data_keyboard,
    )


@router.message(F.text == "Нет, оставить старые данные")
async def keep_old_data(message: Message, state: FSMContext):
    await state.set_state(Form.change_data)
    await message.answer(
        "Старые данные сохранены. Что вы хотите изменить?",
        reply_markup=kb.change_data_keyboard,
    )


@router.callback_query(F.data == "save")
async def save_data(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.answer(
        "Данные успешно сохранены!", reply_markup=kb.change_data_keyboard
    )
    await state.set_state(Form.change_data)
    await callback_query.answer()


@router.message(F.text == "Просмотреть данные")
async def view_data(message: Message):
    async with SessionLocalUsers() as session:
        async with session.begin():
            user_data = (
                (
                    await session.execute(
                        select(User).filter_by(tg_id=str(message.from_user.id))
                    )
                )
                .scalars()
                .first()
            )

            subject_data = (
                (
                    await session.execute(
                        select(Subject).filter_by(
                            tg_id=str(message.from_user.id)
                        )
                    )
                )
                .scalars()
                .first()
            )

            result = await session.execute(
                text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name='specializations'"
                )
            )
            columns = result.scalars().all()

            specialization_columns = [
                col for col in columns if col.startswith("spec_")
            ]

            if specialization_columns:
                spec_query = (
                    f"SELECT {', '.join(specialization_columns)} "
                    "FROM specializations WHERE tg_id = :tg_id"
                )
                specialization_data = await session.execute(
                    text(spec_query),
                    {"tg_id": str(message.from_user.id)},
                )
                specialization_values = specialization_data.fetchone()
            else:
                specialization_values = None

            if specialization_values is not None:
                specializations = []
                for column in specialization_columns:
                    if column in specialization_mapping.values():
                        index = specialization_columns.index(column)
                        if (
                            index < len(specialization_values)
                            and specialization_values[index]
                        ):
                            specializations.append(
                                next(
                                    name
                                    for name, col in (
                                        specialization_mapping.items()
                                    )
                                    if col == column
                                )
                            )
            else:
                specializations = []

            city = user_data.city if user_data else None

            scores = {
                "Русский": subject_data.sub_rus if subject_data else None,
                "Математика": subject_data.sub_math if subject_data else None,
                "Математика профильная": (
                    subject_data.sub_math_prof if subject_data else None
                ),
                "Физика": subject_data.sub_phy if subject_data else None,
                "Химия": subject_data.sub_chem if subject_data else None,
                "История": subject_data.sub_hist if subject_data else None,
                "Обществознание": (
                    subject_data.sub_soc if subject_data else None
                ),
                "Информатика": subject_data.sub_inf if subject_data else None,
                "Биология": subject_data.sub_bio if subject_data else None,
                "География": subject_data.sub_geo if subject_data else None,
                "Английский": subject_data.sub_eng if subject_data else None,
                "Немецкий": subject_data.sub_ger if subject_data else None,
                "Французский": (
                    subject_data.sub_fren if subject_data else None
                ),
                "Испанский": subject_data.sub_span if subject_data else None,
                "Китайский": subject_data.sub_chi if subject_data else None,
                "Литература": subject_data.sub_lit if subject_data else None,
            }

            mean_value = subject_data.mean_value if subject_data else None

            city_message = (
                f"Выбранный город: {city}"
                if city
                else "Выбранный город: не выбран"
            )

            scores_message = "\n".join(
                [
                    f"{subject}: {score}"
                    for subject, score in scores.items()
                    if score is not None
                ]
            )
            scores_message = (
                "Баллы ЕГЭ:\n" + scores_message
                if scores_message
                else "Баллы ЕГЭ: не указаны"
            )

            mean_value_message = (
                f"Ваш средний балл: {mean_value:.2f}"
                if mean_value is not None
                else "Ваш средний балл: не указан"
            )

            spec_message = (
                ", ".join(specializations)
                if specializations
                else "Специализации: не выбраны"
            )
            spec_message = (
                "Выбранные специализации: " + spec_message
                if specializations
                else spec_message
            )

            if (
                city is None
                and not any(scores.values())
                and not specializations
                and mean_value is None
            ):
                await message.answer("Данные не найдены.")
            else:
                await message.answer(
                    f"{city_message}\n{scores_message}\n"
                    f"{mean_value_message}\n{spec_message}",
                    reply_markup=kb.get_clear_data_keyboard(),
                )


@router.callback_query(F.data == "clear_data")
async def inline_clear_data(
    callback_query: types.CallbackQuery, state: FSMContext
):
    async with SessionLocalUsers() as session:
        async with session.begin():
            tg_id = str(callback_query.from_user.id)

            result = await session.execute(
                text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name='specializations'"
                )
            )
            columns = result.scalars().all()

            spec_columns = [col for col in columns if col.startswith("spec_")]

            if spec_columns:
                set_clause = ", ".join(
                    [f"{col} = False" for col in spec_columns]
                )
                update_stmt = (
                    f"UPDATE specializations SET {set_clause} "
                    "WHERE tg_id = :tg_id"
                )

                await session.execute(text(update_stmt), {"tg_id": tg_id})

            await session.execute(
                delete(Subject).where(Subject.tg_id == tg_id)
            )
            await session.execute(delete(User).where(User.tg_id == tg_id))

            await session.commit()

    logging.info(
        f"User {callback_query.from_user.id} data cleared from database"
    )
    await state.clear()
    await callback_query.message.answer(
        "Данные успешно удалены.", reply_markup=kb.main
    )
    await callback_query.answer()


@router.callback_query(F.data == "keep_data")
async def inline_keep_data(
    callback_query: types.CallbackQuery, state: FSMContext
):
    await callback_query.message.answer(
        "Данные сохранены.", reply_markup=kb.main
    )
    await callback_query.answer()


async def send_specialization_keyboard(message: Message):
    buttons = [
        InlineKeyboardButton(text=name, callback_data=key)
        for name, key in specialization_mapping.items()
    ]
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[buttons[i : i + 2] for i in range(0, len(buttons), 2)]
    )
    await message.answer("Выберите специальность:", reply_markup=keyboard)


@router.callback_query(lambda c: c.data in specialization_mapping.values())
async def process_specialization(
    callback_query: types.CallbackQuery, state: FSMContext
):
    specialization = callback_query.data
    user_id = str(callback_query.from_user.id)

    logging.info(
        f"Пользователь {user_id} выбрал специальность: {specialization}"
    )

    async with SessionLocalUsers() as session:
        async with session.begin():
            user_spec = (
                (
                    await session.execute(
                        select(Specialization).filter_by(tg_id=user_id)
                    )
                )
                .scalars()
                .first()
            )

            if not user_spec:
                logging.info(
                    f"Создание новой специализации для пользователя {user_id}"
                )
                user_spec = Specialization(tg_id=user_id)
                result = await session.execute(
                    text(
                        "SELECT column_name FROM information_schema.columns "
                        "WHERE table_name = 'specializations'"
                    )
                )
                existing_columns = [
                    row[0]
                    for row in result.fetchall()
                    if row[0].startswith("spec_")
                ]

                for column in existing_columns:
                    setattr(user_spec, column, False)

                session.add(user_spec)
                await session.commit()

    async with SessionLocalUsers() as session:
        async with session.begin():
            result = await session.execute(
                text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name = 'specializations'"
                )
            )
            existing_columns = [row[0] for row in result.fetchall()]

            logging.info(
                f"Доступные столбцы в таблице specializations: {existing_columns}"
            )

            if specialization in existing_columns:
                new_value = True
                logging.info(
                    f"Запуск обновления для столбца {specialization} с "
                    f"значением {new_value}"
                )

                query = text(
                    f"UPDATE specializations SET {specialization} = :value "
                    "WHERE tg_id = :tg_id"
                )
                await session.execute(
                    query, {"value": new_value, "tg_id": user_id}
                )

                updated_value_query = await session.execute(
                    text(
                        f"SELECT {specialization} FROM specializations "
                        "WHERE tg_id = :tg_id"
                    ),
                    {"tg_id": user_id},
                )
                updated_value = updated_value_query.scalar()

                logging.info(
                    f"Текущее значение для столбца {specialization} после изменения: "
                    f"{updated_value}."
                )
            else:
                logging.error(
                    f"Столбец {specialization} не существует в таблице "
                    "specializations."
                )

        await session.commit()

    await callback_query.message.answer(
        "Специальность успешно сохранена!",
        reply_markup=kb.change_data_keyboard,
    )
    await callback_query.answer()


@router.message(F.text == "Вернуться в начало")
async def back_to_main_menu(message: Message, state: FSMContext):
    await message.answer("Вы вернулись в главное меню.", reply_markup=kb.main)
    await state.clear()


@router.message(F.text == "Начать поиск")
async def start_search(message: Message, state: FSMContext):
    await message.answer(
        "На какие места вы рассчитываете?",
        reply_markup=kb.generate_budget_keyboard(),
    )
    await state.set_state("waiting_for_budget_choice")


@router.message(F.text == "Бюджет")
async def search_budget(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state != "waiting_for_budget_choice":
        return

    tg_id = str(message.from_user.id)

    async with SessionLocalUsers() as session:
        async with session.begin():
            user_data = await session.execute(
                select(Subject).filter_by(tg_id=tg_id)
            )
            user_subject = user_data.scalars().first()

            if user_subject is None or user_subject.mean_value is None:
                await message.answer(
                    "У вас нет данных о средних баллах. "
                    "Пожалуйста, введите данные.",
                    reply_markup=kb.main,
                )
                return

            mean_value = user_subject.mean_value

    async with SessionLocalUniversity() as session:
        async with session.begin():
            universities = await session.execute(text("SELECT * FROM moscow"))
            universities = universities.fetchall()

            matching_universities = []
            for university in universities:
                bud_score = university.bud_score
                if bud_score and not bud_score.startswith("от ?"):

                    parts = bud_score.split(" ")
                    if len(parts) > 1 and parts[1] != "-":
                        try:
                            bud_score_value = float(parts[1])
                            if mean_value >= bud_score_value:
                                matching_universities.append(university)
                        except ValueError:

                            continue

            if not matching_universities:
                await message.answer(
                    "Не найдено вузов, соответствующих вашим средним баллам "
                    "для бюджета."
                )
                return

            await state.update_data(
                matching_universities=matching_universities
            )
            await show_university_list(message, matching_universities)


@router.message(F.text == "Платное")
async def search_paid(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state != "waiting_for_budget_choice":
        return

    tg_id = str(message.from_user.id)

    async with SessionLocalUsers() as session:
        async with session.begin():
            user_data = await session.execute(
                select(Subject).filter_by(tg_id=tg_id)
            )
            user_subject = user_data.scalars().first()

            if user_subject is None or user_subject.mean_value is None:
                await message.answer(
                    "У вас нет данных о средних баллах. "
                    "Пожалуйста, введите данные.",
                    reply_markup=kb.main,
                )
                return

            mean_value = user_subject.mean_value

    async with SessionLocalUniversity() as session:
        async with session.begin():
            universities = await session.execute(text("SELECT * FROM moscow"))
            universities = universities.fetchall()

            matching_universities = []
            for university in universities:
                pay_score = university.pay_score
                if pay_score and not pay_score.startswith("от ?"):

                    parts = pay_score.split(" ")
                    if len(parts) > 1 and parts[1] != "-":
                        try:
                            pay_score_value = float(parts[1])
                            if mean_value >= pay_score_value:
                                matching_universities.append(university)
                        except ValueError:
                            continue

            if not matching_universities:
                await message.answer(
                    "Не найдено вузов, соответствующих вашим средним баллам "
                    "для платного.",
                    reply_markup=kb.main,
                )
                await state.clear()
                return

            await state.update_data(
                matching_universities=matching_universities
            )
            await show_university_list(message, matching_universities)


async def show_university_list(message: Message, matching_universities):
    university_list = "\n".join(
        f"{i + 1}. {university.name}"
        for i, university in enumerate(matching_universities[:5])
    )
    await message.answer(
        f"Подходящие университеты:\n{university_list}",
        reply_markup=generate_university_buttons(matching_universities, 0),
    )


def generate_university_buttons(universities, page):
    buttons = []
    start_index = page * 5
    end_index = start_index + 5

    for i, university in enumerate(universities[start_index:end_index]):
        buttons.append(
            [
                InlineKeyboardButton(
                    text=str(i + 1),
                    callback_data=f"university_{university.ID}",
                )
            ]
        )

    navigation_buttons = []
    if page > 0:
        navigation_buttons.append(
            InlineKeyboardButton(
                text="Назад", callback_data=f"page_{page - 1}"
            )
        )
    if end_index < len(universities):
        navigation_buttons.append(
            InlineKeyboardButton(
                text="Вперед", callback_data=f"page_{page + 1}"
            )
        )

    if navigation_buttons:
        buttons.append(navigation_buttons)

    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.callback_query(F.data.startswith("page_"))
async def navigate_pages(callback: types.CallbackQuery, state: FSMContext):
    page_number = int(callback.data.split("_")[1])
    data = await state.get_data()
    matching_universities = data.get("matching_universities", [])

    if not matching_universities:
        await callback.answer("Нет доступных университетов.")
        return

    university_list = "\n".join(
        f"{i + 1}. {university.name}"
        for i, university in enumerate(
            matching_universities[page_number * 5 : (page_number + 1) * 5]
        )
    )

    await callback.message.edit_text(
        f"Выберите нужный вам ВУЗ:\n{university_list}",
        reply_markup=generate_university_buttons(
            matching_universities, page_number
        ),
    )

    await callback.answer()


@router.callback_query(F.data.startswith("university_"))
async def select_university(callback: types.CallbackQuery, state: FSMContext):
    university_id = int(callback.data.split("_")[1])
    async with SessionLocalUniversity() as session:
        async with session.begin():
            result = await session.execute(
                text("SELECT * FROM moscow WHERE ID = :id"),
                {"id": university_id},
            )
            university = result.mappings().fetchone()

            if university:
                logger.info(
                    "Полученные значения из базы данных: %s", university
                )

                specialization_columns = [
                    column
                    for column in result.keys()
                    if column.startswith("spec_")
                ]

                all_specialties = []
                logger.info(
                    "Проверка специализаций для университета: %s",
                    university["name"],
                )

                for spec in specialization_columns:
                    spec_value = university[spec]
                    logger.info(
                        "Специализация: %s, Значение: %s", spec, spec_value
                    )

                    if spec_value:
                        for (
                            russian_name,
                            db_column,
                        ) in specialization_mapping.items():
                            if db_column == spec:
                                all_specialties.append(russian_name)

                required_budget_score = (
                    f"Необходимое количество баллов ЕГЭ для бюджета: "
                    f"{university['bud_score']}\n"
                )

                required_paid_score = (
                    f"Необходимое количество баллов ЕГЭ для платного: "
                    f"{university['pay_score']}\n"
                )
                specialties_text = (
                    ", ".join(all_specialties)
                    if all_specialties
                    else "Нет доступных специальностей"
                )

                specialties_message = (
                    f"Все специальности: {specialties_text}\n"
                )

                response_message = (
                    f"Название: {university['name']}\n"
                    f"Количество бюджетных мест: {university['bud_places']}\n"
                    f"Количество платных мест: {university['pay_places']}\n"
                    + required_budget_score
                    + required_paid_score
                    + specialties_message
                    + f"Ссылка: {university['url']}"
                )

                await callback.message.answer(
                    response_message, reply_markup=kb.main
                )
            else:
                await callback.message.answer("Университет не найден.")
    await callback.answer()
