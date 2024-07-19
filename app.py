from flask import Flask, render_template, request, jsonify
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Stock, Report, Worker, Foreman
import traceback
from sqlalchemy import func
import logging
from collections import OrderedDict

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("healthy-saga-428922-n9-d1d231903861.json", scope)
client = gspread.authorize(creds)
data_storage_sheet = client.open_by_url('https://docs.google.com/spreadsheets/d/1s1XJLQeE_M9W2lICO94CiNptZYDvxY66GbCR_LqE2AU/edit?gid=0#gid=0').worksheet("Data Storage")
report_sheet = client.open_by_url('https://docs.google.com/spreadsheets/d/1s1XJLQeE_M9W2lICO94CiNptZYDvxY66GbCR_LqE2AU/edit?gid=0#gid=0').worksheet("Report")
stock_sheet = client.open_by_url('https://docs.google.com/spreadsheets/d/1s1XJLQeE_M9W2lICO94CiNptZYDvxY66GbCR_LqE2AU/edit?gid=0#gid=0').worksheet("Stock")
workers_sheet = client.open_by_url('https://docs.google.com/spreadsheets/d/1s1XJLQeE_M9W2lICO94CiNptZYDvxY66GbCR_LqE2AU/edit?gid=0#gid=0').worksheet("Workers")
foremen_sheet = client.open_by_url('https://docs.google.com/spreadsheets/d/1s1XJLQeE_M9W2lICO94CiNptZYDvxY66GbCR_LqE2AU/edit?gid=0#gid=0').worksheet("Foremen")

