# Gophish Report

Gophish Report is a Python tool for transforming raw Gophish CSV exports into interactive HTML reports. It visualises phishing campaign data, user interactions, IP geolocation details, and captured credentials. This enables security teams, penetration testers, and red teams to analyse Gophish results with precision.

---

## 📸 Screenshots

*Here’s what Gophish Report looks like in action:*

**Tool Running in CLI**

![Tool running in CLI](https://i.imgur.com/xK6R0ua.png)

---

**Timezone Selection Dropdown**

![Timezone selection dropdown](https://i.imgur.com/p5uFfCJ.png)

---

**Events Graph**

![Events graph](https://i.imgur.com/nQiKVGh.png)

---

**Events Over Time Graph**

![Events over time graph](https://i.imgur.com/fcg65m9.png)

---

**User-Agent Graph**

![User agent graph](https://i.imgur.com/00YqfLR.png)

---

**Captured Credentials Table**

![Captured credentials table](https://i.imgur.com/sWfgDSE.png)

---

**Per-User Events Timeline**

![Per-user events timeline](https://i.imgur.com/BSuHLcI.png)

---

## ✨ Features

✅ **Parses Gophish CSV Exports**
- Supports all core Gophish events:
  - Email Sent
  - Email Opened
  - Link Clicked
  - Submitted Data

✅ **Interactive HTML Report Generation**
- Generates a self-contained HTML report with:
  - **Executive Summary**
    - Total targets
    - Emails sent
    - Opens
    - Clicks
    - Data submissions
  - **Graphs and Visualisations**
    - Pie chart of email event breakdown
    - Bar chart showing user progression through phishing stages
    - Timeline chart of events over time
    - Horizontal bar graph of User-Agent distribution
  - **Per-User Activity Logs**
    - Full timeline of user events
    - Event timestamps
    - Source IP address
    - Geolocation (city, region, country)
    - ISP or Organisation
    - User-Agent
  - **Captured Credentials Table**
    - Displays all captured form fields from phishing payloads
    - Toggle to mask or unmask sensitive values
  - **Dynamic Timezone Support**
    - Converts timestamps into any selected timezone for clarity

✅ **IP Geolocation Lookup**
- Automatically queries public IP addresses to obtain:
  - City
  - Region
  - Country
  - ISP or Organisation
- Private and reserved IPs are excluded from lookup.
- Integrates with [ipinfo.io](https://ipinfo.io/) for reliable geolocation data.

✅ **Cross-Platform HTML Output**
- Opens in any modern web browser for easy sharing and analysis.

---

## 🚀 Installation (Linux)

To install Gophish Report from GitHub:

```bash
# Clone the repository
git clone https://github.com/intelligencegroup-io/gophish-report.git
cd gophish-report

# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**requirements.txt**

```
pandas==2.2.2
requests==2.31.0
jinja2==3.1.3
colorama==0.4.6
```

---

## 🌐 IP Lookup Configuration

Gophish Report uses [ipinfo.io](https://ipinfo.io/) to perform IP geolocation lookups on public IP addresses, providing details like city, region, country, and ISP or organisation.

- Sign up for a free ipinfo.io account: [https://ipinfo.io/signup](https://ipinfo.io/signup)
- The free plan offers 50,000 requests per month.

After signing up, you will receive an API token, for example `abcd123456efgh`.

---

### How to Add Your API Token

Open the Python script and locate this line near the top:

```python
IPINFO_TOKEN = "your_api_token_here"
```

Replace the placeholder with your token:

```python
IPINFO_TOKEN = "abcd123456efgh"
```

Once updated, the tool will use your token for all IP lookups.

---

**Note:**
- Private or reserved IP addresses, such as 192.168.x.x, are automatically excluded from lookups.
- Only public IPs are sent to ipinfo.io.

---

## ⚙️ Usage

Run the tool against a Gophish CSV export:

```bash
python3 gophish_report.py path/to/your_campaign.csv
```

Example output:

```
[ * ] Starting data processing...
[ + ] Reading CSV file...
[ ✔ ] CSV loaded. Rows: 871
[ + ] Extracting details...
[ * ] Extracting details... 200/871
[ * ] Extracting details... 400/871
[ * ] Extracting details... 600/871
[ * ] Extracting details... 800/871
[ * ] Extracting details... 871/871
[ ✔ ] Details extraction complete.
[ + ] Performing IP lookups...
[ * ] Performing IP lookups... 10/138
[ * ] Performing IP lookups... 20/138
[ * ] Performing IP lookups... 30/138
[ * ] Performing IP lookups... 40/138
[ * ] Performing IP lookups... 50/138
[ * ] Performing IP lookups... 60/138
[ * ] Performing IP lookups... 70/138
[ * ] Performing IP lookups... 80/138
[ * ] Performing IP lookups... 90/138
[ * ] Performing IP lookups... 100/138
[ * ] Performing IP lookups... 110/138
[ * ] Performing IP lookups... 120/138
[ * ] Performing IP lookups... 130/138
[ * ] Performing IP lookups... 138/138
[ ✔ ] IP lookup complete.
[ + ] Building user data...
[ ✔ ] User data build complete.
[ + ] Generating statistics...
[ ✔ ] Report saved: 20250706_235001.html

```

Your HTML report, for example `20250706_235001.html`, will be created in the same directory.

Open it in any browser for a fully interactive report.

---

## 📊 Data Included in Reports

The HTML report provides:

- **Campaign Metrics**
  - Total emails sent
  - Open rates
  - Click rates
  - Data submission rates

- **Time-Series Visualisations**
  - Hourly timeline of events

- **User-Agent Analysis**
  - Frequency of User-Agents observed

- **Detailed User Logs**
  - Event history per user
  - IP geolocation
  - ISP details
  - User-Agent strings

- **Captured Credentials**
  - Tabular view of submitted form data
  - Mask or unmask functionality for sensitive data

---

## 🔎 SEO Keywords

- gophish report generator
- gophish csv to html
- phishing campaign analytics
- gophish csv parser
- generate gophish report
- ip geolocation in phishing reports
- cybersecurity reporting tools
