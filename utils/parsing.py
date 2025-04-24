import os
import re
import time

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from sqlalchemy import Column, create_engine, inspect, Integer, String, text
from sqlalchemy.orm import declarative_base, sessionmaker


load_dotenv()
DATABASE_URI = os.getenv("UNIV_SQL_URL")
engine = create_engine(DATABASE_URI, echo=True)
Base = declarative_base()


class Moscow(Base):
    __tablename__ = "moscow"

    ID = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    coast = Column(String(255), nullable=True)
    bud_places = Column(String(255), nullable=True)
    pay_places = Column(String(255), nullable=True)
    bud_score = Column(String(255), nullable=True)
    pay_score = Column(String(255), nullable=True)
    url = Column(String(255), nullable=True)


driver_path = os.getenv("DRIVER_PATH")
service = Service(driver_path)
driver = webdriver.Edge(service=service)


def add_column_if_not_exists(table_name, column_name):

    inspector = inspect(engine)
    if column_name not in [
        col["name"] for col in inspector.get_columns(table_name)
    ]:
        with engine.connect() as connection:
            connection.execute(
                text(
                    f"ALTER TABLE `{table_name}` ADD COLUMN `{column_name}` BOOLEAN DEFAULT FALSE"
                )
            )


#### Создание новой таблицы
# Base = Base
# Base.metadata.drop_all(engine)
# Base.metadata.create_all(engine)


SessionUniversity2 = sessionmaker(bind=engine)
session = SessionUniversity2()


try:

    for page in range(1, 17):

        url = f"https://vuzopedia.ru/region/city/59?page={page}"
        driver.get(url)

        university_titles = driver.find_elements(By.CLASS_NAME, "itemVuzTitle")
        print(university_titles)

        add_info = driver.find_elements(By.CLASS_NAME, "col-md-2.optionVuzNew")

        print(f"Страница {page}:")

        for i in range(len(university_titles)):
            title_element = university_titles[i]
            title = title_element.text.strip()

            try:
                link_element = title_element.find_element(By.XPATH, "..")
                url = link_element.get_attribute("href")
            except Exception as e:
                print(f"Не удалось найти ссылку для вуза '{title}': {e}")
                url = "нет данных"

            if i < len(add_info):
                fee_info = add_info[i].text.strip()
                coast = None
                bud_places = None
                bud_score = None
                pay_places = None
                pay_score = None

                info_lines = fee_info.splitlines()

                in_budget_section = False

                for line in info_lines:
                    line = line.strip()
                    print(line)

                    if line.endswith("₽"):
                        coast = line

                    if "Бюджет" in line:
                        in_budget_section = True

                    if in_budget_section:
                        if "Платное" in line:
                            in_budget_section = False

                        if line.endswith("мест"):
                            bud_places = line

                        if line.startswith("от"):
                            bud_score = line

                    else:
                        if line.endswith("мест"):
                            pay_places = line

                        if line.startswith("от"):
                            pay_score = line

                print(f"Название вуза: {title}")
                print(f"URL вуза: {url}")
                if coast:
                    print(f"Стоимость обучения: {coast}")
                else:
                    print("Стоимость обучения: нет данных")

                if bud_places:
                    print(f"Бюджетные места: {bud_places}")
                else:
                    print("Бюджетные места: нет данных")

                if bud_score:
                    print(
                        f"Бюджетные места (количество баллов егэ): {bud_score}"
                    )
                else:
                    print(
                        "Бюджетные места (количество баллов егэ): нет данных"
                    )

                if pay_places:
                    print(f"Платные места: {pay_places}")
                else:
                    print("Платные места: нет данных")

                if pay_score:
                    print(
                        f"Платные места (количество баллов егэ): {pay_score}"
                    )
                else:
                    print("Платные места (количество баллов егэ): нет данных")

                print("-" * 40)

                new_university = Moscow(
                    name=title,
                    coast=coast,
                    bud_places=bud_places,
                    pay_places=pay_places,
                    bud_score=bud_score,
                    pay_score=pay_score,
                    url=url,
                )
                session.add(new_university)

            else:
                print(f"Название вуза: {title}, Информация: нет данных")

    for i in range(24):
        url = "https://vuzopedia.ru/city/moskva"
        driver.get(url)

        cur_category_title = driver.find_elements(
            By.CLASS_NAME, "vuzItemTitle"
        )[i].text.strip()
        print(cur_category_title)

        cur_category_count = driver.find_elements(
            By.CLASS_NAME, "cyrCountVUz"
        )[i].text.strip()
        cur_category_count = re.findall(r"\d+", cur_category_count)
        if cur_category_count:
            cur_category_count = int(cur_category_count[0])
        else:
            cur_category_count = 0

        print(cur_category_count)

        title_element = driver.find_elements(By.CLASS_NAME, "teloVuzItemMain")
        link_element = title_element[i].find_element(By.XPATH, "..")
        cur_url = link_element.get_attribute("href")
        print(cur_url)

        category_name = cur_url.split("s=")[-1]
        print(f"Category name for DB: {category_name}")

        column_name = f"spec_{category_name}"
        add_column_if_not_exists("moscow", column_name)

        vuz_per_page = 10
        total_pages = (cur_category_count // vuz_per_page) + (
            1 if cur_category_count % vuz_per_page > 0 else 0
        )

        for page in range(1, total_pages + 1):
            page_url = f"{cur_url}&page={page}"
            driver.get(page_url)

            time.sleep(2)

            vuz_titles = driver.find_elements(By.CLASS_NAME, "itemVuzTitle")
            for title in vuz_titles:
                vuz_name = title.text.strip()
                print(vuz_name)

                session.execute(
                    text(
                        f"UPDATE moscow SET {column_name} = :value WHERE name = :name"
                    ),
                    {"value": True, "name": vuz_name},
                )

        session.commit()

finally:
    session.commit()
    driver.quit()
