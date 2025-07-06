#!/usr/bin/env python3

import pandas as pd
import json
import argparse
import requests
from datetime import datetime
from collections import defaultdict, Counter
from jinja2 import Template
import warnings
from colorama import init, Fore, Style

# Initialise colour support
init(autoreset=True)

# Suppress warnings
warnings.simplefilter("ignore", category=DeprecationWarning)
warnings.simplefilter("ignore", category=UserWarning)

# ---------- CONFIG ----------
IPINFO_TOKEN = "your_api_token_here"
IPINFO_URL = "https://ipinfo.io/{ip}?token=" + IPINFO_TOKEN

PRIVATE_IP_PREFIXES = (
    "10.", "172.16.", "172.17.", "172.18.", "172.19.", "172.20.", "172.21.", "172.22.", "172.23.",
    "172.24.", "172.25.", "172.26.", "172.27.", "172.28.", "172.29.", "172.30.", "172.31.",
    "192.168.", "127.", "169.254.", "::1"
)

TIMEZONE_OPTIONS = sorted([
    "Africa/Johannesburg",
    "America/Anchorage",
    "America/Chicago",
    "America/Denver",
    "America/Los_Angeles",
    "America/New_York",
    "America/Sao_Paulo",
    "Asia/Bangkok",
    "Asia/Dubai",
    "Asia/Kolkata",
    "Asia/Seoul",
    "Asia/Shanghai",
    "Asia/Singapore",
    "Asia/Tokyo",
    "Australia/Brisbane",
    "Australia/Perth",
    "Australia/Sydney",
    "Europe/Berlin",
    "Europe/London",
    "Europe/Madrid",
    "Europe/Moscow",
    "Europe/Paris",
    "Pacific/Auckland",
    "Pacific/Fiji",
    "Pacific/Honolulu",
    "UTC"
])

# ---------- PARSE CLI ----------
parser = argparse.ArgumentParser(description="Generate GoPhish HTML report from CSV export.")
parser.add_argument("csv_file", help="Path to GoPhish CSV export file")
args = parser.parse_args()

INPUT_CSV = args.csv_file
now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
OUTPUT_HTML = f"{now_str}.html"

# ---------- UTILITY PRINT FUNCTIONS ----------
def log_info(message):
    print(f"{Fore.WHITE}[ * ] {message}{Style.RESET_ALL}")

def log_action(message):
    print(f"{Fore.WHITE}[ + ] {message}{Style.RESET_ALL}")

def log_success(message):
    print(f"{Fore.GREEN}[ ✔ ] {message}{Style.RESET_ALL}")

def log_progress(message):
    print(f"{Fore.CYAN}[ * ] {message}{Style.RESET_ALL}")

# ---------- START PROCESS ----------
log_info("Starting data processing...")

log_action("Reading CSV file...")
df = pd.read_csv(INPUT_CSV, header=None, names=["id", "email", "timestamp", "event", "details"])
df = df[df["email"].notnull()]
df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)
log_success(f"CSV loaded. Rows: {len(df)}")

# ---------- EXTRACT DETAILS ----------
log_action("Extracting details...")
ip_list = []
ua_list = []
client_id_list = []
submitted_creds = []

total_rows = df.shape[0]
for idx, (_, row) in enumerate(df.iterrows(), 1):
    details = row["details"]
    if pd.isnull(details) or details.strip() == "":
        ip_list.append(None)
        ua_list.append(None)
        client_id_list.append(None)
        submitted_creds.append(None)
        continue

    try:
        j = json.loads(details)
        browser = j.get("browser", {})
        ip_list.append(browser.get("address", None))
        ua_list.append(browser.get("user-agent", None))

        payload = j.get("payload", {})
        client_ids = payload.get("client_id", [])
        client_id_list.append(client_ids[0] if client_ids else None)

        if row["event"] == "Submitted Data":
            extracted = []
            for key, value in payload.items():
                if key == "client_id":
                    continue
                if isinstance(value, list) and value:
                    extracted.append((key, value[0]))
                elif isinstance(value, str):
                    extracted.append((key, value))
            submitted_creds.append(extracted)
        else:
            submitted_creds.append(None)
    except Exception:
        ip_list.append(None)
        ua_list.append(None)
        client_id_list.append(None)
        submitted_creds.append(None)

    if idx % 200 == 0 or idx == total_rows:
        log_progress(f"Extracting details... {idx}/{total_rows}")

