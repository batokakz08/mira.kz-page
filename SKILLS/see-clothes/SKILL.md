---
name: see-clothes
description: Read a photo of clothes and turn it into a wardrobe list (name, colour, material, style, warmth) before styling.
---

# See clothes in a photo

Use when the user sends a photo of clothes, a flat lay or an open wardrobe.

## Steps

1. Check that the file exists. If not, ask the user for the full path.
2. From the project folder, run:

   ```bash
   python3 TOOLS/see_clothes.py path/to/photo.jpg
   ```

   It takes about 10-40 seconds and prints a JSON array.
3. Show the list to the user in simple words: item, colour, style, warmth (1 = light, 5 = very warm).
4. Check against the photo: remove anything the model made up, mark unclear items, ask for a second photo if needed.
5. With the user's OK, save the array to `wardrobe.json` in the project folder.
6. If there is a person in the photo, describe only the clothes, never the body.

## Good input

- Good light, items not folded on top of each other.
- One photo can hold a whole outfit; a wardrobe needs several photos.
- The model can invent details: colour is usually reliable, material and brand are not.
