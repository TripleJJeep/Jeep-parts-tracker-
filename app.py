import os
import time
import base64
import requests
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder="static", static_url_path="")

# Set these in Render's Environment Variables tab — do NOT hardcode them here.
EBAY_CLIENT_ID = os.environ.get("EBAY_APP_ID", "")
EBAY_CLIENT_SECRET = os.environ.get("EBAY_CLIENT_SECRET", "")

OAUTH_URL = "https://api.ebay.com/identity/v1/oauth2/token"
BROWSE_SEARCH_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"

# eBay Motors Parts & Accessories category
CATEGORY_ID = "6030"

_token_cache = {"token": None, "expires_at": 0}


def get_access_token():
    now = time.time()
    if _token_cache["token"] and now < _token_cache["expires_at"] - 60:
        return _token_cache["token"]

    if not EBAY_CLIENT_ID or not EBAY_CLIENT_SECRET:
        raise RuntimeError("Missing EBAY_APP_ID or EBAY_CLIENT_SECRET environment variables.")

    credentials = f"{EBAY_CLIENT_ID}:{EBAY_CLIENT_SECRET}"
    b64creds = base64.b64encode(credentials.encode()).decode()

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {b64creds}",
    }
    data = {
        "grant_type": "client_credentials",
        "scope": "https://api.ebay.com/oauth/api_scope",
    }

    resp = requests.post(OAUTH_URL, headers=headers, data=data, timeout=15)
    resp.raise_for_status()
    payload = resp.json()

    _token_cache["token"] = payload["access_token"]
    _token_cache["expires_at"] = now + payload.get("expires_in", 7200)
    return _token_cache["token"]


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/search")
def search():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "Missing search query."}), 400

    try:
        token = get_access_token()
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Could not authenticate with eBay: {str(e)}"}), 502

    headers = {
        "Authorization": f"Bearer {token}",
        "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
    }

    used_only = request.args.get("used_only", "true").lower() == "true"

    params = {
        "q": query,
        "category_ids": CATEGORY_ID,
        "limit": "25",
        "sort": "price",
    }
    if used_only:
        params["filter"] = "conditionIds:{3000|4000|5000|6000|7000}"

    try:
        resp = requests.get(BROWSE_SEARCH_URL, headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.HTTPError as e:
        try:
            err_body = resp.json()
            err_msg = err_body.get("errors", [{}])[0].get("message", str(e))
        except Exception:
            err_msg = str(e)
        return jsonify({"error": f"eBay API error: {err_msg}"}), 502
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Could not reach eBay: {str(e)}"}), 502

    raw_items = data.get("itemSummaries", [])

    items = []
    for it in raw_items:
        try:
            price = float(it["price"]["value"])
        except (KeyError, ValueError, TypeError):
            continue

        ship_cost = None
        try:
            shipping_options = it.get("shippingOptions", [])
            if shipping_options:
                ship_val = shipping_options[0].get("shippingCost", {}).get("value")
                if ship_val is not None:
                    ship_cost = float(ship_val)
        except (ValueError, TypeError):
            pass

        items.append({
            "title": it.get("title", ""),
            "price": price,
            "shipping": ship_cost,
            "condition": it.get("condition", "Not specified"),
            "seller": it.get("seller", {}).get("username", "Unknown seller"),
            "url": it.get("itemWebUrl", ""),
            "image": it.get("image", {}).get("imageUrl", ""),
        })

    items.sort(key=lambda x: x["price"])

    return jsonify({"items": items, "count": len(items)})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
