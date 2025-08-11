from sqlalchemy import create_engine, Column, Integer, String, Text, TIMESTAMP,and_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os


DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/postgres')

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()


class Chats(Base):
    __tablename__ = 'chats'
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=True)
    chat_name = Column(String(50), nullable=True)
    content = Column(Text, nullable=True)
    timestamp = Column(TIMESTAMP, nullable=False)

    def init_db():
        """Initialize the database."""
        Base.metadata.create_all(bind=engine)

    def __repr__(self):
        return f"<RequestsLog(id={self.id}, endpoint={self.endpoint}, parameters={self.parameters}, result={self.result}, timestamp={self.timestamp})>"

    @staticmethod
    def get_chats_by_username(username):
        """Retrieve chats by their username."""
        session = SessionLocal()
        try:
            chats = session.query(Chats).filter(Chats.username == username).order_by(Chats.timestamp.desc()).limit(10).all()
            return chats or []
        finally:
            session.close()

    @staticmethod
    def get_chat_by_id(session, id):
        """Retrieve a chat entry by its ID."""
        return session.query(Chats).filter(Chats.id == id).first()
    
    
