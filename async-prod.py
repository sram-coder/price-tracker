import os, json, pandas as pd, asyncio, aiohttp
from dotenv import load_dotenv
from datetime import datetime
from zoneinfo import ZoneInfo

semaphore = asyncio.Semaphore(10)   # limits concurrent requests
API_URL = "https://realtime.oxylabs.io/v1/queries"


def read_json_file(file_path):
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def open_json():
    urls = read_json_file("website-url.json")
    products = read_json_file("products-list.json")
    return urls, products


async def fetch_oxylabs(session, payload, username, password):
    """Generic Oxylabs request"""
    auth = aiohttp.BasicAuth(username, password)

    for attempt in range(3):  # retry up to 3 times
        async with semaphore:
            async with session.post(API_URL, json=payload, auth=auth) as response:

                if response.status == 429:
                    wait = 2 ** attempt
                    print(f"Rate limited. Retrying in {wait}s...")
                    await asyncio.sleep(wait)
                    continue

                if response.status != 200:
                    print("Request failed:", response.status)
                    print(await response.text())
                    return None

                return await response.json()

    print("Max retries reached.")
    return None


async def amazon_product_details(make, model, session, username, password):
    payload = {
        "source": "amazon_search",
        "domain": "com",
        "query": f"{make} {model}",
        "start_page": 1,
        "pages": 1,
        "parse": True
    }

    data = await fetch_oxylabs(session, payload, username, password)
    if not data:
        return None

    try:
        result = data["results"][0]["content"]["results"]["organic"][0]

        return {
            "name": result["title"],
            "make": make,
            "model": model,
            "price": result.get("price"),
            "merchant_sin": result.get("asin"),
            "sku": "null",
            "rating": result.get("rating"),
            "reviews_count": result.get("reviews_count"),
            "sales_volume": result.get("sales_volume"),
            "site": "Amazon",
            "date": datetime.now(ZoneInfo("America/New_York")).isoformat()
        }

    except Exception:
        return None


async def walmart_product_details(make, model, session, username, password):
    payload = {
        "source": "walmart_search",
        "domain": "com",
        "query": f"{make} {model}",
        "parse": True
    }

    data = await fetch_oxylabs(session, payload, username, password)
    if not data:
        return None

    try:
        products = data["results"][0]["content"]["results"]

        filtered = [
            p for p in products
            if "restored" not in p.get("general", {}).get("title", "").lower()
        ]

        if not filtered:
            return None

        p = filtered[0]

        return {
            "name": p["general"]["title"],
            "make": make,
            "model": model,
            "price": p["price"]["price"],
            "merchant_sin": p["general"]["product_id"],
            "sku": "null",
            "rating": p["rating"]["rating"],
            "reviews_count": p["rating"]["count"],
            "sales_volume": "null",
            "site": "Walmart",
            "date": datetime.now(ZoneInfo("America/New_York")).isoformat()
        }

    except Exception:
        return None


async def target_product_details(make, model, session, username, password):
    payload = {
        "source": "target_search",
        "query": f"{make} {model}",
        "render": "html",
        "parse": True
    }

    data = await fetch_oxylabs(session, payload, username, password)
    if not data:
        return None

    try:
        r = data["results"][0]["content"]["results"]["organic"][0]

        return {
            "name": r["title"],
            "make": make,
            "model": model,
            "price": r["price_data"]["price"],
            "merchant_sin": r["product_id"],
            "sku": "null",
            "rating": r["rating_data"]["score"],
            "reviews_count": r["rating_data"]["count"],
            "sales_volume": "null",
            "site": "Target",
            "date": datetime.now(ZoneInfo("America/New_York")).isoformat()
        }

    except Exception:
        return None


async def main():
    load_dotenv()

    username = os.getenv("API_USERNAME")
    password = os.getenv("API_PASSWORD")

    urls, products = open_json()
    tasks = []

    async with aiohttp.ClientSession() as session:

        for product in products.get("products", []):
            make = product.get("make", "")
            model = product.get("model", "")

            for site in urls.get("urls", []):

                if "amazon" in site.lower():
                    tasks.append(
                        amazon_product_details(make, model, session, username, password)
                    )

                elif "walmart" in site.lower():
                    tasks.append(
                        walmart_product_details(make, model, session, username, password)
                    )

                elif "target" in site.lower():
                    tasks.append(
                        target_product_details(make, model, session, username, password)
                    )

        results = await asyncio.gather(*tasks, return_exceptions=True)

    data_list = [r for r in results if r and not isinstance(r, Exception)]

    os.makedirs("products_data", exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    file_path = f"products_data/{today}.csv"

    df = pd.DataFrame(data_list)
    df.to_csv(file_path, index=False)

    print(df)


if __name__ == "__main__":
    asyncio.run(main())