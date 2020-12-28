from os import environ
from dotenv import load_dotenv

from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
import jwt

from models import Base, UserInDB

app = FastAPI(title='User Register Test API')

load_dotenv()

USER = environ.get('USER')
PASSWORD = environ.get('PASSWORD')
HOST = environ.get('HOST')
PORT = environ.get('PORT')
DATABASE = environ.get('DATABASE')


class UserBase(BaseModel):
    username: str
    password: str


async def async_return_engine():
    engine = create_async_engine(f"postgresql+asyncpg://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}?ssl=require")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return [engine]


@app.post("/add")
async def add_user(user: UserBase, engine: list = Depends(async_return_engine)):
    try:
        async with AsyncSession(engine[0]) as session:
            async with session.begin():
                session.add(UserInDB(user.username, user.password))
            await session.commit()
        return {"result": "good"}
    except:
        return {"result": "bad"}
