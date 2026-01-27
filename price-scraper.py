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
        "asin": asin,
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
            title = driver.find_element(By.ID, "productTitle").text
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
                "asin": asin,
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
        "asin": "null",
        "date": datetime.now(ZoneInfo("America/New_York"))

    }

    try:
            wait = WebDriverWait(driver, 20)
            first_result = wait.until(EC.element_to_be_clickable((By.XPATH, "(//a[contains(@href, '/product/')])[1]")))
            first_result.click()
            title_el = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-component-name='ProductHeader'] h1")))
            title = title_el.text
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-sticky-media-gallery] .priceView-hero-price span"))
            )
            
            try:
                price = driver.find_element(By.CSS_SELECTOR, "[data-sticky-media-gallery] .priceView-hero-price span").text
            except:
                price = "null"

            data = {
                "name": title,
                "make": make,
                "model": model,
                "price": price,
                "asin": "null",
                "date": datetime.now(ZoneInfo("America/New_York"))
            }

    except TimeoutException:
        print(f"Timeout while processing {make} {model}")

    return data



def main():
    """Main function for running the Amazon price scraper."""
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--lang=en-US")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),
        options=chrome_options)

    data_list = []
    urls, products = open_json()

    for product in products.get("products", []):
        make = product.get("make", "")
        model = product.get("model", "")

        for site in urls.get("urls", []):

            if "amazon" in site:
                asin = amazon_asin(driver, make, model)
                if asin:
                    data = amazon_product_details(driver, make, model, asin)
                else:
                    data = {
                        "name": "Product not found",
                        "make": make,
                        "model": model,
                        "price": "null",
                        "asin": asin,
                        "sku": "null",
                        "date": datetime.now(ZoneInfo("America/New_York"))
                    }
                data_list.append(data)

            elif "bestbuy" in site:
                data = bestbuy_product_details(driver, make, model)
            else:
                data = {
                        "name": "Product not found",
                        "make": make,
                        "model": model,
                        "price": "null",
                        "asin": "null",
                        "date": datetime.now(ZoneInfo("America/New_York"))
                    }
                data_list.append(data)

            time.sleep(2)

    driver.quit()
    # Save results to CSV
    df = pd.DataFrame(data_list)
    df.to_csv("amazon_products.csv", index=False)
    print(df)

if __name__ == "__main__":
    main()