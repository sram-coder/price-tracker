import os, json, pandas as pd
import asyncio, aiohttp
from dotenv import load_dotenv
from datetime import datetime
from zoneinfo import ZoneInfo
import requests
import pprint

semaphore = asyncio.Semaphore(5)   # limits concurrent requests
API_URL = "https://realtime.oxylabs.io/v1/queries"


def read_json_file(file_path):
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def open_json():
    urls = read_json_file("website-url.json")
    products = read_json_file("productslist2.json")
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


async def amazon_product_details(make, session, username, password, id, location):
    payload = {
        'source': 'amazon_product',
        'domain': 'com',
        'query': id,
        'parse': True,
        'geo_location': location,
        'context': [
            {'key': 'autoselect_variant',
             'value': True}
        ],

    }
    headers = {
        'x-oxylabs-geo-location': location
    }
    async with session.post(
            "https://realtime.oxylabs.io/v1/queries",
            auth=aiohttp.BasicAuth(username, password),
            json=payload,
            headers=headers

    ) as response:
        data = await response.json()
    if not data:
        return None
    try:
        result = data["results"][0]["content"]
        title = (result.get("product_name") or result.get("title"))
        price= result.get("price")
        return {
            "title":title,
            "make": make,
            "price":price,
            "merchant_sin": result.get("asin"),
            "rating": result.get("rating"),
            "reviews_count": result.get("reviews_count"),
            "sales_volume": result.get("sales_volume"),
            "site": "Amazon",
            "date": datetime.now(ZoneInfo("America/New_York")).isoformat()
        }

    except Exception as e:
        print("PARSE ERROR:", e)
        print(json.dumps(data, indent=2)[:500])
        return None


async def walmart_product_details(make, session, username, password, id, location):
    payload = {
        'source': 'walmart_product',
        'domain': 'com',
        'product_id': id,
        'parse': True,
        'geo_location': location,

    }
    headers = {
        'x-oxylabs-geo-location': location
    }
    async with session.post(
            "https://realtime.oxylabs.io/v1/queries",
            auth=aiohttp.BasicAuth(username, password),
            json=payload,
            headers=headers

    ) as response:
        data = await response.json()
    if not data:
        return None
    try:
        result = data["results"][0]["content"]
        title = result["general"]["title"]
        price= result["price"]["price"]
        rating = result["rating"]["rating"]
        review_count = result["rating"]["count"]
        return {
            "title":title,
            "make": make,
            "price":price,
            "merchant_sin": id,
            "rating": rating,
            "reviews_count": review_count,
            "sales_volume":None,
            "site": "Walmart",
            "date": datetime.now(ZoneInfo("America/New_York")).isoformat()
        }

    except Exception as e:
        print("PARSE ERROR:", e)
        print(json.dumps(data, indent=2)[:500])
        return None

async def target_product_details(make, session, username, password, id, location):
    payload = {
        'source': 'target_product',
        'product_id': id,
        'parse': True,
        'geo_location': location,

    }
    headers = {
        'x-oxylabs-geo-location': location
    }
    # data = await fetch_oxylabs(session, payload, username, password)
    async with session.post(
            "https://realtime.oxylabs.io/v1/queries",
            auth=aiohttp.BasicAuth(username, password),
            json=payload,
            headers=headers

    ) as response:
        data = await response.json()
    if not data:
        return None
    try:
        result = data["results"]
        print(json.dumps(result, indent=4))
        title = result.get("content").get("title")
        price = result.get("content").get("price").get("current")
        rating = result.get("content").get("rating").get("score")
        review_count = result.get("content").get("rating").get("count")
        return {
            "title": title,
            "make": make,
            "price": price,
            "merchant_sin": id,
            "rating": rating,
            "reviews_count": review_count,
            "sales_volume": None,
            "site": "Target",
            "date": datetime.now(ZoneInfo("America/New_York")).isoformat()
        }

    except Exception as e:
        print("PARSE ERROR:", e)
        print(json.dumps(data, indent=2)[:500])
        return None


async def main():
    load_dotenv()


    username = os.getenv("API_USERNAME")
    password = os.getenv("API_PASSWORD")
    location = os.getenv("GEOLOCATION")
    urls, products = open_json()
    tasks = []

    async with aiohttp.ClientSession() as session:

        for product in products.get("products", []):
            make = product.get("make", "")
            walmart_id = product.get("Walmart ID", "")
            amazon_asin = product.get("Amazon ASIN", "")
            target_id = product.get("Target ID", "")

            for site in urls.get("urls", []):

                if "amazon" in site.lower():
                    tasks.append(
                        amazon_product_details(make, session, username, password, amazon_asin, location)
                    )


                elif "walmart" in site.lower():
                    tasks.append(
                        walmart_product_details(make, session, username, password, walmart_id, location)
                    )


                elif "target" in site.lower():
                    tasks.append(
                        target_product_details(make, session, username, password, target_id, location)
                    )

        results = await asyncio.gather(*tasks, return_exceptions=True)
        print("Total tasks:", len(tasks))
    data_list = [r for r in results if r and not isinstance(r, Exception)]

    os.makedirs("products_data", exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    file_path = f"products_data/{today}.csv"

    df = pd.DataFrame(data_list)
    df.to_csv(file_path, index=False)

    print(df)


if __name__ == "__main__":
    asyncio.run(main())