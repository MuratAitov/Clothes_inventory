from flask import Flask, render_template, request, jsonify
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Stock, Report, Worker, Foreman
import traceback

app = Flask(__name__)

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("healthy-saga-428922-n9-d1d231903861.json", scope)
client = gspread.authorize(creds)
data_storage_sheet = client.open_by_url('https://docs.google.com/spreadsheets/d/1s1XJLQeE_M9W2lICO94CiNptZYDvxY66GbCR_LqE2AU/edit?gid=0#gid=0').worksheet("Data Storage")
report_sheet = client.open_by_url('https://docs.google.com/spreadsheets/d/1s1XJLQeE_M9W2lICO94CiNptZYDvxY66GbCR_LqE2AU/edit?gid=0#gid=0').worksheet("Report")
stock_sheet = client.open_by_url('https://docs.google.com/spreadsheets/d/1s1XJLQeE_M9W2lICO94CiNptZYDvxY66GbCR_LqE2AU/edit?gid=0#gid=0').worksheet("Stock")

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

                new_entry = Stock(
                    item=entry['item'],
                    item_type=entry['type'],
                    size=entry['quantity'],  # Assuming size is stored in quantity field
                    quantity=int(entry['quantity'])
                )
                session.add(new_entry)
                session.commit()

                # Add entry to report
                report_date = datetime.strptime(entry['date'], '%Y-%m-%d').date()  # Convert string to date
                new_report = Report(
                    date=report_date,
                    worker_name=entry['name'],
                    foreman_name=entry['foreman'],
                    item=entry['item'],
                    item_type=entry['type'],
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

@app.route('/load_stock', methods=['GET'])
def load_stock():
    try:
        session.query(Stock).delete()  # Clear existing data in the local database

        data = stock_sheet.get_all_values()
        headers = data[0]
        sizes = [row[0] for row in data[1:]]

        for col_idx in range(1, len(headers)):
            item_info = headers[col_idx].split(' ')
            item = item_info[0]
            item_type = item_info[1] if len(item_info) > 1 else ""
            for row_idx in range(1, len(data)):
                size = sizes[row_idx - 1]
                quantity = data[row_idx][col_idx]
                if quantity:
                    new_stock = Stock(
                        item=item,
                        item_type=item_type,
                        size=size,
                        quantity=int(quantity)
                    )
                    session.add(new_stock)
        session.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        session.rollback()
        print(f"Error in load_stock: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'status': 'failure', 'message': str(e)}), 500

@app.route('/download_stock', methods=['POST'])
def download_stock():
    try:
        stock_data = session.query(Stock).all()
        sizes = sorted(set(stock.size for stock in stock_data))
        items = sorted(set((stock.item, stock.item_type) for stock in stock_data))

        data = [['Size'] + [f"{item} {item_type}" for item, item_type in items]]

        for size in sizes:
            row = [size]
            for item, item_type in items:
                quantity = session.query(Stock.quantity).filter_by(size=size, item=item, item_type=item_type).first()
                row.append(quantity[0] if quantity else 0)
            data.append(row)

        # Clear existing data in the Google Sheet
        stock_sheet.clear()
        # Update the sheet with new data
        for row in data:
            stock_sheet.append_row(row)

        return jsonify({'status': 'success'})
    except Exception as e:
        print(f"Error in download_stock: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'status': 'failure', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
