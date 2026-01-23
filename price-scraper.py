import json
import time
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager


def get_general_category(soup_text, title):
    if "breadcrumb" in soup_text.lower():
        return "Electronics"

    title_lower = title.lower()

    if any(k in title_lower for k in [
        "laptop", "desktop", "computer", "monitor", "ssd", "ram",
        "keyboard", "mouse", "headphones", "earbuds", "tablet", "pc"
    ]):
        return "Electronics"

    if any(k in title_lower for k in [
        "shirt", "pants", "dress", "jacket", "hoodie", "jeans"
    ]):
        return "Clothing"

    if any(k in title_lower for k in [
        "book", "novel", "paperback", "hardcover", "kindle"
    ]):
        return "Books"

    if any(k in title_lower for k in [
        "furniture", "sofa", "chair", "table", "bed"
    ]):
        return "Home & Kitchen"

    return "Category not found"


def read_json_file(file_path):
    with open(file_path, "r") as file:
        return json.load(file)


def open_json():
    urls = read_json_file("website-url.json")
    products = read_json_file("products-list.json")
    return urls, products


def main():
    chrome_options = Options()

    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--lang=en-US")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options,
    )

    driver.set_page_load_timeout(30)

    data_list = []
    urls, products = open_json()

    for product in products["products"]:
        make = product["make"]
        model = product["model"]

        for url in urls["urls"]:
            full_url = f"https://{url}"

            try:
                driver.get(full_url)
            except TimeoutException:
                print(f"Timed out loading {full_url}, skipping")
                continue

            time.sleep(2)

            soup_text = driver.page_source
            category = get_general_category(soup_text, model)

            data_list.append({
                "product name": f"{make} {model}",
                "make": make,
                "model": model,
                "url": full_url,
                "category": category,
                "date": datetime.now(ZoneInfo("America/New_York")),
            })

    driver.quit()

    df = pd.DataFrame(data_list)
    df.to_csv("amazon_products.csv", index=False)
    print(df)


if __name__ == "__main__":
    main()
