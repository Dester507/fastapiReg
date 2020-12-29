# from os import environ
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime, timedelta

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
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


class Token(BaseModel):
    access_token: str
    token_type: str


class DependsGroup:
    def __init__(self, groups: list):
        self.groups = groups

    async def __call__(self):
        group = await decode_token(token = oauth2_scheme, group=True)
        if group not in self.groups:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="You don`t have permissions")


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
group_routes = {'admin-panel': DependsGroup(['admin', 'dev', 'owner'])}


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
        user = result_user.scalar_one()
        if user:
            stmt = select(Salt).where(Salt.user == username)
            result_salt = await session.execute(stmt)
            user_salt = result_salt.scalar_one()
            hash_new_password = check_password_hash(password, user_salt.salt)
            if hash_new_password != user.password:
                return False
        else:
            return False
    return user


def create_token(*, data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=5)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def decode_token(token, group=False):
    error_detail = HTTPException(
        status_code=401,
        detail="Bad data",
        headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        print(token)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise error_detail
        if group is True:
            user_group: str = payload.get("group")
            return user_group
        valid_user = UserValidation(username=username)
    except jwt.PyJWTError as ex:
        raise error_detail
    engine = await async_return_engine()
    async with AsyncSession(engine) as session:
        stmt = select(UserInDB).where(UserInDB.username == valid_user.username)
        result = await session.execute(stmt)
        user = result.scalar_one()
        if not user:
            raise error_detail
        return user


@app.post("/token", response_model=Token)
async def login_in_acc(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await login_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Bad Data", headers={"WWW-Authenticate": "Bearer"})
    token = create_token(data={"sub": user.username, "group": user.group})
    return {"access_token": token, "token_type": "bearer"}


async def get_group(token: str = Depends(oauth2_scheme)):
    return await decode_token(token, group=True)


@app.get("/group")
async def get_user_group(group: str = Depends(get_group)):
    return {"group": group}


# TEST
@app.get("/admin-panel")
async def admin_panel(group: str = Depends(group_routes['admin-panel'])):
    return {'detail': 'you have perm'}






