import os
from sqlalchemy import create_engine, Column, Integer, String, Text, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import bcrypt

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/postgres')

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)

    def init_db():
        """Initialize the database."""
        Base.metadata.create_all(bind=engine)
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"
    
    @staticmethod
    def get_user_by_id(user_id):
        """Retrieve a user by their ID."""
        session = SessionLocal()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            return user
        finally:
            session.close()

    @staticmethod
    def get_user_by_username(username):
        """Retrieve a user by their username."""
        session = SessionLocal()
        try:
            user = session.query(User).filter(User.username == username).first()
            return user
        finally:
            session.close()

    @staticmethod
    def get_user_by_email(self, email):
        """Retrieve a user by their email."""
        session = SessionLocal()
        try:
            user = session.query(User).filter(User.email == email).first()
            return user
        finally:
            session.close()

    @staticmethod
    def exists_password_and_user(usr, password):
        """Check if a user with the given username and password exists."""
        session = SessionLocal()
        try:
            user = session.query(User).filter(User.username == usr).first()
            if user and bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
                return True
            return False
        finally:
            session.close()