df["ip"] = ip_list
df["user_agent"] = ua_list
df["client_id"] = client_id_list
df["credentials"] = submitted_creds
log_success("Details extraction complete.")

# ---------- IP LOOKUPS ----------
geo_cache = {}

def lookup_ip(ip):
    if ip in geo_cache:
        return geo_cache[ip]
    if not ip:
        geo_cache[ip] = ("N/A", "N/A")
        return geo_cache[ip]
    if ip.startswith(PRIVATE_IP_PREFIXES):
        geo_cache[ip] = ("Private/Reserved", "Private/Reserved")
        return geo_cache[ip]
    try:
        r = requests.get(IPINFO_URL.format(ip=ip), timeout=5)
        if r.status_code == 200:
            j = r.json()
            city = j.get("city", "")
            region = j.get("region", "")
            country = j.get("country", "")
            org = j.get("org", "")
            parts = [p for p in [city, region, country] if p]
            location = ", ".join(parts) if parts else "Unknown"
            geo_cache[ip] = (location, org)
            return geo_cache[ip]
        else:
            geo_cache[ip] = ("Lookup Failed", "N/A")
            return geo_cache[ip]
    except:
        geo_cache[ip] = ("Lookup Failed", "N/A")
        return geo_cache[ip]

log_action("Performing IP lookups...")
unique_ips = df["ip"].dropna().unique()
total_ips = len(unique_ips)
for idx, ip in enumerate(unique_ips, 1):
    lookup_ip(ip)
    if idx % 10 == 0 or idx == total_ips:
        log_progress(f"Performing IP lookups... {idx}/{total_ips}")
log_success("IP lookup complete.")

# ---------- BUILD USERS ----------
log_action("Building user data...")
users = defaultdict(lambda: {"email": "", "events": []})

for _, row in df.iterrows():
    email = row["email"]
    if pd.isna(email) or email.strip() == "":
        continue
    if row["event"] not in ["Email Sent", "Email Opened", "Clicked Link", "Submitted Data"]:
        continue

    ip = row["ip"]
    location, isp = lookup_ip(ip) if ip else ("N/A", "N/A")

    users[email]["email"] = email
    users[email]["events"].append({
        "event": row["event"],
        "timestamp": row["timestamp"].isoformat() if pd.notnull(row["timestamp"]) else "N/A",
        "ip": ip or "N/A",
        "location": location,
        "isp": isp,
        "ua": row["user_agent"] or "N/A",
    })

users = {email: u for email, u in users.items() if len(u["events"]) > 0}
log_success("User data build complete.")

# ---------- STATS ----------
log_action("Generating statistics...")
emails_sent_df = df[df["event"] == "Email Sent"]
total_targets = emails_sent_df["email"].nunique()
sent_count = len(emails_sent_df)
open_count = len(df[df["event"] == "Email Opened"])
click_count = len(df[df["event"] == "Clicked Link"])
submit_count = len(df[df["event"] == "Submitted Data"])

users_opened_only = 0
users_opened_and_clicked = 0
users_opened_clicked_submitted = 0

for u in users.values():
    ev = [e["event"] for e in u["events"]]
    if "Submitted Data" in ev:
        users_opened_clicked_submitted += 1
    elif "Clicked Link" in ev:
        users_opened_and_clicked += 1
    elif "Email Opened" in ev:
        users_opened_only += 1

timeline = defaultdict(int)
for t in df["timestamp"].dropna():
    bucket = t.floor("h").strftime("%Y-%m-%d %H:%M")
    timeline[bucket] += 1

timeline_sorted = sorted(timeline.items())
timeline_labels = [t[0] for t in timeline_sorted]
timeline_raw = [datetime.strptime(t[0], "%Y-%m-%d %H:%M").isoformat() for t in timeline_sorted]
timeline_counts = [t[1] for t in timeline_sorted]

ua_counter = Counter(df["user_agent"].dropna())
ua_labels = list(ua_counter.keys())
ua_counts = list(ua_counter.values())

# ---------- BUILD CREDENTIALS TABLE ----------
fieldnames = set()
for c in df["credentials"].dropna():
    for k, _ in c:
        fieldnames.add(k)
fieldnames = sorted(fieldnames)

