from flask import Flask, render_template, request, jsonify
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import traceback
import logging

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("healthy-saga-428922-n9-d1d231903861.json", scope)
client = gspread.authorize(creds)
sheet = client.open_by_url('https://docs.google.com/spreadsheets/d/1s1XJLQeE_M9W2lICO94CiNptZYDvxY66GbCR_LqE2AU/edit?gid=0#gid=0')
stock_sheet = sheet.worksheet("Stock")
report_sheet = sheet.worksheet("Report")
workers_sheet = sheet.worksheet("Workers")
foremen_sheet = sheet.worksheet("Foremen")

@app.route('/')
def index():
    return render_template('index.html', datetime=datetime)

@app.route('/get_foremen', methods=['GET'])
def get_foremen():
    try:
        foremen = foremen_sheet.col_values(1)[1:]  # Пропускаем заголовок
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
            items = workers_sheet.col_values(1)[1:]  # Пропускаем заголовок
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
            # Get all stock data at once
            stock_data = stock_sheet.get_all_values()
            headers = stock_data[0]
            item_types = stock_data[1]
            sizes = [row[0] for row in stock_data[2:]]

            for entry in data:
                print(f"Processing entry: {entry}")
                
                
                existing_workers = workers_sheet.col_values(1)
                if entry['name'] not in existing_workers:
                    workers_sheet.append_row([entry['name']])

                item_col = headers.index(entry['item'])
                type_row = item_types.index(entry['type'])
                size_row = sizes.index(entry['size']) + 2

                print(f"Item column: {item_col}")
                print(f"Type row: {type_row}")
                print(f"Size row: {size_row}")

                current_quantity = stock_data[size_row][item_col]
                print(f"Current quantity (raw): {current_quantity}")

                current_quantity = int(current_quantity) if current_quantity and current_quantity.isdigit() else 0
                print(f"Current quantity (processed): {current_quantity}")

                new_quantity = current_quantity - int(entry['quantity'])
                print(f"New quantity: {new_quantity}")
                
                if new_quantity < 0:
                    error_message = f"Not enough stock for {entry['item']} {entry['type']} size {entry['size']}. Current: {current_quantity}, Requested: {entry['quantity']}"
                    print(error_message)
                    return jsonify({'status': 'failure', 'message': error_message}), 400
                
                # Update the stock data
                stock_data[size_row][item_col] = str(new_quantity)
                stock_sheet.update(f'A1:{chr(65+len(headers)-1)}{len(stock_data)}', stock_data)

                # Add entry to Report sheet
                report_sheet.append_row([
                    entry['date'],
                    entry['name'],
                    entry['foreman'],
                    entry['item'],
                    entry['type'],
                    entry['size'],
                    entry['quantity']
                ])

            return jsonify({'status': 'success'})
        return jsonify({'status': 'failure', 'message': 'No data received'}), 400
    except Exception as e:
        print(f"Error in submit: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'status': 'failure', 'message': str(e)}), 500

@app.route('/get_items_and_types', methods=['GET'])
def get_items_and_types():
    try:
        stock_data = stock_sheet.get_all_values()
        headers = stock_data[0]  # Get all headers
        sizes = [row[0] for row in stock_data[1:] if row[0].strip()]  # Sizes are in the first column

        items_and_types = {}
        items_sizes = {}

        for col, item in enumerate(headers[1:], start=1):  # Skip the first column (sizes)
            if item and item.strip():
                items_and_types[item] = set()
                items_sizes[item] = {}

                for row in range(1, len(stock_data)):
                    if col < len(stock_data[row]):
                        item_type = stock_data[row][col].strip()
                        if item_type:
                            items_and_types[item].add(item_type)
                            
                            if row - 1 < len(sizes):  # Check if the size index is within range
                                size = sizes[row - 1]
                                quantity = int(stock_data[row][col]) if stock_data[row][col].isdigit() else 0
                                
                                if item_type not in items_sizes[item]:
                                    items_sizes[item][item_type] = []
                                
                                if quantity > 0:
                                    items_sizes[item][item_type].append({'size': size, 'quantity': quantity})

        # Convert sets to lists for JSON serialization
        for item in items_and_types:
            items_and_types[item] = list(items_and_types[item])

        print(f"Fetched items and types: {items_and_types}")
        print(f"Fetched items and sizes: {items_sizes}")
        return jsonify({'items_and_types': items_and_types, 'items_sizes': items_sizes})
    except Exception as e:
        error_message = f"Error in get_items_and_types: {str(e)}"
        print(error_message)
        print("Current state:")
        print(f"stock_data length: {len(stock_data)}")
        print(f"headers: {headers}")
        print(f"sizes: {sizes}")
        print(traceback.format_exc())
        return jsonify({'error': error_message, 'details': traceback.format_exc()}), 500

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)