from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

TENANT_ID = os.environ.get("TENANT_ID")
CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
WORKSPACE_ID = os.environ.get("WORKSPACE_ID")
DATASET_ID = os.environ.get("DATASET_ID")

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

def run_dax_query(dax_query, access_token):
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{WORKSPACE_ID}/datasets/{DATASET_ID}/executeQueries"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    body = {
        "queries": [
            {
                "query": dax_query
            }
        ],
        "serializerSettings": {
            "includeNulls": True
        }
    }
    response = requests.post(url, headers=headers, json=body)

    print("Status Code:", response.status_code)
    print("Power BI response text:", response.text)

    if response.status_code != 200:
        return {"error": f"Power BI API error. Status: {response.status_code}, Body: {response.text}"}

    return response.json()

@app.route('/query', methods=['POST'])
def query_powerbi():
    user_query = request.json.get('query')

    access_token = get_access_token()

    dax_query = """
    EVALUATE
    SELECTCOLUMNS(
        'Master Items Sales Analysis by',
        "Customer", 'Master Items Sales Analysis by'[CUSTOMER_NUMBER],
        "Invoice", 'Master Items Sales Analysis by'[INVOICE_NUMBER]
    )
    """

    results = run_dax_query(dax_query, access_token)

    return jsonify(results)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
