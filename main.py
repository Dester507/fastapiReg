# from os import environ
from dotenv import load_dotenv
from pathlib import Path

from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import select
import jwt

from models import Base, UserInDB, Salt
from hash_password import hash_password, check_password_hash

app = FastAPI(title='User Register Test API')

load_dotenv(dotenv_path=Path('.env'))

USER = 'iakuacmxmnxawl'  # environ.get('USER')
PASSWORD = 'f36ffdd60bcbac1b42d18d652dc465dbda47859d46fc9893db8229b1cdae67dd'  # environ.get('PASSWORD')
HOST = 'ec2-54-75-229-28.eu-west-1.compute.amazonaws.com'  # environ.get('HOST')
PORT = '5432'  # environ.get('PORT')
DATABASE = 'd1p21lku7v294h'  # environ.get('DATABASE')
SECRET_KEY = 'dester123456789dester'  # environ.get('SECRET_KEY')
ALGORITHM = 'HS256'  # environ.get('ALGORITHM')


class UserReg(BaseModel):
    username: str
    password: str


class UserValidation(BaseModel):
    username: str


async def async_return_engine():
    engine = create_async_engine(f"postgresql+asyncpg://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}?ssl=require")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return engine


@app.post('/reg')
async def user_register(user: UserReg, engine: AsyncEngine = Depends(async_return_engine)):
    try:
        async with AsyncSession(engine) as session:
            async with session.begin():
                storage = hash_password(user.password)
                session.add(UserInDB(user.username, storage[0]))
                session.add(Salt(user.username, storage[1]))
            await session.commit()
        return {'result': 'user has been registered'}
    except IntegrityError:
        raise HTTPException(status_code=409,
                            detail="User with this username already exist.")


async def login_user(username, password):
    engine = await async_return_engine()
    async with AsyncSession(engine) as session:
        stmt = select(UserInDB).where(UserInDB.username == username)
        result_user = await session.execute(stmt)
        if result_user.first():
            stmt = select(Salt).where(Salt.user == username)
            result_salt = await session.execute(stmt)
            hash_new_password = check_password_hash(password, result_salt.first().salt)
            if hash_new_password != result_user.first().password:
                return False
        else:
            return False
    return True


def create_token(*, data: dict):
    to_encode = data.copy()
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def decode_token(token):
    error_detail = HTTPException(
        status_code=401,
        detail="Bad data",
        headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("user")
        if username is None:
            raise error_detail
        valid_user = UserValidation(username=username)
    except jwt.PyJWTError:
        raise error_detail
    engine = await async_return_engine()
    async with AsyncSession(engine) as session:
        stmt = select(UserInDB).where(UserInDB.username == valid_user.username)
        result = await session.execute(stmt)
        if result.first() is None:
            raise error_detail
        return result.first()
