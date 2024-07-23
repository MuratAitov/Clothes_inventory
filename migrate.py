import os
import sqlite3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Stock, Report, Worker, Foreman

# Подключение к локальной базе данных SQLite
sqlite_engine = create_engine('sqlite:///inventory.db')
SQLiteSession = sessionmaker(bind=sqlite_engine)
sqlite_session = SQLiteSession()

# Подключение к базе данных PostgreSQL на Heroku
DATABASE_URL = 'postgresql://u18fk5qasngcqm:p03daa10dcc2c67d95aeb405c130e7b48f981f6ec3e0c23f9500eb0d4e3a61726@c67okggoj39697.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/d2j7ej2dt1tjo9'
postgres_engine = create_engine(DATABASE_URL)
PostgreSQLSession = sessionmaker(bind=postgres_engine)
postgres_session = PostgreSQLSession()

# Создание таблиц в базе данных PostgreSQL
Base.metadata.create_all(postgres_engine)

# Миграция данных из SQLite в PostgreSQL
for item in sqlite_session.query(Stock).all():
    postgres_session.add(Stock(
        item=item.item,
        item_type=item.item_type,
        size=item.size,
        quantity=item.quantity
    ))

for report in sqlite_session.query(Report).all():
    postgres_session.add(Report(
        date=report.date,
        worker_name=report.worker_name,
        foreman_name=report.foreman_name,
        item=report.item,
        item_type=report.item_type,
        size=report.size,
        quantity=report.quantity
    ))

for worker in sqlite_session.query(Worker).all():
    postgres_session.add(Worker(
        name=worker.name
    ))

for foreman in sqlite_session.query(Foreman).all():
    postgres_session.add(Foreman(
        name=foreman.name
    ))

# Коммит изменений и закрытие сессий
postgres_session.commit()
sqlite_session.close()
postgres_session.close()
