---
name: style-outfit
description: Build 3 outfits from clothes the user already owns, for one occasion and the weather.
---

# Style an outfit

Use when the wardrobe is known and the user wants what to wear.

## Steps

1. Read `KNOWLEDGE/style.md` first. Use it as defaults; the user's own rules win. Never leave the wardrobe.
2. You need three things: the wardrobe (`wardrobe.json` or a written list), the occasion, and the weather or place.
   Ask only for what is missing.
3. From the project folder, run:

   ```bash
   python3 TOOLS/suggest.py --wardrobe wardrobe.json --occasion "university presentation" --weather "Almaty, +8 C, windy"
   ```

   Add `--notes "no heels, I walk a lot"` when the user has extra wishes.
4. The tool prints JSON with 3 outfits: Safe, Sharper, Comfortable.
5. Check every item against `wardrobe.json`. Replace anything that is not in the wardrobe and rerun if needed.
6. Present the outfits with 1-2 lines of why and one watch-out each ("take a scarf, it is windy").
7. Ask what to adjust, then rerun with `--notes`.

## Rules

- Only owned clothes. v0.1 does not suggest shopping.
- Follow `KNOWLEDGE/style.md`. Use body-shape rules only when the user gives measurements or a shape,
  then follow `SKILLS/bodyshape/SKILL.md`; never guess a shape.
- Cold weather means layers, warm shoes and a coat; hot weather means one light layer and shade.
- No body comments. No "slimming", no "hides your figure".
- If the occasion needs something the wardrobe does not have, say it plainly: "You have no formal shoes; the black boots are the closest."
