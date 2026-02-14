import requests
from pprint import pprint
from dotenv import load_dotenv
import os

def main():
    load_dotenv()  # Load environment variables from .env file

    username = os.getenv("API_USERNAME")
    password = os.getenv("API_PASSWORD")

    if not username or not password:
        raise ValueError("API credentials not found in .env file.")

    # Structure payload.
    payload = {
        'source': 'amazon_product',
        'query': 'B07FZ8S74R',
        'geo_location': '90210',
        'parse': True
    }

    # Get response.
    response = requests.request(
        'POST',
        'https://realtime.oxylabs.io/v1/queries',
        auth=(username, password),
        json=payload,
        )

    # Print prettified response to stdout.
    pprint(response.json())

if __name__ == '__main__':
    main()