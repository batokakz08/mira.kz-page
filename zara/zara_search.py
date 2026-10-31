"""Search a Zara country store and save the products as JSON.

Usage:
    pip install playwright && python -m playwright install chromium
    python zara_search.py "t shirt from Zara kz"                  (women's section)
    python zara_search.py "t shirt from Zara kz" --section MAN    (men's section)

The script opens the Zara search page in a real Chromium browser, because
Zara blocks plain HTTP clients. It records the JSON responses that the page
gets from its own API, then finds the product objects in them.

Output:
    zara_raw.json       all JSON responses (use it to inspect the real schema)
    zara_products.json  name, price, URL and image for each product found
"""

import json
import re
import sys
from urllib.parse import quote

from playwright.sync_api import sync_playwright

PHRASE = re.compile(r"(?P<q>.+?)\s+from\s+zara\s+(?P<cc>[a-z]{2})\b", re.I)


def parse(text):
    m = PHRASE.match(text.strip())
    if not m:
        raise ValueError('Use the format: "<item> from Zara <country code>"')
    return m["q"].strip(), m["cc"].lower()


def find_products(node, found=None):
    """Walk any JSON tree and collect objects that look like products.

    Zara (checked 27 Oct 2026, KZ store 11749): the search API
    /api/storefront/2/stores/<store>/grids/search sends products in "components",
    each with identifier.id, name and pricing.price.current. The older format
    (id + name + price on one object) is still accepted."""
    if found is None:
        found = {}
    if isinstance(node, dict):
        ident = node.get("identifier")
        if isinstance(ident, dict) and "id" in ident and "name" in node and "pricing" in node:
            found.setdefault(ident["id"], node)
        elif "name" in node and "price" in node and "id" in node:
            found.setdefault(node["id"], node)
        for value in node.values():
            find_products(value, found)
    elif isinstance(node, list):
        for value in node:
            find_products(value, found)
    return found


def first_image(product):
    """Return the first image URL in a product object, if one exists."""
    stack = [product]
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            url = node.get("url")
            if isinstance(url, str) and "static.zara.net" in url:
                return url.replace("{width}", "750")
            stack.extend(node.values())
        elif isinstance(node, list):
            stack.extend(reversed(node))
    return None


def price_of(product):
    """Price in normal units (tenge). New format: value * 10**exponent; old format: minor units / 100."""
    cur = ((product.get("pricing") or {}).get("price") or {}).get("current")
    if isinstance(cur, dict) and isinstance(cur.get("value"), (int, float)):
        exp = (cur.get("currency") or {}).get("exponent", -2)
        return cur["value"] * 10 ** exp, (cur.get("currency") or {}).get("code")
    price = product.get("price")
    return (price / 100 if isinstance(price, (int, float)) else price), None


def summarize(product, cc, lang):
    seo = product.get("seo") or {}
    url = None
    if seo.get("keyword") and seo.get("seoProductId"):
        # keyword is already URL-encoded and ends with "-": Zara's own links look like ...i-love-ny--p03366100.html
        url = f"https://www.zara.com/{cc}/{lang}/{seo['keyword']}-p{seo['seoProductId']}.html"
        if seo.get("discernProductId"):
            url += f"?v1={seo['discernProductId']}"
    price, currency = price_of(product)
    ident = product.get("identifier") or {}
    return {
        "id": ident.get("id", product.get("id")),
        "name": product.get("name"),
        "price": price,
        "currency": currency,
        "color": (product.get("color") or {}).get("name"),
        "hex": (product.get("color") or {}).get("hexCode"),
        "family": ((product.get("classification") or {}).get("family") or {}).get("name"),
        "section": ((product.get("classification") or {}).get("section") or {}).get("name"),
        "url": url,
        "image": first_image(product),
    }


def zara_search(text, lang="ru", headless=False, section="WOMAN"):
    query, cc = parse(text)
    url = f"https://www.zara.com/{cc}/{lang}/search?searchTerm={quote(query)}&section={section}"
    payloads = []

    def on_response(resp):
        if "json" not in resp.headers.get("content-type", ""):
            return
        try:
            payloads.append({"url": resp.url, "data": resp.json()})
        except Exception:
            pass

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page(locale=f"{lang}-{cc.upper()}")
        page.on("response", on_response)
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_timeout(5000)
        for _ in range(5):  # scroll to load more results
            page.mouse.wheel(0, 4000)
            page.wait_for_timeout(1500)
        browser.close()

    found = {}
    for item in payloads:
        find_products(item["data"], found)
    products = [summarize(p, cc, lang) for p in found.values()]
    return url, payloads, products


if __name__ == "__main__":
    args = sys.argv[1:]
    section = "WOMAN"
    if "--section" in args:  # WOMAN (default), MAN or KID
        i = args.index("--section")
        section = args[i + 1].upper()
        del args[i:i + 2]
    phrase = " ".join(args) or "t shirt from Zara kz"
    url, payloads, products = zara_search(phrase, section=section)
    with open("zara_raw.json", "w", encoding="utf-8") as f:
        json.dump(payloads, f, ensure_ascii=False, indent=2)
    with open("zara_products.json", "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    print(f"Search page: {url}")
    print(f"JSON responses: {len(payloads)}, products: {len(products)}")
    for p in products[:20]:
        print(f"- {p['name']} | {p['price']} | {p['section']} | {p['url']}")
