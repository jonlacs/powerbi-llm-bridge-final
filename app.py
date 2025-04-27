from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Load environment variables
TENANT_ID = os.environ.get("TENANT_ID")
CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
DATASET_ID = os.environ.get("DATASET_ID")
WORKSPACE_ID = os.environ.get("WORKSPACE_ID")
CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY")

# Get Power BI Access Token
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

# Run DAX Query
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
    return response.json()

# Send to Claude
def ask_claude(prompt):
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": CLAUDE_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    body = {
        "model": "claude-3-sonnet-20240229",  # or claude-3-opus if you want even smarter but costs more
        "max_tokens": 500,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }
    response = requests.post(url, headers=headers, json=body)
    return response.json()["content"][0]["text"]

@app.route('/query', methods=['POST'])
def query_powerbi_and_claude():
    user_query = request.json.get('query')
    access_token = get_access_token()

    # Convert user query into a simple DAX (example only)
    dax_query = f"""
    EVALUATE
    TOPN(10,
        SUMMARIZE('Master Items Sales Analysis by',
            'Master Items Sales Analysis by'[CUSTOMER_NAME],
            "Revenue", SUM('Master Items Sales Analysis by'[LINE_TOTAL])
        ),
        [Revenue], DESC
    )
    """

    powerbi_results = run_dax_query(dax_query, access_token)

    # Build a text table for Claude
    table_text = "Customer Name | Revenue\n"
    table_text += "--------------------------\n"
    for row in powerbi_results["results"][0]["tables"][0]["rows"]:
        customer = row.get("CUSTOMER_NAME", "Unknown")
        revenue = row.get("Revenue", 0)
        table_text += f"{customer} | {revenue}\n"

    # Ask Claude
    final_prompt = f"""Here is the customer revenue data:\n\n{table_text}\n\nPlease analyze this information and summarize key insights, such as which customers are top buyers, any patterns you notice, and anything interesting."""
    claude_response = ask_claude(final_prompt)

    return jsonify({"answer": claude_response})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
