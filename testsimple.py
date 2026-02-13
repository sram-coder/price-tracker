import requests
from bs4 import BeautifulSoup
import time
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


def get_first_asin(query, session):
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
    response = session.get(product_url)

    if "captcha" in response.text.lower():
        print("CAPTCHA detected on product page")
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    price_whole = soup.select_one("span.a-price-whole")
    price_fract = soup.select_one("span.a-price-fraction")

    if price_whole and price_fract:
        whole = price_whole.text.replace(",", "").strip()
        fraction = price_fract.text.strip()
        price = f"{whole}{fraction}"
        return float(price)
    return None

def main():
    ua = UserAgent(browsers=['chrome', 'firefox'])

    headers = {
        'User-Agent': ua.random,
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
        'Accept': 'application/json',
    }

    session = requests.Session()
    session.headers.update(headers)
    urls, products = open_json()

    data_rows = []

    for product in products:
        print(f"\nSearching: {product}")

        asin = get_first_asin(product, session, product["make"], product["model"])
        if not asin:
            print("No ASIN found.")
            continue

        print("ASIN:", asin)

        time.sleep(2)

        price = amazon_product_details(asin, session)
        if not price:
            print("Price not found.")
            continue

        print("Price:", price)

        timestamp = datetime.now()

        data_rows.append({
            "timestamp": timestamp,
            "product_query": product,
            "asin": asin,
            "price": price
        })

        time.sleep(2)


        if data_rows:
            today = datetime.now()
            dir_path = f"products_data"
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