from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Date

# Создаем движок SQLAlchemy для подключения к базе данных
engine = create_engine('sqlite:///inventory.db')
metadata = MetaData()

# Удаляем старую таблицу reports, если она существует

# Создаем новую таблицу report с нужными столбцами
report_table = Table(
    'report', metadata,
    Column('id', Integer, primary_key=True),
    Column('date', Date),
    Column('worker_name', String),
    Column('foreman_name', String),
    Column('item', String),
    Column('item_type', String),
    Column('size', String),
    Column('quantity', Integer)
)

# Создаем новую таблицу в базе данных
metadata.create_all(engine)

# Закрываем соединение
engine.dispose()