credentials_rows = []
for _, row in df[df["event"] == "Submitted Data"].iterrows():
    creds = row["credentials"]
    if creds:
        cred_dict = {k: v for k, v in creds}
        row_data = {
            "timestamp": row["timestamp"].isoformat() if pd.notnull(row["timestamp"]) else "N/A",
            "ip": row["ip"] or "N/A",
            "location": lookup_ip(row["ip"])[0] if row["ip"] else "N/A",
            "isp": lookup_ip(row["ip"])[1] if row["ip"] else "N/A",
            "fields": [cred_dict.get(f, "N/A") for f in fieldnames]
        }
        credentials_rows.append(row_data)

# ---------- HTML ----------
html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>GoPhish Campaign Report</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script src="https://cdn.jsdelivr.net/npm/luxon@3.4.3/build/global/luxon.min.js"></script>
<style>
    body { font-family: Arial, sans-serif; margin: 40px; }
    table { 
        border-collapse: collapse; 
        width: 100%; 
        margin-bottom: 40px; 
        table-layout: auto;
    }
    th, td {
        border: 1px solid #ccc;
        padding: 8px;
        text-align: left;
        vertical-align: middle;
        word-wrap: break-word;
    }
    th { background-color: #f2f2f2; }
    .masked, .unmasked { 
        display: inline-block;
        width: 100%; 
        overflow: visible;
        word-wrap: break-word;
    }
    .unmasked { display: none; }
    button.toggle-btn { 
        border: none; 
        background: none; 
        font-size: 16px; 
        cursor: pointer; 
    }
</style>
</head>
<body>

<h1>GoPhish Campaign Report</h1>

<h2>Executive Summary</h2>
<ul>
    <li><strong>Total Targets:</strong> {{ total_targets }}</li>
    <li><strong>Emails Sent:</strong> {{ sent_count }}</li>
    <li><strong>Emails Opened:</strong> {{ open_count }}</li>
    <li><strong>Links Clicked:</strong> {{ click_count }}</li>
    <li><strong>Data Submitted:</strong> {{ submit_count }}</li>
</ul>

<label for="timezone-select"><strong>Select Timezone:</strong></label>
<select id="timezone-select">
    {% for tz in timezone_options %}
    <option value="{{ tz }}">{{ tz }}</option>
    {% endfor %}
</select>

<h2>Charts</h2>
<div class="chart-container">
    <canvas id="eventChart"></canvas>
</div>
<div class="chart-container">
    <canvas id="userSummary"></canvas>
</div>
<div class="chart-container">
    <canvas id="timelineChart"></canvas>
</div>
<div class="chart-container">
    <canvas id="uaChart"></canvas>
</div>

{% if credentials_rows %}
<h2>Captured Credentials</h2>
<p>
    <button onclick="toggleAllPasswords(true)">🔓 Show All</button>
    <button onclick="toggleAllPasswords(false)">🔒 Hide All</button>
</p>
<table>
    <tr>
        <th>Time</th>
        {% for f in fieldnames %}
        <th>{{ f }}</th>
        {% endfor %}
        <th>IP</th>
        <th>Location</th>
        <th>ISP</th>
    </tr>
    {% for cred in credentials_rows %}
    <tr>
        <td class="datetime" data-utc="{{ cred.timestamp }}">{{ cred.timestamp }}</td>
        {% for val in cred.fields %}
        <td>
            <span class="masked">********</span>
            <span class="unmasked">{{ val }}</span>
        </td>
        {% endfor %}
        <td>{{ cred.ip }}</td>
        <td>{{ cred.location }}</td>
        <td>{{ cred.isp }}</td>
    </tr>
    {% endfor %}
</table>
{% endif %}

<h2>Per-User Details</h2>
{% for user in users %}
<h3>{{ user.email }}</h3>
<h4>Event Timeline:</h4>
<table>
    <tr>
        <th>Time</th>
        <th>Event</th>
        <th>IP</th>
        <th>Location</th>
        <th>ISP</th>
        <th>User Agent</th>
    </tr>
    {% for e in user.events %}
    <tr>
        <td class="datetime" data-utc="{{ e.timestamp }}">{{ e.timestamp }}</td>
        <td>{{ e.event }}</td>
        <td>{{ e.ip }}</td>
        <td>{{ e.location }}</td>
        <td>{{ e.isp }}</td>
        <td>{{ e.ua }}</td>
    </tr>
    {% endfor %}
</table>
{% endfor %}

<script>
function toggleAllPasswords(show) {
    document.querySelectorAll(".masked").forEach(masked => {
        var unmasked = masked.nextElementSibling;
        masked.style.display = show ? "none" : "inline-block";
        unmasked.style.display = show ? "inline-block" : "none";
    });
}

var rawTimes = {{ timeline_raw | tojson }};
var currentTZ = document.getElementById("timezone-select").value || "UTC";
var convertedLabels = rawTimes.map(dt => {
    var lux = luxon.DateTime.fromISO(dt, { zone: "utc" });
    return lux.setZone(currentTZ).toFormat("yyyy-LL-dd HH:mm");
});

var timelineCtx = document.getElementById('timelineChart').getContext('2d');
var timelineChart = new Chart(timelineCtx, {
    type: 'line',
    data: {
        labels: convertedLabels,
        datasets: [{
            label: 'Events Over Time',
            data: {{ timeline_counts | tojson }},
            backgroundColor: 'rgba(54, 162, 235, 0.2)',
            borderColor: 'rgba(54, 162, 235, 1)',
            fill: true,
            tension: 0.3
        }]
    }
});

document.getElementById("timezone-select").addEventListener("change", function() {
    var tz = this.value;
    document.querySelectorAll(".datetime").forEach(elem => {
        var origUTC = elem.getAttribute("data-utc");
        if (!origUTC || origUTC === "N/A") return;
        var dt = luxon.DateTime.fromISO(origUTC, { zone: "utc" });
        if (dt.isValid) {
            elem.textContent = dt.setZone(tz).toFormat("yyyy-LL-dd HH:mm:ss ZZZZ");
        } else {
            elem.textContent = "Invalid DateTime";
        }
    });
    var converted = rawTimes.map(dt => {
        var lux = luxon.DateTime.fromISO(dt, { zone: "utc" });
        return lux.setZone(tz).toFormat("yyyy-LL-dd HH:mm");
    });
    timelineChart.data.labels = converted;
    timelineChart.update();
});

new Chart(document.getElementById('eventChart').getContext('2d'), {
    type: 'pie',
    data: {
        labels: ['Emails Opened', 'Links Clicked', 'Data Submitted'],
        datasets: [{ data: [{{ open_count }}, {{ click_count }}, {{ submit_count }}],
            backgroundColor: ['#FFCE56', '#FF6384', '#4BC0C0'] }]
    }
});

new Chart(document.getElementById('userSummary').getContext('2d'), {
    type: 'bar',
    data: {
        labels: ['Opened Only', 'Opened + Clicked', 'Opened + Clicked + Submitted'],
        datasets: [{ label: 'Users',
            data: [{{ users_opened_only }}, {{ users_opened_and_clicked }}, {{ users_opened_clicked_submitted }}],
            backgroundColor: ['#FFCE56', '#FF6384', '#4BC0C0'] }]
    }
});

new Chart(document.getElementById('uaChart').getContext('2d'), {
    type: 'bar',
    data: {
        labels: {{ ua_labels | tojson }},
        datasets: [{
            label: 'User Agents Seen',
            data: {{ ua_counts | tojson }},
            backgroundColor: 'rgba(153, 102, 255, 0.6)'
        }]
    },
    options: {
        indexAxis: 'y',
        scales: { x: { beginAtZero: true } }
    }
});
</script>

</body>
</html>
"""

template = Template(html_template)

rendered = template.render(
    total_targets=total_targets,
    sent_count=sent_count,
    open_count=open_count,
    click_count=click_count,
    submit_count=submit_count,
    users_opened_only=users_opened_only,
    users_opened_and_clicked=users_opened_and_clicked,
    users_opened_clicked_submitted=users_opened_clicked_submitted,
    timeline_labels=timeline_labels,
    timeline_raw=timeline_raw,
    timeline_counts=timeline_counts,
    ua_labels=ua_labels,
    ua_counts=ua_counts,
    credentials_rows=credentials_rows,
    users=list(users.values()),
    timezone_options=TIMEZONE_OPTIONS,
    fieldnames=fieldnames
)

with open(OUTPUT_HTML, "w") as f:
    f.write(rendered)

log_success(f"Report saved: {OUTPUT_HTML}")
