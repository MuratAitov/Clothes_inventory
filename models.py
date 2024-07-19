from sqlalchemy import Column, Integer, String, Date, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

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
    
    
class Report(Base):
    __tablename__ = 'report'
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False)
    worker_name = Column(String, nullable=False)
    foreman_name = Column(String, nullable=False)
    item = Column(String, nullable=False)
    item_type = Column(String, nullable=False)
    size = Column(String, nullable=False)  # New column
    quantity = Column(Integer, nullable=False)
    
class IndividualReport(Base):
    __tablename__ = 'individual_report'
    id = Column(Integer, primary_key=True)
    worker_name = Column(String)
    total_tshirts_last_year = Column(Integer)
    last_tshirt_date = Column(Date)

engine = create_engine('sqlite:///inventory.db')
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()
