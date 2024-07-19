from flask import Flask, render_template, request, jsonify
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import traceback

app = Flask(__name__)

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("healthy-saga-428922-n9-d1d231903861.json", scope)
client = gspread.authorize(creds)
data_storage_sheet = client.open_by_url('https://docs.google.com/spreadsheets/d/1s1XJLQeE_M9W2lICO94CiNptZYDvxY66GbCR_LqE2AU/edit?gid=0#gid=0').worksheet("Data Storage")
report_sheet = client.open_by_url('https://docs.google.com/spreadsheets/d/1s1XJLQeE_M9W2lICO94CiNptZYDvxY66GbCR_LqE2AU/edit?gid=0#gid=0').worksheet("Report")

@app.route('/')
def index():
    return render_template('index.html', datetime=datetime)

@app.route('/get_foremen', methods=['GET'])
def get_foremen():
    try:
        foremen = list(set(data_storage_sheet.col_values(2)[1:]))  # Get unique foremen, skip header
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
            items = data_storage_sheet.col_values(1)[1:]  # Assuming names are in the first column, skip header
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
            names = data_storage_sheet.col_values(1)[1:]  # Existing names in column A
            foremen = data_storage_sheet.col_values(2)[1:]  # Existing foremen in column B
            print(f"Existing names: {names}")
            print(f"Existing foremen: {foremen}")

            for entry in data:
                print(f"Processing entry: {entry}")
                if entry['name'] not in names:
                    print(f"Name not found in Data Storage: {entry['name']}, adding it.")
                    row = len(data_storage_sheet.get_all_values()) + 1  # Determine the next row to add the name
                    data_storage_sheet.update_cell(row, 1, entry['name'])  # Update the specific cell in column A (column index 1)
                    data_storage_sheet.update_cell(row, 2, entry['foreman'])  # Update the specific cell in column B (column index 2)
                    print(f"Added name '{entry['name']}' with foreman '{entry['foreman']}' to row {row}")  # Column index is 1
                    names.append(entry['name'])  # Update the list of names

                print(f"Adding entry to report sheet: {entry}")
                report_sheet.append_row([entry['date'], entry['name'], entry['foreman'], entry['item'], entry['type'], entry['quantity']])

            return jsonify({'status': 'success'})
        return jsonify({'status': 'failure', 'message': 'No data received'}), 400
    except Exception as e:
        print(f"Error in submit: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'status': 'failure', 'message': str(e)}), 500

@app.route('/get_items_and_types', methods=['GET'])
def get_items_and_types():
    try:
        items = data_storage_sheet.col_values(4)[1:] 
        types = data_storage_sheet.col_values(5)[1:] 

        items_and_types = {}
        for item, item_type in zip(items, types):
            if item not in items_and_types:
                items_and_types[item] = []
            if item_type:
                items_and_types[item].append(item_type)

        print(f"Fetched items and types: {items_and_types}")
        return jsonify({'items_and_types': items_and_types})
    except Exception as e:
        print(f"Error in get_items_and_types: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
