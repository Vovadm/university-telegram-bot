from os import getenv
from time import sleep

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

from db.universiries import Moscow

load_dotenv()

DATABASE_URI = getenv("DB_URL")
engine = create_engine(DATABASE_URI, echo=True)
Base = declarative_base()


# ! Создание новой таблицы
# Base.metadata.drop_all(engine)
# Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()



driver_path = getenv("DRIVER_PATH")
service = Service(driver_path)
driver = webdriver.Edge(service=service)

try:
    print("1")

    # ! город/бюджетные места/платные места/названия/URL
    driver.get("https://vuzopedia.com/moskva/")

    for i in range(1, 175):

        name_xpath = f"/html/body/div/section/article/div[3]/article[{i}]/a/h3"

        budget_xpath = f"/html/body/div/section/article/div[3]/article[{i}]/a/div[2]/div[1]/span"

        pay_xpath = f"/html/body/div/section/article/div[3]/article[{i}]/a/div[2]/div[2]/span"

        name_element = WebDriverWait(driver, 10).until(
            ec.presence_of_element_located((By.XPATH, name_xpath))
        )

        budget_element = WebDriverWait(driver, 10).until(
            ec.presence_of_element_located((By.XPATH, budget_xpath))
        )

        pay_element = WebDriverWait(driver, 10).until(
            ec.presence_of_element_located((By.XPATH, pay_xpath))
        )

        university_name = name_element.text.strip()

        budget_count = budget_element.text.strip()

        pay_count = pay_element.text.strip()

        if budget_count == "":
            budget_count = None
        elif budget_count is not None and budget_count.lower() == "нет":
            budget_count = 0
        else:
            budget_count = int(budget_count)

        if pay_count == "":
            pay_count = None
        elif pay_count is not None and pay_count.lower() == "нет":
            pay_count = 0
        else:
            pay_count = int(pay_count)

        link_element = name_element.find_element(By.XPATH, "..")
        url = link_element.get_attribute("href")

        new_entry = Moscow(
            name=university_name,
            budget_count=budget_count,
            url=url,
            pay_count=pay_count,
        )
        session.add(new_entry)

    session.commit()

    # ! информация конкретно по вузу
    records = session.query(Moscow).all()

    for record in records:
        url = record.url

        driver.get(url)

        additional_data_xpath = (
            "/html/body/div[1]/article/div[3]/div[1]/div[2]/span"
        )

        try:
            additional_data_element = WebDriverWait(driver, 10).until(
                ec.presence_of_element_located(
                    (By.XPATH, additional_data_xpath)
                )
            )

            additional_data = additional_data_element.text.strip()

            record.def_conscription = additional_data

            print(
                f"Дополнительные данные для {record.name}: {additional_data}"
            )

        except Exception as e:
            print(f"Произошла ошибка: {e}")
            session.rollback()

    # ! рейтинг вузов

    driver.get("https://vuzopedia.com/rating-top-100/")

    for i in range(1, 101):

        rating_name_xpath_1 = f"/html/body/div[1]/section/div/div[1]/div[{i}]/article/div[2]/a/h2"

        rating_name_xpath_2 = (
            f"/html/body/div[1]/section/div/div[1]/div[{i}]/article/div[2]/h2"
        )

        rating_value_xpath_1 = (
            f"/html/body/div/section/div/div[1]/div[{i}]/article/span"
        )

        rating_value_xpath_2 = (
            f"/html/body/div[1]/section/div/div[1]/div[{i}]/article/span"
        )

        university_name = None
        rating_value = None

        try:
            name_element = WebDriverWait(driver, 1).until(
                ec.presence_of_element_located((By.XPATH, rating_name_xpath_1))
            )
            university_name = name_element.text.strip()
        except Exception:
            try:
                name_element = WebDriverWait(driver, 1).until(
                    ec.presence_of_element_located(
                        (By.XPATH, rating_name_xpath_2)
                    )
                )
                university_name = name_element.text.strip()
            except Exception as e:
                print(
                    f"Не удалось получить название университета для индекса {i}: {e}"
                )

        if university_name:
            try:
                rating_element = WebDriverWait(driver, 1).until(
                    ec.presence_of_element_located(
                        (By.XPATH, rating_value_xpath_1)
                    )
                )
                rating_value = int(rating_element.text.strip())
            except Exception:
                try:
                    rating_element = WebDriverWait(driver, 1).until(
                        ec.presence_of_element_located(
                            (By.XPATH, rating_value_xpath_2)
                        )
                    )
                    rating_value = int(rating_element.text.strip())
                except Exception as e:
                    print(
                        f"Не удалось получить рейтинг для {university_name}: {e}"
                    )

            if university_name and rating_value is not None:
                record = (
                    session.query(Moscow)
                    .filter(Moscow.name == university_name)
                    .first()
                )
                if record:

                    record.rating = rating_value
                    print(
                        f"Обновлен рейтинг для {university_name}: {rating_value}"
                    )

    session.commit()

    # ! получение специализаций
    specializations = [
        "https://vuzopedia.com/voennye/",
        "https://vuzopedia.com/gumanitarnye/",
        "https://vuzopedia.com/meditsinskie/",
        "https://vuzopedia.com/pedagogicheskie/",
        "https://vuzopedia.com/pravoohranitelnye/",
        "https://vuzopedia.com/teatralnye/",
        "https://vuzopedia.com/tekhnicheskie/",
        "https://vuzopedia.com/ekonomicheskie/",
        "https://vuzopedia.com/yuridicheskie/",
    ]

    specialization_mapping = {
        "voennye": "spec_mil",
        "gumanitarnye": "spec_hum",
        "meditsinskie": "spec_med",
        "pedagogicheskie": "spec_ped",
        "pravoohranitelnye": "spec_enf",
        "teatralnye": "spec_the",
        "tekhnicheskie": "spec_tec",
        "ekonomicheskie": "spec_eco",
        "yuridicheskie": "spec_leg",
    }

    specialization_number = {
        "voennye": 7,
        "gumanitarnye": 14,
        "meditsinskie": 5,
        "pedagogicheskie": 17,
        "pravoohranitelnye": 6,
        "teatralnye": 8,
        "tekhnicheskie": 21,
        "ekonomicheskie": 21,
        "yuridicheskie": 14,
    }

    for url in specializations:

        specialization_name = url.split("/")[-2]
        column_name = specialization_mapping.get(specialization_name)

        if column_name:
            try:

                driver.get(url)

                num_universities = specialization_number[specialization_name]

                for i in range(1, num_universities + 1):

                    xpath = f"/html/body/div[1]/article/div[3]/article[{i}]/a/div[2]/h3"
                    name_element = WebDriverWait(driver, 100).until(
                        ec.presence_of_element_located((By.XPATH, xpath))
                    )
                    university_name = name_element.text.strip()

                    record = (
                        session.query(Moscow)
                        .filter(Moscow.name == university_name)
                        .first()
                    )
                    if record:
                        setattr(record, column_name, True)
                        print(
                            f"Категория {column_name} установлена для {university_name}"
                        )

                sleep(10)

            except Exception as e:
                print(f"Ошибка при обработке URL {url}: {e}")

    session.commit()

    driver.get("https://vuzopedia.com/moskva/")

    for i in range(1, 175):
        try:

            xpath = f"/html/body/div[1]/section/article/div[3]/article[{i}]/div/span"
            score_element = WebDriverWait(driver, 10).until(
                ec.presence_of_element_located((By.XPATH, xpath))
            )
            avg_score = score_element.text.strip()

            record = session.query(Moscow).filter(Moscow.ID == i).first()
            if record:

                record.avg_score = avg_score
                print(f"Заполнен avg_score для записи с ID {i}: {avg_score}")

        except Exception as e:
            print(f"Не удалось получить avg_score для индекса {i}: {e}")
            continue


finally:
    session.commit()
    session.close()
    driver.quit()
