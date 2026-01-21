''''# price_scraper.py
#import requests
from bs4 import BeautifulSoup
from curl_cffi import requests
import pandas as pd

def get_general_category(soup, title):
    # 1) Try breadcrumb
    breadcrumb = soup.select("div#wayfinding-breadcrumbs_container ul li a")
    if breadcrumb:
        return breadcrumb[0].get_text(strip=True)

    # 2) Try Best Sellers Rank → category link
    rank_label = soup.find(string=lambda s: s and "Best Sellers Rank" in s)
    if rank_label:
        li = rank_label.find_parent("li")
        if li:
            links = li.select("a")
            if links:
                return links[0].get_text(strip=True)

    # 3) Infer from title keywords
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

    # 4) Final fallback
    return "Other"

#website url
url = ("https://www.amazon.com/dp/B0FN9NWW62")

#http request
webpage = requests.get(url, impersonate="chrome")
soup = BeautifulSoup(webpage.content, 'html.parser')

# Title
title_tag = soup.select_one("span#productTitle")
product_title = title_tag.get_text(strip=True) if title_tag else "Unknown Title"

# Price
price_whole_tag = soup.select_one("div#corePriceDisplay_desktop_feature_div span.a-price-whole")
price_fraction_tag = soup.select_one("span.a-price-fraction")
if price_whole_tag and price_fraction_tag:
    product_price_whole = price_whole_tag.get_text(strip=True).replace(",", "")
    product_price_fraction = price_fraction_tag.get_text(strip=True)
    product_price = float(product_price_whole + product_price_fraction)
else:
    product_price = 0.0

# Category
category = get_general_category(soup, product_title)

data = {
    "title": product_title,
    "price": product_price,
    "url": url,
    "category": category
}

print("title:", product_title)
print("price: $", product_price)
print("url:", url)
print("category:", category)'''

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
from datetime import datetime
from zoneinfo import ZoneInfo
import json

def get_general_category(soup_text, title):
    # Breadcrumb
    if "breadcrumb" in soup_text.lower():  # simplified check
        # for simplicity, return 'Electronics' if breadcrumb exists
        return "Electronics"

    # Keyword inference from title
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
    return "Other"


# --- Selenium setup ---
chrome_options = Options()
chrome_options.add_argument("--headless")  # run in background
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--lang=en-US")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# --- List of product URLs ---
with open('website-url.json', 'r') as file:
    urls = json.load(file)

with open('products-list.json', 'r') as file:
    products = json.load(file)

data_list = []

for url in urls:
    driver.get(url)
    time.sleep(3)  # wait for page to load fully

    # Grab title
    try:
        title = driver.find_element(By.ID, "productTitle").text.strip()
    except:
        title = "Unknown Title"

    # Grab price
    try:
        price_whole = driver.find_element(By.CSS_SELECTOR,
                                          "div#corePriceDisplay_desktop_feature_div span.a-price-whole").text.replace(
            ",", "")
        price_fraction = driver.find_element(By.CSS_SELECTOR, "span.a-price-fraction").text
        price = float(f"{price_whole}.{price_fraction}")
    except:
        price = 0.0

    # Grab category
    soup_text = driver.page_source
    category = get_general_category(soup_text, title)

    data_list.append({
        "product name": product,
        "title": title,
        "price": price,
        "url": url,
        "category": category,
        "date":datetime.now(ZoneInfo("America/New_York"))
    })

driver.quit()

# --- Save to CSV ---
df = pd.DataFrame(data_list)
df.to_csv("amazon_products.csv", index=False)

print(df)