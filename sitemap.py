#!/usr/bin/python3
import sys
import json
import time
import argparse
import requests
import xmltodict
from typing import Dict, Tuple, Optional


class Sitemap:
    def __init__(self, base_url: str):
        if not base_url.startswith("http"):
            # add schema
            base_url = f"http://{base_url}"
        self.base = base_url
        self.product_map = self.fetch_product_map()

    def fetch_product_map(self, *args: Tuple[Optional[str]]) -> Dict[str, str]:
        response = requests.request(
            "GET",
            f"{self.base}/sitemap_products_1.xml",
            params={"from": 1, "to": 9999999999999},
        )
        product_name_url_map = dict()
        product_dict = xmltodict.parse(response.content)
        products = product_dict.get("urlset", {}).get("url")
        if products is None:
            return {}
        for product in product_dict["urlset"]["url"]:
            if product["loc"] in response.url:
                # filter out the root xml node
                continue
            if len(args) != 0 and args[0] is not None:
                # keyword argument supplied and passed here - break on find
                if args[0].lower() in product["image:image"]["image:title"].lower():
                    print(
                        f"[!] Match - {product['image:image']['image:title']} - {product['loc']}"
                    )
                    # TODO - print permalinks to stdout
            product_url = product["loc"]
            product_name = product.get("image:image", {}).get(
                "image:title", product_url.split("/")[-1]
            )
            product_name_url_map.update({product_name: product_url})
        # print(json.dumps(product_name_url_map, indent=4))
        return product_name_url_map


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url")
    parser.add_argument("--keyword")
    parser.add_argument("--poll", type=int, default=10)
    args = parser.parse_args()
    domains = ["com", "co", "it", "net", "org", "pl"]
    if args.base_url is None or not any(
        args.base_url.endswith(domain) for domain in domains
    ):
        print(
            f"Please specify a --base-url with any of the following domains: {domains}\nie. --base-url=shoppersparadise.com"
        )
        sys.exit()
    print(f"Parsing sitemap for: {args.base_url}")
    sitemap = Sitemap(args.base_url)

    while True:
        print(f"{len(list(sitemap.product_map.keys()))} products cataloged...")
        updated_product_map = sitemap.fetch_product_map(args.keyword)
        if updated_product_map != sitemap.product_map:
            updated_items = set(updated_product_map.items()) ^ set(
                sitemap.product_map.items()
            )
            print(f"Updated items: {updated_items}")
        sitemap.product_map = updated_product_map
        time.sleep(args.poll)
