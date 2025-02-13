import os

from dotenv import load_dotenv
from sqlalchemy import Column, Integer, String, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


load_dotenv()
DATABASE_URI = os.getenv("UNIV_SQL_URL")
engine = create_async_engine(DATABASE_URI, echo=True)
SessionLocalUniversity = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)
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


async def get_specialization_mapping(session: AsyncSession):
    query = (
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = 'moscow'"
    )

    result = await session.execute(text(query))

    specialization_mapping = {}
    for row in result.fetchall():
        column_name = row[0]
        if column_name.startswith("spec_"):
            specialization_key = column_name[5:]
            specialization_mapping[specialization_key] = column_name

    return specialization_mapping


# Создание новой таблицы
# Base.metadata.drop_all(engine)
# Base.metadata.create_all(engine)
