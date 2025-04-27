from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Load credentials and IDs from environment variables
TENANT_ID = os.environ.get("TENANT_ID")
CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
DATASET_ID = os.environ.get("DATASET_ID")
WORKSPACE_ID = os.environ.get("WORKSPACE_ID")

def get_access_token():
    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    body = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "https://analysis.windows.net/powerbi/api/.default"
    }
    response = requests.post(url, headers=headers, data=body)
    response.raise_for_status()
    return response.json()["access_token"]

def run_dax_query(dax_query, access_token):
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{WORKSPACE_ID}/datasets/{DATASET_ID}/executeQueries"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    body = {
        "queries": [{"query": dax_query}],
        "serializerSettings": {"includeNulls": True}
    }
    response = requests.post(url, headers=headers, json=body)
    response.raise_for_status()
    return response.json()

@app.route('/query', methods=['POST'])
def query_powerbi():
    try:
        request_data = request.get_json()
        dax_query = request_data.get('query')

        if not dax_query:
            return jsonify({"error": "No DAX query provided."}), 400

        access_token = get_access_token()
        results = run_dax_query(dax_query, access_token)

        return jsonify({"result": results})

    except requests.exceptions.HTTPError as http_err:
        return jsonify({"error": "Bad DAX query or Power BI API error.", "details": str(http_err)}), 400

    except Exception as err:
        return jsonify({"error": "Unexpected server error.", "details": str(err)}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
