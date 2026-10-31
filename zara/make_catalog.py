"""Turn zara_products.json files into a virtual-stylist catalog (same format as KNOWLEDGE/koton-live.json).

Usage (on your laptop, after zara_search.py):
    python make_catalog.py women zara-live.json  tops_w.json jeans_w.json jackets_w.json
    python make_catalog.py men   zara-live-men.json  tops_m.json jeans_m.json

Each input is one zara_products.json that you renamed after a search. The output has
shop, audience, checked (today), source, products (id, name, url, image, price, old_price, color, hex,
stock, category), errors and stale, like the Koton and Qazaq Republic files. Category comes from the
Zara product family: верх, низ, платье, слой, аксессуар. Shoes and unknown families are skipped and
counted in "errors" (the app has no shoes slot).
"""
import datetime
import json
import sys
import time

CATEGORY = [  # first match wins; words from Zara's family names (Russian store)
    ("слой", ["КУРТК", "ПАЛЬТО", "ПИДЖАК", "ЖАКЕТ", "БЛЕЙЗЕР", "ПУХОВИК", "ПАРК", "ТРЕНЧ", "КАРДИГАН", "ЖИЛЕТ",
              "БОМБЕР", "ВЕТРОВК", "ПЛАЩ", "ДУБЛЕНК", "ВЕРХНЯЯ"]),
    ("платье", ["ПЛАТЬ", "САРАФАН", "КОМБИНЕЗОН"]),
    ("низ", ["БРЮК", "ДЖИНС", "ЮБК", "ШОРТ", "ЛЕГИНС", "ЛОСИН"]),
    ("верх", ["ФУТБОЛК", "РУБАШК", "БЛУЗ", "ТОП", "СВИТЕР", "ДЖЕМПЕР", "ПОЛО", "ТОЛСТОВК", "ЛОНГСЛИВ", "СВИТШОТ",
              "ВОДОЛАЗК", "ХУДИ", "МАЙК", "КОРСЕТ", "БОДИ", "ТРИКОТАЖ"]),
    ("аксессуар", ["СУМК", "РЕМ", "ШАРФ", "ШАПК", "ПЛАТОК", "ПЕРЧАТК", "ОЧК", "УКРАШЕН", "СЕРЬГ", "ОЖЕРЕЛ", "БРАСЛЕТ"]),
]
SHOES = ["ОБУВ", "КРОССОВК", "БОТИН", "САПОГ", "ТУФЛ", "КЕД", "САНДАЛ", "ЛОФЕР", "МОКАСИН", "ШЛЕПАНЦ"]


MAX_PER_CATEGORY = 40  # keep Koton, Viled and Qazaq visible: the page picks at random from all shops together


def nice_name(name):
    """ФУТБОЛКА С ПРИНТОМ I LOVE NY® -> Футболка с принтом I LOVE NY® (Russian words in lower case, Latin words kept)."""
    words = [w.lower() if any("А" <= ch <= "я" or ch in "Ёё" for ch in w) else w for w in (name or "").split()]
    text = " ".join(words)
    return text[:1].upper() + text[1:]


def category_of(item):
    text = f"{item.get('family') or ''} {item.get('name') or ''}".upper()
    if any(w in text for w in SHOES):
        return None
    for cat, words in CATEGORY:
        if any(w in text for w in words):
            return cat
    return None


def main(audience, out, inputs):
    products, errors, seen = [], [], set()
    for path in inputs:
        for item in json.load(open(path, encoding="utf-8")):
            if not item.get("url") or not item.get("image") or not isinstance(item.get("price"), (int, float)):
                errors.append(f"{path}: no url, image or price: {item.get('name')}")
                continue
            if item["id"] in seen:
                continue
            cat = category_of(item)
            if cat is None:
                errors.append(f"{path}: skipped (shoes or unknown family): {item.get('family')} / {item.get('name')}")
                continue
            if sum(1 for p in products if p["category"] == cat) >= MAX_PER_CATEGORY:
                continue
            seen.add(item["id"])
            products.append({"shop": "Zara KZ", "id": str(item["id"]), "name": nice_name(item["name"]), "url": item["url"], "image": item["image"],
                             "price": int(round(item["price"])), "old_price": None, "color": (item.get("color") or "").lower(),
                             "hex": item.get("hex"), "stock": None, "category": cat})
    catalog = {"shop": "Zara KZ", "audience": audience, "checked": datetime.date.today().isoformat(),
               "fetched_at": int(time.time()), "source": "https://www.zara.com/kz/ru/ (saved by hand with zara_search.py)",
               "products": products, "errors": errors, "stale": False}
    json.dump(catalog, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    by_cat = {}
    for p in products:
        by_cat[p["category"]] = by_cat.get(p["category"], 0) + 1
    print(f"{out}: {len(products)} products {by_cat}, skipped {len(errors)}")


if __name__ == "__main__":
    if len(sys.argv) < 4 or sys.argv[1] not in ("women", "men"):
        sys.exit("usage: python make_catalog.py women|men OUT.json IN1.json [IN2.json ...]")
    main(sys.argv[1], sys.argv[2], sys.argv[3:])
