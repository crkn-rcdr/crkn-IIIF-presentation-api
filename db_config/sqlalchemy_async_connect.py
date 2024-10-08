from sqlalchemy.ext.asyncio import create_async_engine,AsyncSession
from sqlalchemy.orm import declarative_base,sessionmaker
import os
from dotenv import load_dotenv
import ssl
from pathlib import Path

# load .env file
load_dotenv()

DB_URL = os.getenv("DB_URL")
cert_file = Path(__file__).resolve().parent.parent / 'DigiCertGlobalRootG2.crt.pem'

ssl_context = ssl.create_default_context(cafile=str(cert_file))
engine = create_async_engine(
                            DB_URL,
                            future=True,
                            echo=False,
                            connect_args={"ssl":ssl_context}
)
AsyncSessionFactory = sessionmaker(engine,expire_on_commit=False,class_=AsyncSession)
Base = declarative_base()

async def async_get_db():
    async with AsyncSessionFactory() as db:
        yield db
