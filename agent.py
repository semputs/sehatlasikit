import os
import csv
import json
import requests
from datetime import datetime

# 1. Fetch Google Sheet CSV
SHEET_CSV_URL = os.environ.get("SHEET_CSV_URL")
if not SHEET_CSV_URL:
    raise ValueError("SHEET_CSV_URL secret is not set.")

response = requests.get(SHEET_CSV_URL)
response.encoding = 'utf-8'

csv_lines = response.text.splitlines()
reader = csv.DictReader(csv_lines)

# 2. Map CSV rows to dashboard JSON format
dashboard_data = []
for row in reader:
    # Convert keys to lowercase and strip whitespace
    r = {k.strip().lower(): v.strip() for k, v in row.items() if k}
    
    date_val = r.get('date', '')
    if date_val and date_val.lower() != 'date':
        dashboard_data.append({
            "week": r.get('week', ''),
            "date": date_val,
            "day": r.get('day', ''),
            "weight": r.get('weight', '--'),
            "activity": r.get('activity', '--'),
            "breakfast": r.get('breakfast', '--'),
            "b_score": r.get('b_score', '--'),
            "lunch": r.get('lunch', '--'),
            "l_score": r.get('l_score', '--'),
            "dinner": r.get('dinner', '--'),
            "d_score": r.get('d_score', '--'),
            "comments": r.get('comments', '')
        })

# 3. Inject updated JSON into index.html
with open('index.html', 'r', encoding='utf-8') as f:
    html_content = f.read()

json_string = json.dumps(dashboard_data, indent=2)

# Replace window.dashboardData array
before = html_content.split('window.dashboardData =')[0]
after = html_content.split('window.dashboardData =')[1].split(';', 1)[1]
updated_html = before + f'window.dashboardData = {json_string};' + after

# Replace last-updated footer timestamp
if 'id="last-updated">' in updated_html:
    now_str = datetime.now().strftime("%b %d, %Y • %H:%M UTC")
    part1 = updated_html.split('id="last-updated">')[0]
    part2 = updated_html.split('id="last-updated">')[1].split('</span>', 1)[1]
    updated_html = part1 + f'id="last-updated">{now_str}</span>' + part2

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(updated_html)

print(f"Successfully updated index.html with {len(dashboard_data)} records from Google Sheets!")
