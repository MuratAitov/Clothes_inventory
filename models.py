from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Stock(Base):
    __tablename__ = 'stock'
    id = Column(Integer, primary_key=True)
    item = Column(String, nullable=False)
    item_type = Column(String, nullable=False)
    size = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)

class Worker(Base):
    __tablename__ = 'workers'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

class Foreman(Base):
    __tablename__ = 'foremen'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

engine = create_engine('sqlite:///inventory.db')
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()
