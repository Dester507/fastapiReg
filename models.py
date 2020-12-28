from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, LargeBinary

Base = declarative_base()


class UserInDB(Base):
    __tablename__ = 'user_work_fastapi_password'

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(LargeBinary, nullable=False)

    group = Column(String, default='default')

    def __init__(self, username, password):
        self.username = username
        self.password = password


class Salt(Base):
    __tablename__ = 'user_salts_fastapi_password'

    id = Column(Integer, primary_key=True)
    user = Column(String, unique=True)
    salt = Column(LargeBinary, nullable=False)

    def __init__(self, user, salt):
        self.user = user
        self.salt = salt
