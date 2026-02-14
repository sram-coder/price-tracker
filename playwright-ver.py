import os
import json
import time
import re
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

def read_json_file(file_path):
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except json.JSONDecodeError:
        print(f"Error decoding JSON file: {file_path}")
        return {}


def open_json():
    urls = read_json_file("website-url.json")
    products = read_json_file("products-list.json")
    return urls, products

def amazon_asin(page, make, model):
    query = f"{make} {model}"
    print(f"Searching Amazon for: {query}")

    page.goto("https://www.amazon.com/")
    page.wait_for_selector("#twotabsearchtextbox")

    page.fill("#twotabsearchtextbox", query)
    page.press("#twotabsearchtextbox", "Enter")

    try:
        page.wait_for_selector('div[data-component-type="s-search-result"]', timeout=15000)
        results = page.query_selector_all('div[data-component-type="s-search-result"]')

        for result in results:
            asin = result.get_attribute("data-asin")
            if asin:
                return asin

    except PlaywrightTimeout:
        print("Amazon search timeout")

    return None


def amazon_product_details(page, make, model, asin):
    url = f"https://www.amazon.com/dp/{asin}"
    print(f"Opening product page: {url}")
    page.goto(url)


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

    page.goto(url)

    # CAPTCHA detection
    if "captcha" in page.url.lower():
        print("CAPTCHA detected on Amazon")
        return data

    try:
        page.wait_for_selector("#productTitle", timeout=10000)
        title = page.inner_text("#productTitle").strip()

        # Try multiple price selectors (Amazon changes these often)
        price = "N/A"
        try:
            page.wait_for_selector("span.a-price", timeout=8000)

            price_block = page.query_selector("span.a-price")

            whole = price_block.query_selector("span.a-price-whole")
            fraction = price_block.query_selector("span.a-price-fraction")

            if whole:
                whole_price = whole.inner_text().strip()
                whole_price = whole_price.replace("\n", "").replace(".", "").strip()

                if fraction:
                    fraction_price = fraction.inner_text().strip()
                    price = f"{whole_price}.{fraction_price}"
                else:
                    price = whole_price
            else:
                price = "N/A"

        except:
            print(f"Product {make} {model} not found")

        data.update({
            "name": title,
            "price": price
        })

    except PlaywrightTimeout:
        print(f"Timeout loading product: {make} {model}")

    return data


def bestbuy_product_details(page, make, model):
    query = f"{make} {model}"
    print(f"Searching BestBuy for: {query}")

    data = {
        "name": "Product not found",
        "make": make,
        "model": model,
        "price": "null",
        "merchant sin": "null",
        "sku": "null",
        "site": "BestBuy",
        "date": datetime.now(ZoneInfo("America/New_York"))
    }

    page.goto("https://www.bestbuy.com")
    page.wait_for_selector("#autocomplete-search-bar")

    page.fill("#autocomplete-search-bar", query)
    page.press("#autocomplete-search-bar", "Enter")

    try:
        page.wait_for_selector("a[href*='/product/']", timeout=15000)

        first_result = page.query_selector("a[href*='/product/']")
        first_result.click()

        page.wait_for_selector("h1", timeout=15000)
        title = page.inner_text("h1").strip()

        # Price selector may change — adjust if needed
        price = page.inner_text("span[aria-hidden='true']").strip()

        url = page.url

        bsin_match = re.search(r"/product/[^/]+/([^/]+)/sku", url)
        bsin = bsin_match.group(1) if bsin_match else None

        sku_match = re.search(r"/sku/(\d+)", url)
        sku = sku_match.group(1) if sku_match else None

        data.update({
            "name": title,
            "price": price,
            "merchant sin": bsin,
            "sku": sku
        })

    except PlaywrightTimeout:
        print(f"Timeout while processing {make} {model}")

    return data

def main():

    urls, products = open_json()
    data_list = []

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False  # Start headful first
        )

        context = browser.new_context()
        page = context.new_page()

        for product in products.get("products", []):
            make = product.get("make", "")
            model = product.get("model", "")

            for site in urls.get("urls", []):

                try:
                    if "amazon" in site:
                        asin = amazon_asin(page, make, model)
                        if asin:
                            data = amazon_product_details(page, make, model, asin)
                            data_list.append(data)

                    elif "bestbuy" in site:
                        data = bestbuy_product_details(page, make, model)
                        data_list.append(data)

                except Exception as e:
                    print(f"Error processing {make} {model}: {e}")

                time.sleep(3)

        browser.close()

    # Save CSV
    today = datetime.now()
    os.makedirs("products_data", exist_ok=True)
    file_path = f"products_data/{today.strftime('%Y-%m-%d')}.csv"

    df = pd.DataFrame(data_list)
    df.to_csv(file_path, index=False)
    print(df)


if __name__ == "__main__":
    main()
