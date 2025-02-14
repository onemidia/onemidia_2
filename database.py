from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, declarative_base
import os

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
Base = declarative_base()

def init_db():
    from models import Produto
    Base.metadata.create_all(bind=engine)

def get_db():
    db = db_session()
    try:
        yield db
    finally:
        db.close()
