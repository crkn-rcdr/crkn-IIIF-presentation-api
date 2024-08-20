from sqlalchemy.ext.asyncio import create_async_engine,AsyncSession
from sqlalchemy.orm import declarative_base,sessionmaker
import os
from dotenv import load_dotenv

# load .env file
load_dotenv()

DB_URL = os.getenv("DB_URL")
engine = create_async_engine(DB_URL,future=True,echo=False)
AsyncSessionFactory = sessionmaker(engine,expire_on_commit=False,class_=AsyncSession)
Base = declarative_base()

async def async_get_db():
    async with AsyncSessionFactory() as db:
        yield db
