# Author: Sharanya Ram

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
import tempfile
from urllib.parse import urlparse, parse_qs

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

def amazon_asin(driver, make, model):
    '''Returns asin of product to search items more easily!'''
    driver.get("https://www.amazon.com")
    time.sleep(3)

    search_box = driver.find_element(By.ID, "twotabsearchtextbox")
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

def costco_product_details(driver, make, model):
    driver.get("https://www.costco.com")

    wait = WebDriverWait(driver, 20)

    search_box = wait.until(
        EC.presence_of_element_located((By.ID, "search-field"))
    )

    search_box.clear()
    search_box.send_keys(f"{make} {model}")
    search_box.send_keys(Keys.RETURN)

    data = {
        "name": "Product not found",
        "make": make,
        "model": model,
        "price": "null",
        "merchant sin": "null",
        "sku": "null",
        "site": "Costco",
        "date": datetime.now(ZoneInfo("America/New_York"))
    }

    try:
        # First product tile
        first_product = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div.product-tile-set div.product")
            )
        )

        # Click the product link inside the tile
        product_link = first_product.find_element(By.TAG_NAME, "a")
        product_link.click()

        # Product title
        title = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "h1")
            )
        ).text

        # Try to get price (may not exist)
        try:
            price = wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "[data-testid='price']")
                )
            ).text
        except:
            price = "Login required"

        data.update({
            "name": title,
            "price": price
        })

    except TimeoutException as e:
        print(f"Timeout while processing {make} {model}: {e}")
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

    driver = webdriver.Chrome(options=options)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),
        options=options)
    driver.get("https://example.com")
    input("Press Enter to close")
    driver.quit()
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
                    else:
                        print(f"Amazon product not found: {make} {model}")
                elif "bestbuy" in site:
                    data = bestbuy_product_details(driver, make, model)
                if "costco" in site:
                    data = costco_product_details(driver, make, model)

                data_list.append(data)
                time.sleep(2)
            except Exception as e:
                print(f"Error processing {make} {model}: {e}")


                data_list.append(data)

            time.sleep(2)

    driver.quit()
    # Save results to CSV
    df = pd.DataFrame(data_list)
    df.to_csv("amazon_products.csv", index=False)
    print(df)

if __name__ == "__main__":
    main()