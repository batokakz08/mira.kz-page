import argparse
import json

from api import chat, image_part, parse_json

PROMPT = """Look at this photo of clothes.
List only items you can see clearly. Do not invent items, brands or sizes.
Return a JSON array and nothing else. Each item:
{"name": "short name", "color": "main colour", "material": "if visible, else unknown",
 "style": "casual / smart / sport / street / formal", "warmth": 1,
 "confidence": "high / medium / low", "note": "short detail"}
warmth: 1 = very light (t-shirt), 3 = medium (hoodie), 5 = very warm (winter coat).
Use 2 to 12 items."""


def main():
    parser = argparse.ArgumentParser(description="Turn a photo of clothes into a wardrobe list.")
    parser.add_argument("photo", help="path to the photo")
    args = parser.parse_args()

    message = {
        "role": "user",
        "content": [
            {"type": "text", "text": PROMPT},
            image_part(args.photo),
        ],
    }
    print(json.dumps(parse_json(chat([message], max_tokens=4000, thinking=True)), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
