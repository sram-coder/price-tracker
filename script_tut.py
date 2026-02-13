from seleniumwire import webdriver
from seleniumwire.utils import decode as decodesw
import json


def show_request_url(driver, target_url):
    driver.get(target_url)
    urls = []
    for request in driver.requests:
        urls.append({"url": request.url})
    return urls

def main():
    driver = webdriver.Firefox(seleniumwire_options={"disable_encoding":True})
    target_url = "https://www.amazon.com/Apple-Bluetooth-Headphones-Personalized-Effortless/dp/B0DGHMNQ5Z/ref=sr_1_1_sspa?sr=8-1-spons&sp_csd=d2lkZ2V0TmFtZT1zcF9hdGY"
    urls = show_request_url(driver, target_url)
    for url in urls:
        print(url)

if __name__ == "__main__":
    main()