#!/usr/bin/python3
import sys
import json
import time
import argparse
import datetime
import requests
import xmltodict
from typing import Dict, Tuple, Optional


class Sitemap:
    def __init__(self, base_url: str):
        if not base_url.startswith("http"):
            # add schema
            base_url = f"http://{base_url}"
        self.base = base_url
        self.catalog = dict()
        self.retry_wait_seconds = 3
        self.catalog = self.fetch_catalog()

    def fetch_catalog(self, *args: Tuple[Optional[str]]) -> Dict[str, str]:
        tries = 1
        while tries != 5:
            # keep trying until we get a response
            try:
                response = requests.request(
                    "GET",
                    f"{self.base}/sitemap_products_1.xml",
                    params={"from": 1, "to": 9999999999999},
                )
                break
            except Exception as exc:
                print(
                    f"[!] {datetime.datetime.now()} :: {exc} - Sleeping for {self.retry_wait_seconds} seconds then retrying request - trying {5-tries} more times"
                )
                tries += 1
                time.sleep(self.retry_wait_seconds)
        if tries == 5:
            print(
                f"[!] {datetime.datetime.now()} :: Giving up on updating catalog - using stale version this pass"
            )
            return self.catalog
        else:
            product_name_url_map = dict()
            response_content = response.content
            try:
                product_dict = xmltodict.parse(response_content)
            except Exception as exc:
                print(
                    f"[!] {datetime.datetime.now()} :: Unable to parse xml to dict - raw content: {response_content}\nNot parsing - using stale catalog"
                )

                return self.catalog
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
                        f"[!] {datetime.datetime.now()} :: Match - {product['image:image']['image:title']} - {product['loc']}"
                    )
                    tries = 1
                    while tries != 5:
                        try:
                            product_detail_json = requests.request(
                                "GET", f"{product['loc']}.json"
                            ).json()
                            break
                        except Exception as exc:
                            print(
                                f"[!] {datetime.datetime.now()} :: Unable to get json for product - trying {5-tries} more times"
                            )
                            tries += 1
                            time.sleep(1)
                    if tries == 5:
                        print(
                            f"[!] {datetime.datetime.now()} :: Giving up on json/details of matching product"
                        )
                    else:
                        variants = product_detail_json["product"]["variants"]
                        for variant in variants:
                            print(
                                f"\t{variant['title']} :: {self.base}/cart/{variant['id']}:1"
                            )
                        print()
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
        print(
            f"{datetime.datetime.now()} :: {len(list(sitemap.catalog.keys()))} products cataloged..."
        )
        updated_catalog = sitemap.fetch_catalog(args.keyword)
        if updated_catalog != sitemap.catalog:
            # TODO - compare keys in updated_items
            #  ie. determine category for each: added item, removed item, edited item
            updated_items = set(updated_catalog.items()) ^ set(sitemap.catalog.items())
            for item in updated_items:
                current_changed_product_name = item[0]
                current_changed_product_url = item[1]
                if current_changed_product_name in list(
                    sitemap.catalog.keys()
                ) and current_changed_product_name in list(updated_catalog.keys()):
                    # item in both old and new catalog - url must have been updated/edited
                    print(
                        f"[!] {datetime.datetime.now()} :: [{current_changed_product_name}] url was UPDATED -> {current_changed_product_url}"
                    )
                elif current_changed_product_name in list(updated_catalog.keys()):
                    # item is in the new catalog but not the old one - new item added
                    print(
                        f"[!] {datetime.datetime.now()} :: [{current_changed_product_name}] item was ADDED -> {current_changed_product_url}"
                    )
                else:
                    # item not in both updated and old, and not only in updated catalog - must be removed
                    print(
                        f"[!] {datetime.datetime.now()} :: [{current_changed_product_name}] item was REMOVED -> {current_changed_product_url}"
                    )
            # print(f"{datetime.datetime.now()} :: Updated items: {updated_items}")
        sitemap.catalog = updated_catalog
        time.sleep(args.poll)
