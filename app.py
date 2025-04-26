from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

import os

TENANT_ID = os.environ.get("TENANT_ID")
CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")


def get_access_token():
    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    headers = { "Content-Type": "application/x-www-form-urlencoded" }
    body = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "https://analysis.windows.net/powerbi/api/.default"
    }
    response = requests.post(url, headers=headers, data=body)
    return response.json()["access_token"]

@app.route('/query', methods=['POST'])
def query_powerbi():
    user_query = request.json.get('query')

    access_token = get_access_token()

    # **Later**, here is where you would actually query Power BI with DAX
    return jsonify({"result": f"You asked: {user_query}. Real data fetching coming soon!"})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
