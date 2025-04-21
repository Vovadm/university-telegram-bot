import asyncio
import logging
import os


from dotenv import load_dotenv
from sqlalchemy import BigInteger, inspect, String, text
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    AsyncAttrs,
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


load_dotenv()


logging.basicConfig(level=logging.INFO)


engine_users = create_async_engine(os.getenv("USER_SQL_URL"), echo=True)
engine_univs = create_async_engine(os.getenv("UNIV_SQL_URL"), echo=True)


SessionLocalUsers = async_sessionmaker(
    engine_users, class_=AsyncSession, expire_on_commit=False
)
SessionLocalUnivs = async_sessionmaker(
    engine_univs, class_=AsyncSession, expire_on_commit=False
)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id = mapped_column(BigInteger)
    city: Mapped[str] = mapped_column(String(25), nullable=True)


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id = mapped_column(BigInteger)
    sub_rus: Mapped[int] = mapped_column(nullable=True)
    sub_math: Mapped[int] = mapped_column(nullable=True)
    sub_math_prof: Mapped[int] = mapped_column(nullable=True)
    sub_phy: Mapped[int] = mapped_column(nullable=True)
    sub_chem: Mapped[int] = mapped_column(nullable=True)
    sub_hist: Mapped[int] = mapped_column(nullable=True)
    sub_soc: Mapped[int] = mapped_column(nullable=True)
    sub_inf: Mapped[int] = mapped_column(nullable=True)
    sub_bio: Mapped[int] = mapped_column(nullable=True)
    sub_geo: Mapped[int] = mapped_column(nullable=True)
    sub_eng: Mapped[int] = mapped_column(nullable=True)
    sub_ger: Mapped[int] = mapped_column(nullable=True)
    sub_fren: Mapped[int] = mapped_column(nullable=True)
    sub_span: Mapped[int] = mapped_column(nullable=True)
    sub_chi: Mapped[int] = mapped_column(nullable=True)
    sub_lit: Mapped[int] = mapped_column(nullable=True)
    mean_value: Mapped[float] = mapped_column(nullable=True)


class Specialization(Base):
    __tablename__ = "specializations"

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id = mapped_column(BigInteger)


async def create_tables():
    async with engine_users.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    async with engine_users.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def recreate_specializations_table():
    async with engine_users.begin() as conn:
        await conn.run_sync(
            Base.metadata.drop_all, tables=[Specialization.__table__]
        )
        await conn.run_sync(
            Base.metadata.create_all, tables=[Specialization.__table__]
        )
        logging.info("Recreated the specializations table.")


async def add_column_if_not_exists(table_name, column_name):
    async with engine_users.connect() as connection:
        existing_columns = await connection.run_sync(
            lambda sync_conn: [
                col["name"]
                for col in inspect(sync_conn).get_columns(table_name)
            ]
        )

        if column_name not in existing_columns:
            alter_query = (
                f"ALTER TABLE {table_name} ADD COLUMN {column_name} "
                "BOOLEAN DEFAULT 0"
            )
            await connection.execute(text(alter_query))

            logging.info(
                f"Added column {column_name} to table {table_name} "
                "with default value False (0)."
            )


async def get_specialization_columns_univs(session: AsyncSession):
    query = (
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = 'moscow'"
    )
    result = await session.execute(text(query))

    specialization_columns = [
        row[0] for row in result.fetchall() if row[0].startswith("spec_")
    ]
    return specialization_columns


async def sync_specializations():
    async with SessionLocalUnivs() as session_univs:
        specialization_columns = await get_specialization_columns_univs(
            session_univs
        )
        async with SessionLocalUsers():
            for column_name in specialization_columns:
                await add_column_if_not_exists("specializations", column_name)


async def async_main():
    try:
        async with engine_users.begin():
            await recreate_specializations_table()
            await sync_specializations()
    except Exception as e:
        logging.error(e)


if __name__ == "__main__":
    try:
        asyncio.run(async_main())
    except Exception as e:
        logging.error(f"Failed to run the main async function: {e}")
    finally:
        if asyncio.get_event_loop().is_running():
            asyncio.get_event_loop().close()
