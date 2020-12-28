from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String

Base = declarative_base()


class UserInDB(Base):
    __tablename__ = 'user_work_fastapi_password'

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)

    def __init__(self, username, password):
        self.username = username
        self.password = password
