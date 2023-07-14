# Script to import existing dashboard into Apache Superset
#
# Adapted from:
# https://github.com/apache/superset/issues/20288

import requests
import sys

zip_file = './dashboard_export.zip'
username = 'admin'
password = sys.argv[1]
clickhouse_password = sys.argv[2]

base_url = 'http://localhost:8088'

while True:
    try:
        response = requests.get(base_url, timeout=10)
        response.raise_for_status()
        break
    except Exception:
        pass

login_url = f"{base_url}/login/"
session = requests.Session()

payload = {}
headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Accept-Language': 'en-US,en;q=0.9'
}

response = session.request("GET", login_url, headers=headers, data=payload)
csrf_token = response.text.split('<input id="csrf_token" name="csrf_token" type="hidden" value="')[1].split('">')[0]

# Perform login

payload = f'csrf_token={csrf_token}&username={username}&password={password}'
headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Content-Type': 'application/x-www-form-urlencoded'}

session.request("POST", login_url, headers=headers, data=payload, allow_redirects=False)
cookie = session.cookies.get_dict().get('session')
print(session.cookies.get_dict())


# Get access token
api_url = f"{base_url}/api/v1/security/login"
payload = {
    "password": password, 
    "provider": "db",
    "refresh": True,
    "username": "admin"
}
responseToken = requests.post(api_url, json=payload)
access_token = responseToken.json()['access_token']

# Import dashboards

import_dashboard_url = f"{base_url}/api/v1/dashboard/import/"

with open(zip_file, 'rb') as f:
    payload = {
        'passwords': '{"databases/ClickHouse_-_Twitter.yaml":"ck_password"}',
        'overwrite': 'true'
    }
    files = [
        ('formData', ('dashboards.zip', f, 'application/zip'))
    ]
    headers = {
        'Authorization': f"Bearer {access_token}",
        'Accept': 'application/json',
        'Cookie': f'session={cookie}',
        'X-CSRFToken': csrf_token
    }

    response = requests.request("POST", import_dashboard_url, headers=headers, data=payload, files=files)

print(response.text)