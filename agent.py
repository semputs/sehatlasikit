import os
import csv
import json
import re
import requests
from datetime import datetime

# 1. Fetch Google Sheet CSV
SHEET_CSV_URL = os.environ.get("SHEET_CSV_URL")
if not SHEET_CSV_URL:
    raise ValueError("SHEET_CSV_URL secret is not set in GitHub Secrets.")

print("Fetching spreadsheet data from CSV URL...")
response = requests.get(SHEET_CSV_URL)
response.encoding = 'utf-8'

if response.status_code != 200 or "<html" in response.text.lower():
    raise ValueError("Failed to fetch CSV. Ensure Google Sheet sharing is set to 'Anyone with the link can view'.")

csv_lines = response.text.splitlines()
reader = csv.DictReader(csv_lines)

# Variables to track peak metrics and dates
latest_weight = "--"
latest_weight_date = ""

peak_speed = 0.0
peak_speed_date = ""

peak_distance = 0.0
peak_distance_date = ""

dashboard_data = []

for row in reader:
    r = {str(k).strip().lower(): str(v).strip() for k, v in row.items() if k}
    date_val = r.get('date', '')

    if date_val and date_val.lower() != 'date':
        comments_val = r.get('comments', '')
        weight_val = r.get('weight', '--')
        activity_val = r.get('activity', '--')

        # Fallback sleep extraction
        sleep_val = r.get('sleep', '')
        if not sleep_val or sleep_val == '--':
            match = re.search(r'(?:slept|sleep)\D*?(\d+(?:\.\d+)?)\s*(?:h|hrs|hours)\b', comments_val, re.IGNORECASE)
            sleep_val = match.group(1) if match else '--'

        # Extract latest non-empty weight
        if weight_val not in ['--', '', '-']:
            clean_wt = re.findall(r'\d+(?:\.\d+)?', weight_val)
            if clean_wt:
                latest_weight = f"{clean_wt[0]} kg"
                latest_weight_date = date_val

        # Extract peak distance (e.g. 3.2km, 3.5 km, Distance 3.1)
        dist_match = re.search(r'(\d+(?:\.\d+)?)\s*km\b', activity_val, re.IGNORECASE)
        if dist_match:
            dist_num = float(dist_match.group(1))
            if dist_num > peak_distance:
                peak_distance = dist_num
                peak_distance_date = date_val

        # Extract peak speed (e.g. speed 7.6, 7.4 km/h)
        spd_matches = re.findall(r'(?:speed|@|\b)(\d+\.\d+)\b', activity_val, re.IGNORECASE)
        for spd_str in spd_matches:
            spd_num = float(spd_str)
            if spd_num > peak_speed:
                peak_speed = spd_num
                peak_speed_date = date_val

        dashboard_data.append({
            "week": r.get('week', ''),
            "date": date_val,
            "day": r.get('day', ''),
            "weight": weight_val,
            "activity": activity_val,
            "breakfast": r.get('breakfast', '--'),
            "b_score": r.get('b_score', '--'),
            "lunch": r.get('lunch', '--'),
            "l_score": r.get('l_score', '--'),
            "dinner": r.get('dinner', '--'),
            "d_score": r.get('d_score', '--'),
            "sleep": sleep_val,
            "comments": comments_val
        })

print(f"Parsed {len(dashboard_data)} records from spreadsheet.")
if len(dashboard_data) == 0:
    raise ValueError("No records found in CSV.")

# Format peak strings
peak_speed_str = f"{peak_speed:.1f} km/h" if peak_speed > 0 else "--"
peak_dist_str = f"{peak_distance:.2f} km" if peak_distance > 0 else "--"

# Inject JSON into index.html
with open('index.html', 'r', encoding='utf-8') as f:
    html_content = f.read()

if 'window.dashboardData =' not in html_content:
    raise ValueError("Could not find 'window.dashboardData =' marker in index.html.")

json_string = json.dumps(dashboard_data, indent=2)
before = html_content.split('window.dashboardData =')[0]
after = html_content.split('window.dashboardData =')[1].split(';', 1)[1]
updated_html = before + f'window.dashboardData = {json_string};' + after

# Update last-updated header
if 'id="last-updated">' in updated_html:
    now_str = datetime.now().strftime("%b %d, %Y • %H:%M MYT")
    p1 = updated_html.split('id="last-updated">')[0]
    p2 = updated_html.split('id="last-updated">')[1].split('</', 1)[1]
    updated_html = p1 + f'id="last-updated">{now_str}</' + p2

# Helper function to inject values into element IDs
def update_element_by_id(html, element_id, value_text):
    if f'id="{element_id}"' in html:
        p1 = html.split(f'id="{element_id}">')[0]
        p2 = html.split(f'id="{element_id}">')[1].split('</', 1)[1]
        return p1 + f'id="{element_id}">{value_text}</' + p2
    return html

# Replace stat card values and dates
updated_html = update_element_by_id(updated_html, "kpi-weight", latest_weight)
updated_html = update_element_by_id(updated_html, "kpi-speed", peak_speed_str)
updated_html = update_element_by_id(updated_html, "kpi-distance", peak_dist_str)

updated_html = update_element_by_id(updated_html, "kpi-weight-date", f"as of {latest_weight_date}" if latest_weight_date else "--")
updated_html = update_element_by_id(updated_html, "kpi-speed-date", f"hit on {peak_speed_date}" if peak_speed_date else "--")
updated_html = update_element_by_id(updated_html, "kpi-distance-date", f"hit on {peak_distance_date}" if peak_distance_date else "--")

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(updated_html)

print("Successfully injected stats and dates into index.html!")
