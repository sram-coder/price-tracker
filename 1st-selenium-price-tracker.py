# Author: Sharanya Ram
import os
import json, time, csv, pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import re


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

def initialize_asins(products, session, json_path):
    updated = False

    for product in products:
        if product.get("asin"):
            continue  # Skip if ASIN already exists

        query = f"{product['make']} {product['model']}"
        print(f"Finding ASIN for: {query}")

        asin = get_first_asin(query, session)

        if asin:
            print("Found:", asin)
            product["asin"] = asin
            updated = True
            time.sleep(2)
        else:
            print("ASIN not found.")

    if updated:
        with open(json_path, "w") as file:
            json.dump({"products": products}, file, indent=2)
        print("JSON updated with ASINs.")
def amazon_asin(driver, make, model):
    '''Returns asin of product to search items more easily!'''
    driver.get("https://www.amazon.com/ref=nav_logo")
    time.sleep(3)

    search_box = driver.find_element(By.CSS_SELECTOR, "input#twotabsearchtextbox")
    search_box.send_keys(f"{make} {model}")
    search_box.send_keys(Keys.ENTER)

    results = WebDriverWait(driver, 15).until(
        EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, 'div[data-component-type="s-search-result"]')))

    for result in results:
        asin = result.get_attribute("data-asin")
        if asin:
            return asin  # first valid ASIN
    return None

def amazon_product_details(driver, make, model, asin):
    """
    Searches Amazon for make + model and returns the first product's details.
    """
    driver.get(f"https://www.amazon.com/dp/{asin}")
    content = driver.page_source
    data = {
        "name": "Product not found",
        "make": make,
        "model": model,
        "price": "null",
        "merchant sin": asin,
        "sku":"null",
        "site": "Amazon",
        "date": datetime.now(ZoneInfo("America/New_York"))

    }

    try:
            WebDriverWait(driver, 10).until(
            EC.url_contains("/dp/"))
            title_el = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "productTitle")))
            title = title_el.text
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "span.a-price-whole"))
            )
            try:
                whole_price = driver.find_element(By.CSS_SELECTOR, "span.a-price-whole").text
                fraction_price = driver.find_element(By.CSS_SELECTOR, "span.a-price-fraction").text
                price = f"{whole_price}.{fraction_price}"
            except:
                price = "N/A"

            data = {
                "name": title,
                "make": make,
                "model": model,
                "price": price,
                "merchant sin": asin,
                "sku":"null",
                "site": "Amazon",
                "date": datetime.now(ZoneInfo("America/New_York"))
            }

    except TimeoutException:
        print(f"Timeout while processing {make} {model}")

    return data


def bestbuy_product_details(driver, make, model):
    """
    Searches Best Buy for make + model and returns the first product's details.
    """
    driver.get("https://www.bestbuy.com")

    search_box = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.ID, "autocomplete-search-bar"))
    )


    search_box.clear()
    search_box.send_keys(f"{make} {model}")
    search_box.send_keys(Keys.ENTER)

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

    try:
            wait = WebDriverWait(driver, 60)
            print("1")
            first_result = wait.until(EC.element_to_be_clickable((By.XPATH, "(//a[contains(@href, '/product/')])[1]")))
            print("2")
            first_result.click()
            print("3")
            # wait for product page
            #time.sleep(5)
            title = wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "h1.h4")
                )
            ).text
            print("4:"+title)

            price = (wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "span.font-sans.text-default.text-style-body-md-400.font-500.text-7.leading-7")
                )
            )).text
            print("5")



            url = driver.current_url

            bsin_match = re.search(r"/product/[^/]+/([^/]+)/sku", url)
            bsin = bsin_match.group(1) if bsin_match else None

            sku_match = re.search(r"/sku/(\d+)", url)
            sku = sku_match.group(1) if sku_match else None

            data = {
                    "name": title,
                    "make": make,
                    "model": model,
                    "price": price,
                    "merchant sin": bsin,
                    "sku": sku,
                    "site": "BestBuy",
                    "date": datetime.now(ZoneInfo("America/New_York"))
                }

    except TimeoutException as e:
        print(f"Timeout while processing {make} {model}:{e}")
    except Exception as e:
        print(f"Error while processing {make} {model}: {e}")
    return data


def main():
    """Main function for running the Amazon price scraper."""

    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--disable-session-crashed-bubble")
    options.add_argument("--disable-restore-session-state")
    options.add_argument("--incognito")


    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),
        options=options)

    data_list = []
    urls, products = open_json()

    for product in products.get("products", []):
        make = product.get("make", "")
        model = product.get("model", "")

        for site in urls.get("urls", []):
            data = {
                        "name": "Product not found",
                        "make": make,
                        "model": model,
                        "price": "null",
                        "merchant sin": "null",
                        "sku": "null",
                        "site": "null",
                        "date": datetime.now(ZoneInfo("America/New_York"))
            }

            try:
                if "amazon" in site:
                    asin = amazon_asin(driver, make, model)
                    if asin:
                        data = amazon_product_details(driver, make, model, asin)
                        data_list.append(data)

                elif "bestbuy" in site:
                    data = bestbuy_product_details(driver, make, model)
                    data_list.append(data)


            except Exception as e:
                print(f"Error processing {make} {model}: {e}")




            time.sleep(2)

    driver.quit()
    # Save results to CSV
    today = datetime.now()
    dir_path = f"products_data"  # e.g., products_info_2/2/2026
    os.makedirs(dir_path, exist_ok=True)
    file_path = f"{dir_path}/{today.strftime('%Y-%m-%d')}.csv"
    df = pd.DataFrame(data_list)
    df.to_csv(file_path, index=False)
    print(df)

if __name__ == "__main__":
    main()