# https://realpython.com/api-integration-in-python/
# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)

examples = [
        {"retailer": "ebay", "price": "50$", "discount":"50%", "used": "yes"},
        {"retailer": "amazon", "price": "100$", "discount":"None", "used": "no"}
]

CORS(app)

def _find_next_id():
    return max(country["id"] for country in countries) + 1

@app.get("/hisense/75H5R1")
def get_countries():
    return jsonify(examples)

@app.post("/countries")
def add_country():
    if request.is_json:
        country = request.get_json()
        country["id"] = _find_next_id()
        countries.append(country)
        return country, 201
    return {"error": "Request must be JSON"}, 415

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
