import os, json, time, pandas as pd
from pprint import pprint
from dotenv import load_dotenv
from datetime import datetime
from zoneinfo import ZoneInfo
import certifi
import urllib3
import asyncio
import aiohttp

def read_json_file(file_path):
    """Reads a JSON file and returns a dictionary."""
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except json.JSONDecodeError:
        print(f"Error decoding JSON file: {file_path}")
        return {}


def open_json():
    """Opens the JSON files and returns urls and products dictionaries."""
    urls = read_json_file("website-url.json")
    products = read_json_file("products-list.json")
    return urls, products


async def target_product_details(make, model, session, username, password, location):
    '''Returns product details from Oxylabs Target API using search query make and model.
    Arguments:
        make: Brand of product
        model: Product name
        username: Username for Oxylabs API
        password: Password for Oxylabs API
        location: Zip code for store location, used as part of payload for API request'''
    payload = {
        'source': 'target_search',
        'query': f'{make} {model}',
        'render': 'html',
        'parse': True
    }
    auth = aiohttp.BasicAuth(username, password)

    async with session.post(url, json=payload, auth=auth) as response:
        if response.status != 200:
            print("Request failed:", response.status)
            print(await response.text())
            return None

        data = await response.json()
    title = "null"
    price = "null"
    merchant_sin = "null"
    rating = "null"
    reviews_count = "null"

    if response.status_code != 200:
        print("Request failed:", response.status_code)
        print(response.text)
        return None
    print(response.headers)

    data = response.json()
    results = data["results"][0]
    first_result = results["content"]["results"]["organic"][0]
    pretty_json = json.dumps(first_result, indent=4)
    print(pretty_json)
    title = first_result["title"]
    price = first_result["price_data"]["price"]
    merchant_sin = first_result["product_id"]
    reviews_count = first_result["rating_data"]["count"]
    rating = first_result["rating_data"]["score"]

    data_list = {
        "name": title,
        "make": make,
        "model": model,
        "price": price,
        "merchant_sin": merchant_sin,
        "sku": "null",
        "rating": rating,
        "reviews_count": reviews_count,
        "sales_volume": "null",
        "site": "Target",
        "date": datetime.now(ZoneInfo("America/New_York"))
    }
    return data_list


async def amazon_product_details(make, model, session, username, password, location):
    '''Returns product details from Oxylabs Amazon API using search query make and model.
    Arguments:
        make: Brand of product
        model: Product name
        username: Username for Oxylabs API
        password: Password for Oxylabs API
        location: Zip code for store location, used as part of payload for API request'''
    payload = {
        'source': 'amazon_search',
        'domain': 'com',
        'query': f'{make} {model}',
        'start_page': 1,
        'pages': 1,
        'parse': True
    }

    response = requests.post(
        'https://realtime.oxylabs.io/v1/queries',
        auth=(username, password),
        json=payload,
    )

    if response.status_code != 200:
        print("Request failed:", response.status_code)
        print(response.text)
        return None
    # print(response.headers)

    data = response.json()
    results = data["results"][0]
    pretty_json = json.dumps(data, indent=4)
    # print(pretty_json)
    organic_results = results.get("content", {}).get("results", {}).get("organic", [])
    first_result = organic_results[0]
    # print(organic_results)
    # print(first_result)
    title = first_result["title"]
    price = first_result["price"]
    asin = first_result["asin"]
    rating = first_result["rating"]
    reviews_count = first_result["reviews_count"]
    sales_volume = first_result["sales_volume"]
    if sales_volume == None:
        sales_volume = "null"

    data = {
        "name": title,
        "make": make,
        "model": model,
        "price": price,
        "merchant_sin": asin,
        "sku": "null",
        "rating": rating,
        "reviews_count": reviews_count,
        "sales_volume": sales_volume,
        "site": "Amazon",
        "date": datetime.now(ZoneInfo("America/New_York"))
    }

    return data


