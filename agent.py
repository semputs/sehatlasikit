import os
import csv
import json
import requests

# 1. Fetch Google Sheet CSV
SHEET_CSV_URL = os.environ.get("SHEET_CSV_URL")
if not SHEET_CSV_URL:
    raise ValueError("SHEET_CSV_URL secret is not set.")

response = requests.get(SHEET_CSV_URL)
response.encoding = 'utf-8'

csv_lines = response.text.splitlines()
reader = csv.DictReader(csv_lines)
rows = list(reader)

# 2. Map CSV rows to dashboard JSON format
dashboard_data = []
for row in rows:
    # Use key names matching your spreadsheet columns
    if row.get('date'):
        dashboard_data.append({
            "week": row.get('week', ''),
            "date": row.get('date', ''),
            "day": row.get('day', ''),
            "weight": row.get('weight', '--'),
            "activity": row.get('activity', '--'),
            "breakfast": row.get('breakfast', '--'),
            "b_score": row.get('b_score', '--'),
            "lunch": row.get('lunch', '--'),
            "l_score": row.get('l_score', '--'),
            "dinner": row.get('dinner', '--'),
            "d_score": row.get('d_score', '--'),
            "comments": row.get('comments', '')
        })

# 3. Inject updated JSON into index.html
with open('index.html', 'r', encoding='utf-8') as f:
    html_content = f.read()

json_string = json.dumps(dashboard_data, indent=2)

# Replace existing window.dashboardData array
before = html_content.split('window.dashboardData =')[0]
after = html_content.split('window.dashboardData =')[1].split(';', 1)[1]

updated_html = before + f'window.dashboardData = {json_string};' + after

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(updated_html)

print(f"Successfully updated index.html with {len(dashboard_data)} records from Google Sheets!")
