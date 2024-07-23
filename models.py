import os
from sqlalchemy import create_engine, Column, Integer, String, Date
from sqlalchemy.orm import declarative_base, sessionmaker

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
    size = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)

class IndividualReport(Base):
    __tablename__ = 'individual_report'
    id = Column(Integer, primary_key=True)
    worker_name = Column(String)
    total_tshirts_last_year = Column(Integer)
    last_tshirt_date = Column(Date)

# Используем базу данных Heroku PostgreSQL
DATABASE_URL = 'postgresql://u18fk5qasngcqm:p03daa10dcc2c67d95aeb405c130e7b48f981f6ec3e0c23f9500eb0d4e3a61726@c67okggoj39697.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/d2j7ej2dt1tjo9'
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()
