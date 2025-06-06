# 🤖 Телеграм-бот по подбору университета, с учетом критериев пользователя

Мой проект помогает абитуриентам помочь с выбором университат (ВУЗа)

## 📕 Сопроводительная документация

<https://1drv.ms/w/c/48554c1ce0299cea/ETddkHrKrkdHp7f_BbonDLoBbS5PR_mh0Mx3BviylLVyTA?e=TLV85G>

## 🚀 Возможности

- ✅ сохрание данных о баллах ЕГЭ по выбранным предметам

- 📄 пользователь может выбирать специальности ВУЗа, на которые он хотел бы поступить

- 🧠 база о 200+ ВУЗов горрода Москвы

## 📦 Установка

1.Клонируй репозиторий:

```bash
git clone https://github.com/Vovadm/university-telegram-bot.git
cd university-telegram-bot
```

2.Создай и активируй виртуальное окружение:

```bash
python -m venv venv
source venv/bin/activate  # Для Linux/macOS
venv\Scripts\activate     # Для Windows
```

3.Установи зависимости

```bash
pip install -r requirements.txt
```

4.Замените данные в файле EXAMPLE.env на ваши:

```bash
TOKEN=<TOKEN>
USER_SQL_URL=<'USER_DB_URL'>
UNIV_SQL_URL=<'UNIV_DB_URL'>
DRIVER_PATH=<r'DRIVER_PATH'>
```

## 🏃 Запуск бота

```bash
python main.py
```

## 🏃 Запуск парсинга

```bash
cd utils
python parsing.py
```

## 💻 Программный-код

- [`main.py`](/src/main.py) - запуск проекта

- [`handlers.py`](/src/app/handlers.py) - обработка событий

- [`parsing.py`](/src/utils/parsing.py) - парсинг данных с сайта

- [`keyboards.py`](/src/app/keyboards.py) - создание клавиатур

- [`universities.py`](/src/db/universities.py) - работа с базами данных университетом

- [`users.py`](/src/db/users.py) - работа с базами данных пользователей
