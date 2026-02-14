import requests
from bs4 import BeautifulSoup
import time
from zoneinfo import ZoneInfo
from datetime import datetime
import pandas as pd
import os
import random
import csv
import json
from fake_useragent import UserAgent


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


def amazon_asin(query, session):
    search_url = f"https://www.amazon.com/s?k={query.replace(' ', '+')}"
    response = session.get(search_url)

    if "captcha" in response.text.lower():
        print("CAPTCHA detected on search page")
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    results = soup.find_all("div", {"data-component-type": "s-search-result"})

    for result in results:
        asin = result.get("data-asin")
        if asin:
            return asin

    return None

def amazon_product_details(asin, session, make, model):
    product_url = f"https://www.amazon.com/dp/{asin}"
    time.sleep(random.uniform(3, 6))
    response = session.get(product_url)

    if "captcha" in response.text.lower():
        print("CAPTCHA detected on product page")
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    data = {
        "name": "Product not found",
        "make": make,
        "model": model,
        "price": "null",
        "merchant sin": asin,
        "sku": "null",
        "site": "Amazon",
        "date": datetime.now(ZoneInfo("America/New_York"))
    }

    try:
        # FIXED TITLE SELECTOR
        title_el = soup.select_one("#productTitle")
        if title_el:
            data["name"] = title_el.text.strip()

        # SAFER PRICE EXTRACTION
        price_el = soup.select_one("span.a-offscreen")
        if price_el:
            raw_price = price_el.text.strip()
            clean_price = raw_price.replace("$", "").replace(",", "")
            data["price"] = clean_price

    except Exception as e:
        print(f"Error processing {make} {model}: {e}")

    return data

def main():
    ua = UserAgent(browsers=['chrome', 'firefox'])

    headers = {
        'User-Agent': ua.random,
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
    }

    session = requests.Session()
    session.headers.update(headers)

    urls, products_data = open_json()
    products = products_data["products"]

    data_rows = []

    for product in products:
        make = product["make"]
        model = product["model"]
        query = f"{make} {model}"

        print(f"\nSearching: {query}")

        asin = amazon_asin(query, session)
        if not asin:
            print("No ASIN found.")
            continue

        print("ASIN:", asin)

        time.sleep(2)

        product_data = amazon_product_details(asin, session, make, model)
        if not product_data:
            print("Product data not found.")
            continue

        print("Price:", product_data["price"])

        data_rows.append(product_data)

        time.sleep(2)

    # Save once after loop
    if data_rows:
        today = datetime.now()
        dir_path = "products_data"
        os.makedirs(dir_path, exist_ok=True)

        file_path = f"{dir_path}/{today.strftime('%Y-%m-%d')}.csv"

        df = pd.DataFrame(data_rows)

        if os.path.exists(file_path):
            df.to_csv(file_path, mode="a", header=False, index=False)
        else:
            df.to_csv(file_path, index=False)

        print(f"\nSaved to {file_path}")
if __name__ == "__main__":
    main()