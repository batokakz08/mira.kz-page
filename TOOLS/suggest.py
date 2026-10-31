import argparse
import json
import sys
from pathlib import Path

from api import chat, parse_json

KNOWLEDGE_PATH = Path(__file__).resolve().parent.parent / "KNOWLEDGE" / "style.md"


def load_knowledge():
    try:
        return KNOWLEDGE_PATH.read_text(encoding="utf-8")
    except OSError:
        return ""


def load_profile(path):
    file = Path(path)
    if not file.exists():
        return None
    try:
        data = json.loads(file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise SystemExit(f"Profile {path} is not valid JSON: {error}")
    return data if isinstance(data, dict) else None


def profile_text(profile):
    if not profile or not profile.get("color_type"):
        return ""
    palette = ", ".join(
        f"{item.get('name', '?')} {item.get('hex', '')}".strip()
        for item in profile.get("palette", [])
        if isinstance(item, dict)
    )
    return (
        f"User colour profile: {profile.get('color_type', 'unknown')} "
        f"(undertone: {profile.get('undertone', 'unknown')}, "
        f"contrast: {profile.get('contrast', 'unknown')}).\n"
        f"Palette: {palette or 'not given'}.\n"
        "Prefer these colours. If an item is outside the palette, mention it gently in watch_out, "
        "but do not refuse an item only because of its colour."
    )


def load_items(path):
    with open(path, encoding="utf-8") as file:
        data = json.load(file)
    items = data.get("items", data) if isinstance(data, dict) else data
    if not isinstance(items, list) or not items:
        raise SystemExit(f"No items in {path}. Use a JSON list or an object with an items list.")
    return items


def names_of(items):
    return [item.get("name") or item.get("item") or str(item) for item in items]


def main():
    parser = argparse.ArgumentParser(description="Build 3 outfits from clothes the user owns.")
    parser.add_argument("--wardrobe", required=True, help="wardrobe JSON file")
    parser.add_argument("--occasion", required=True, help="where the user is going")
    parser.add_argument("--weather", default="not given", help="city, temperature, wind or rain")
    parser.add_argument("--notes", default="", help="extra wishes, for example: no heels")
    parser.add_argument("--profile", default="profile.json", help="colour profile JSON (optional)")
    parser.add_argument("--style", default="универсальный", help="мужской, женский or универсальный")
    parser.add_argument("--vibe", default="без предпочтения", help="classic, casual, street or minimal")
    parser.add_argument("--count", type=int, default=3, help="number of outfits")
    args = parser.parse_args()

    items = load_items(args.wardrobe)
    names = names_of(items)
    knowledge = load_knowledge()
    colour = profile_text(load_profile(args.profile))
    prompt = f"""You are a stylist in Kazakhstan. Build {args.count} outfits from the user's wardrobe.
Occasion: {args.occasion}
Weather: {args.weather}
Wishes: {args.notes or "none"}
Use ONLY these items, with the exact names from this list:
{json.dumps(names, ensure_ascii=False)}
{colour}
Write why and watch_out in the same language as Occasion and Wishes (Russian for Russian input).
Style knowledge (use as defaults; the user's wishes win):
{knowledge or "Keep the outfit simple, use one focal point and match the weather."}
Return JSON only:
{{"outfits": [{{"name": "Safe", "items": ["exact name"], "why": "1-2 sentences", "watch_out": "one short warning"}}]}}
Name the outfits Safe, Sharper and Comfortable (or close translations).
Warm weather: one light layer. Cold weather: layers, warm shoes and a coat.
Never suggest buying anything. Never comment on the body or body shape.
If the wardrobe is missing something for the occasion, say so in watch_out."""

    answer = chat([{"role": "user", "content": prompt}], max_tokens=1500, thinking=False)
    result = parse_json(answer)
    if isinstance(result, list):
        result = {"outfits": result}
    outfits = result.get("outfits")
    if not isinstance(outfits, list) or not outfits:
        raise SystemExit("The model did not return any outfits:\n" + answer[:800])
    outfits = outfits[: args.count]
    labels = ["Safe", "Sharper", "Comfortable"]
    for outfit, label in zip(outfits, labels):
        outfit["name"] = label
    result = {"outfits": outfits}

    known = set(names)
    for outfit in result.get("outfits", []):
        unknown = [item for item in outfit.get("items", []) if item not in known]
        if unknown:
            print(
                "Warning: these items are not in the wardrobe: " + ", ".join(unknown),
                file=sys.stderr,
            )

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