# Local database setup
engine = create_engine('sqlite:///inventory.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

@app.route('/')
def index():
    return render_template('index.html', datetime=datetime)

@app.route('/get_foremen', methods=['GET'])
def get_foremen():
    try:
        foremen = session.query(Foreman.name).all()
        foremen = [f[0] for f in foremen]
        print(f"Fetched foremen: {foremen}")
        return jsonify({'foremen': foremen})
    except Exception as e:
        print(f"Error in get_foremen: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q', '').lower()
    search_type = request.args.get('type', 'name')
    print(f"Search query: {query}, type: {search_type}")

    if query:
        if search_type == 'name':
            items = session.query(Worker.name).all()
            items = [item[0] for item in items]
        else:
            items = []
        matched_items = [item for item in items if query in item.lower()]
        print(f"Matched items: {matched_items}")
        return jsonify(matched_items)
    return jsonify([])
@app.route('/submit', methods=['POST'])
def submit():
    try:
        data = request.json.get('data', [])
        print(f"Received data: {data}")

        if data:
            for entry in data:
                print(f"Processing entry: {entry}")

                worker = session.query(Worker).filter_by(name=entry['name']).first()
                if not worker:
                    print(f"Name not found in Worker table: {entry['name']}, adding it.")
                    worker = Worker(name=entry['name'])
                    session.add(worker)
                    session.commit()
                    print(f"Added name '{entry['name']}' to Worker table")

                foreman = session.query(Foreman).filter_by(name=entry['foreman']).first()
                if not foreman:
                    print(f"Foreman not found in Foreman table: {entry['foreman']}, adding it.")
                    foreman = Foreman(name=entry['foreman'])
                    session.add(foreman)
                    session.commit()
                    print(f"Added foreman '{entry['foreman']}' to Foreman table")

                # Update the Stock quantity
                stock_item = session.query(Stock).filter_by(
                    item=entry['item'],
                    item_type=entry['type'],
                    size=entry['size']
                ).first()
                if stock_item:
                    if stock_item.quantity >= int(entry['quantity']):
                        stock_item.quantity -= (int(entry['quantity']))
                        session.commit()
                    else:
                        return jsonify({'status': 'failure', 'message': f'Not enough stock for item {entry["item"]}, type {entry["type"]}, size {entry["size"]}. Available: {stock_item.quantity}, requested: {entry["quantity"]}'}), 400

                else:
                    return jsonify({'status': 'failure', 'message': f'Stock item not found for item {entry["item"]}, type {entry["type"]}, size {entry["size"]}.'}), 400

                # Add entry to report
                report_date = datetime.strptime(entry['date'], '%Y-%m-%d').date()  # Convert string to date
                new_report = Report(
                    date=report_date,
                    worker_name=entry['name'],
                    foreman_name=entry['foreman'],
                    item=entry['item'],
                    item_type=entry['type'],
                    size=entry['size'],
                    quantity=int(entry['quantity'])
                )
                session.add(new_report)
                session.commit()

            return jsonify({'status': 'success'})
        return jsonify({'status': 'failure', 'message': 'No data received'}), 400
    except Exception as e:
        session.rollback()
        print(f"Error in submit: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'status': 'failure', 'message': str(e)}), 500

    
@app.route('/get_items_and_types', methods=['GET'])
def get_items_and_types():
    try:
        items_and_types = session.query(Stock.item, Stock.item_type).distinct().all()
        items_sizes = {}

        for item, item_type in items_and_types:
            sizes = session.query(Stock.size, Stock.quantity).filter_by(item=item, item_type=item_type).all()
            if item not in items_sizes:
                items_sizes[item] = {}
            items_sizes[item][item_type] = [{'size': size, 'quantity': quantity} for size, quantity in sizes if quantity > 0]

        result = {}
        for item, item_type in items_and_types:
            if item not in result:
                result[item] = []
            if item_type:
                result[item].append(item_type)

        print(f"Fetched items and types: {result}")
        print(f"Fetched items and sizes: {items_sizes}")
        return jsonify({'items_and_types': result, 'items_sizes': items_sizes})
    except Exception as e:
        print(f"Error in get_items_and_types: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/load_all_data', methods=['GET'])
def load_all_data():
    try:
        # Очистка существующих данных
        session.query(Stock).delete()
        session.query(Worker).delete()
        session.query(Foreman).delete()

        # Загрузка данных stock
        stock_data = stock_sheet.get_all_values()
        if len(stock_data) < 3:
            raise ValueError("Stock sheet must have at least 3 rows")

        headers = stock_data[0]
        item_types = stock_data[1]
        sizes = [row[0] for row in stock_data[2:]]

        for col_idx in range(1, len(headers)):
            item = headers[col_idx]
            item_type = item_types[col_idx]  # Сохраняем полное значение типа

            for row_idx, size in enumerate(sizes):
                if row_idx + 2 < len(stock_data):
                    quantity = stock_data[row_idx + 2][col_idx]
                    if quantity and quantity.isdigit():
                        new_stock = Stock(
                            item=item,
                            item_type=item_type,  # Используем полное значение типа
                            size=size,
                            quantity=int(quantity)
                        )
                        session.add(new_stock)
                else:
                    app.logger.warning(f"Ran out of rows at index {row_idx + 2} for column {col_idx}")
                    break

        # Загрузка данных workers (без изменений)
        workers_data = workers_sheet.get_all_values()[1:]  # Пропускаем заголовок
        for row in workers_data:
            if row and row[0]:  # Проверяем, что строка не пуста и имя существует
                new_worker = Worker(name=row[0])
                session.add(new_worker)

        # Загрузка данных foremen (без изменений)
        foremen_data = foremen_sheet.get_all_values()[1:]  # Пропускаем заголовок
        for row in foremen_data:
            if row and row[0]:  # Проверяем, что строка не пуста и имя существует
                new_foreman = Foreman(name=row[0])
                session.add(new_foreman)

        session.commit()
        return jsonify({'status': 'success', 'message': 'All data loaded successfully'})
    except Exception as e:
        session.rollback()
        error_msg = f"An error occurred: {str(e)}\n{traceback.format_exc()}"
        app.logger.error(error_msg)
        return jsonify({'status': 'error', 'message': str(e)}), 500
    
    
@app.route('/download_all_data', methods=['POST'])
def download_all_data():
    app.logger.info("Starting download_all_data function")
    try:
        # Выгрузка данных stock
        app.logger.debug("Fetching stock data from database")
        stock_data = session.query(Stock).all()
        app.logger.debug(f"Fetched {len(stock_data)} stock records")

        # Define the expected size order
        size_order = ('S', 'M', 'L', 'XL', 'XLL', 'XLLL')

        # Group items and their types while preserving order
        items_and_types = OrderedDict()
        for stock in stock_data:
            if stock.item not in items_and_types:
                items_and_types[stock.item] = OrderedDict()
            if stock.item_type not in items_and_types[stock.item]:
                items_and_types[stock.item][stock.item_type] = True

        # Create header rows
        stock_sheet_data = [[''], ['']]  # First cell empty in both rows
        for item, types in items_and_types.items():
            stock_sheet_data[0].extend([item] * len(types))
            stock_sheet_data[1].extend([f"{type}({item})" for type in types])

        # Fill in the data
        for size in size_order:
            size_row = [size]
            for item, types in items_and_types.items():
                for item_type in types:
                    quantity = session.query(func.sum(Stock.quantity)).filter_by(
                        size=size, item=item, item_type=item_type).scalar()
                    size_row.append(quantity if quantity else 0)
            stock_sheet_data.append(size_row)

        app.logger.debug("Updating stock sheet")
        stock_sheet.clear()
        stock_sheet.append_rows(stock_sheet_data)
        app.logger.debug("Stock sheet updated successfully")

        # Выгрузка данных report
        app.logger.debug("Fetching report data from database")
        report_data = [['Date', 'Worker Name', 'Foreman Name', 'Item', 'Item Type', 'Size', 'Quantity']]
        report_records = session.query(Report).all()
        app.logger.debug(f"Fetched {len(report_records)} report records")
        report_data += [
            [str(report.date), report.worker_name, report.foreman_name,
             report.item, report.item_type, report.size, report.quantity]
            for report in report_records
        ]

        app.logger.debug("Updating report sheet")
        report_sheet.clear()
        report_sheet.append_rows(report_data)
        app.logger.debug("Report sheet updated successfully")

        app.logger.info("All data downloaded successfully")
        return jsonify({'status': 'success', 'message': 'All data downloaded successfully'})

    except Exception as e:
        app.logger.error(f"An error occurred: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({'status': 'error', 'message': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
    app.config['DEBUG'] = True
    app.config['PROPAGATE_EXCEPTIONS'] = True
    
