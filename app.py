import os
import requests
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder="static", static_url_path="")

# Set this in Render's Environment Variables tab — do NOT hardcode your key here.
EBAY_APP_ID = os.environ.get("EBAY_APP_ID", "")

EBAY_FINDING_URL = "https://svcs.ebay.com/services/search/FindingService/v1"


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/search")
def search():
    if not EBAY_APP_ID:
        return jsonify({"error": "Server is missing EBAY_APP_ID. Set it in Render's Environment tab."}), 500

    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "Missing search query."}), 400

    params = {
        "OPERATION-NAME": "findItemsByKeywords",
        "SERVICE-VERSION": "1.0.0",
        "SECURITY-APPNAME": EBAY_APP_ID,
        "RESPONSE-DATA-FORMAT": "JSON",
        "REST-PAYLOAD": "",
        "keywords": query,
        "paginationInput.entriesPerPage": "25",
        "sortOrder": "PricePlusShippingLowest",
        "categoryId": "6030",
    }

    try:
        resp = requests.get(EBAY_FINDING_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Could not reach eBay: {str(e)}"}), 502

    root = data.get("findItemsByKeywordsResponse", [{}])[0]
    ack = root.get("ack", [None])[0]

    if ack not in ("Success", "Warning"):
        err_msg = "eBay API returned an error."
        try:
            err_msg = root["errorMessage"][0]["error"][0]["message"][0]
        except (KeyError, IndexError):
            pass
        return jsonify({"error": err_msg}), 502

    raw_items = root.get("searchResult", [{}])[0].get("item", [])

    items = []
    for it in raw_items:
        try:
            price = float(it["sellingStatus"][0]["currentPrice"][0]["__value__"])
        except (KeyError, IndexError, ValueError):
            continue

        ship_cost = None
        try:
            ship_cost = float(it["shippingInfo"][0]["shippingServiceCost"][0]["__value__"])
        except (KeyError, IndexError, ValueError):
            pass

        condition = "Not specified"
        try:
            condition = it["condition"][0]["conditionDisplayName"][0]
        except (KeyError, IndexError):
            pass

        seller = "Unknown seller"
        try:
            seller = it["sellerInfo"][0]["sellerUserName"][0]
        except (KeyError, IndexError):
            pass

        items.append({
            "title": it.get("title", [""])[0],
            "price": price,
            "shipping": ship_cost,
            "condition": condition,
            "seller": seller,
            "url": it.get("viewItemURL", [""])[0],
            "image": it.get("galleryURL", [""])[0],
        })

    return jsonify({"items": items, "count": len(items)})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