async def walmart_product_details(make, model, session, username, password, location):
    '''Returns product details from Oxylabs Walmart API using search query make and model.
    Arguments:
        make: Brand of product
        model: Product name
        username: Username for Oxylabs API
        password: Password for Oxylabs API
        location: Zip code for store location, used as part of payload for API request'''
    payload = {
        'source': 'walmart_search',
        'domain': 'com',
        'query': f'{make} {model}',
        'parse': True
    }

    response = requests.post(
        'https://realtime.oxylabs.io/v1/queries',
        auth=(username, password),
        json=payload,
    )
    title = "null"
    price = "null"
    merchant_sin = "null"
    rating = "null"
    reviews_count = "null"

    if response.status_code != 200:
        print("Request failed:", response.status_code)
        print(response.text)
        return None
    # print(response.headers)

    data = response.json()
    results = data["results"][0]
    # pretty_json = json.dumps(data, indent=4)
    # print(pretty_json)
    # product_results = first_job_result["content"]["results"]
    # print(json.dumps(product_results, indent=4))
    if "results" in data and data["results"]:
        first_job_result = data["results"][0]
        content = first_job_result.get("content", {})
        product_results = content.get("results", [])

        filtered_products = [
            product for product in product_results
            if "restored" not in product.get("general", {}).get("title", "").lower()
        ]

        if filtered_products:
            product = filtered_products[0]
            title = product.get("general", {}).get("title", "No title")
            price = product.get("price", {}).get("price", 0)
            merchant_sin = product.get("general", {}).get("product_id")
            rating = product.get("rating", {}).get("rating", 0)
            reviews_count = product.get("rating", {}).get("count", 0)
        else:
            print("No non-restored products found.")
    else:
        print("No 'results' key or empty list in API response.")
    data_list = {
        "name": title,
        "make": make,
        "model": model,
        "price": price,
        "merchant_sin": merchant_sin,
        "sku": "null",
        "rating": rating,
        "reviews_count": reviews_count,
        "sales_volume": "null",
        "site": "Walmart",
        "date": datetime.now(ZoneInfo("America/New_York"))
    }
    return data_list

#do not use
def bestbuy_product_details(make, model, username, password, location):
    '''Returns product details from Oxylabs Best Buy API using search query make and model.
    Arguments:
        make: Brand of product
        model: Product name
        username: Username for Oxylabs API
        password: Password for Oxylabs API
        location: Zip code for store location, used as part of payload for API request'''
    proxies = {
        'http': f'http://{username}:{password}@realtime.oxylabs.io:60000',
        'https': f'https://{username}:{password}@realtime.oxylabs.io:60000'
    }

    headers = {
        'x-oxylabs-user-agent-type': 'desktop_chrome',
        'x-oxylabs-geo-location': f'{location}',
        'X-Oxylabs-Render': 'html',
    }
    urllib3.disable_warnings()

    payload = {
        'source': 'bestbuy_search',
        'domain': 'com',
        'query': f'{make} {model}',
        'parse': True,
        'render': 'html',
    }

    response = requests.request(
        'POST',
        'https://realtime.oxylabs.io/v1/queries',
        auth=(username, password),
        json=payload,
        headers=headers,  # Pass the defined headers.
        verify=False,  # Accept our certificate.
        proxies=proxies,
    )

    if response.status_code != 200:
        print("Request failed:", response.status_code)
        print(response.text)
        return None
    print(response.headers)

    data = response.json()
    pretty_json = json.dumps(data, indent=4)
    # print(pretty_json)


async def main():
    load_dotenv()  # Load environment variables from .env file

    username = os.getenv("API_USERNAME")
    password = os.getenv("API_PASSWORD")
    location = os.getenv("GEOLOCATION")

    if not username or not password:
        raise ValueError("API credentials not found in .env file.")
    data_list = []
    urls, products = open_json()

    tasks = []
    async with aiohttp.ClientSession() as session:

        for product in products.get("products", []):
            make = product.get("make", "")
            model = product.get("model", "")
            for site in urls.get("urls", []):
                try:
                    if "amazon" in site.lower():
                        tasks.append(
                            amazon_product_details(make, model, session, username, password, location)
                        )
                        data_list.append(result)
                    if "walmart" in site.lower():
                        tasks.append(
                            walmart_product_details(make, model, session, username, password, location)
                        )
                        data_list.append(result)
                    if "target" in site.lower():
                        tasks.append(
                            target_product_details(make, model, session, username, password, location)
                        )
                        data_list.append(result)
                except Exception as e:
                    print(f"Error processing {make} {model}: {e}")
                    # Append default on error
                    data_list.append({
                        "name": "Product not found",
                        "make": make,
                        "model": model,
                        "price": "null",
                        "merchant_sin": "null",
                        "sku": "null",
                        "site": site,
                        "date": datetime.now(ZoneInfo("America/New_York"))
                    })

                    results = await asyncio.gather(*tasks, return_exceptions=True)


                for result in results:
                    if result and not isinstance(result, Exception):
                        data_list.append(result)

    today = datetime.now()
    dir_path = f"products_data"  # e.g., products_info_2/2/2026
    os.makedirs(dir_path, exist_ok=True)
    file_path = f"{dir_path}/{today.strftime('%Y-%m-%d')}.csv"
    df = pd.DataFrame(data_list)
    df.to_csv(file_path, index=False)
    print(df)

if __name__ == "__main__":
    asyncio.run(main())