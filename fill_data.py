from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Stock

# Создание соединения с базой данных
engine = create_engine('sqlite:///inventory.db')
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

# Данные для заполнения таблицы stock
stock_data = [
    {"item": "T-shirt", "item_type": "Orange(worker)", "size": "S", "quantity": 10},
    {"item": "T-shirt", "item_type": "Orange(worker)", "size": "M", "quantity": 20},
    {"item": "T-shirt", "item_type": "Orange(worker)", "size": "L", "quantity": 30},
    {"item": "T-shirt", "item_type": "Orange(worker)", "size": "XL", "quantity": 40},
    {"item": "T-shirt", "item_type": "Orange(worker)", "size": "XLL", "quantity": 50},
    {"item": "T-shirt", "item_type": "Red(foreman)", "size": "S", "quantity": 5},
    {"item": "T-shirt", "item_type": "Red(foreman)", "size": "M", "quantity": 15},
    {"item": "T-shirt", "item_type": "Red(foreman)", "size": "L", "quantity": 25},
    {"item": "T-shirt", "item_type": "Red(foreman)", "size": "XL", "quantity": 35},
    {"item": "T-shirt", "item_type": "Red(foreman)", "size": "XLL", "quantity": 45},
    {"item": "T-shirt", "item_type": "Office(black)", "size": "S", "quantity": 8},
    {"item": "T-shirt", "item_type": "Office(black)", "size": "M", "quantity": 18},
    {"item": "T-shirt", "item_type": "Office(black)", "size": "L", "quantity": 28},
    {"item": "T-shirt", "item_type": "Office(black)", "size": "XL", "quantity": 38},
    {"item": "T-shirt", "item_type": "Office(black)", "size": "XLL", "quantity": 48},
    # Add more initial stock data as needed
]

# Добавление данных в сессию и сохранение в базе данных
stocks = [Stock(item=data["item"], item_type=data["item_type"], size=data["size"], quantity=data["quantity"]) for data in stock_data]

session.add_all(stocks)
session.commit()

print("Данные успешно добавлены в таблицу stock.")
