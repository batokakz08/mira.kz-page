---
name: bodyshape
description: Optional body-shape guidance for fit, silhouette and necklines, using measurements or the user's own description. Body-neutral, no photo diagnosis, no judgment.
---

# Fit by body shape

Use only when the user asks "what suits my body", "what is my shape", "how should this fit",
or when they give measurements or a shape and want outfits that use that information.

Body shape is a styling preference, not a diagnosis. Do not guess it from a selfie, a photo of
clothes or a size. If the user does not want to share it, skip this skill and use fit and comfort only.

## Ask

Ask for the smallest useful input, in this order:

1. "Хочешь, учту силуэт? Это необязательно."
2. If yes, offer four measurements in cm: shoulders, bust, waist, hips.
3. If they do not want to measure, offer the shape names: песочные часы, груша, яблоко,
   прямоугольник, перевёрнутый треугольник, "не знаю".

Do not ask for weight, size, age or body photos. Store only the shape if the user agrees; do not
store the measurements in a public place.

## Measurements

Ask the user to measure over light clothes, with the tape level and not pulled tight:

- **Shoulders** — widest point across the upper back, arms down.
- **Bust** — fullest point, tape level under the arms.
- **Waist** — narrowest point; if there is no clear waist, 2 cm above the navel.
- **Hips** — fullest point at the seat.

Use whole centimetres. A difference under 2 cm is not meaningful; do not over-interpret it.

## Name the shape

Read `SKILLS/bodyshape/SKILL.md` rules and run the calculator when a tool is available:

```bash
python3 TOOLS/bodyshape.py --shoulders 96 --bust 90 --waist 72 --hips 100
```

On the web page, the optional **«Силуэт»** block uses the same rules and keeps the shape only for the
current visit; it does not save the measurements. After you choose a shape, it shows a short
**«Верх / Низ / Слой / Вырез»** guide, and the same shape is added to the outfit prompt. In the chat, run
the calculator below when you need to check the numbers.

The order matters:

1. **Груша** — hips are at least 5 cm wider than shoulders and at least 5 cm wider than bust.
2. **Перевёрнутый треугольник** — shoulders are at least 5 cm wider than hips.
3. **Песочные часы** — shoulders and hips are within 5 cm of each other and the waist is at least
   10 cm smaller than the smallest of shoulders, bust and hips.
4. **Яблоко** — the waist is close to the bust or hips (within 2 cm of the smaller one) and
   shoulders and hips are within 7 cm.
5. **Прямоугольник** — everything else with a small shoulder–hip difference and no clear waist.

If a measurement is within 2 cm of a threshold, say "between two shapes" and use the rules from both.
If the user names a shape, use their name; do not correct them with measurements unless they ask.
If the measurements are incomplete, do not classify.

## What to do with each shape

These are options, not corrections. The user's comfort, modesty, weather, occasion and own taste win.
Never say "hide", "slim", "flatter", "problem area", "too wide" or "bad proportions".

### Песочные часы

- **If the user wants definition:** wrap tops, belts, high-rise straight or wide trousers, bias-cut
  midi skirts, single-breasted coats.
- **If the user wants ease:** straight or relaxed layers with one clean vertical line; no need to cinch.
- Necklines: V, scoop, crew. An open collar or a long pendant can add a vertical line.
- Avoid making every layer tight; one fitted piece and one relaxed piece is usually enough.

### Груша

- Balance the line with a little structure or light on the upper body: boat, V or square necklines,
  collared shirts, soft shoulder seams, tops that end at the high hip or below the hip.
- Bottoms: straight, wide-leg, bootcut, A-line midi; choose fabrics that let you sit and walk.
- Outer layer: a jacket or coat that ends below the hip; a longer cardigan can create a vertical line.
- If the user likes fitted bottoms, keep the top and layer relaxed; do not make the hips the topic.

### Яблоко

- Create a long vertical line: open shirts, V or scoop necklines, long cardigans, straight coats.
- Bottoms: straight or wide-leg, high-rise with a soft waistband; avoid a stiff waistband if it digs in.
- Tops: soft fabrics that skim rather than cling; a longer hem can feel easier than a cropped one.
- Do not suggest shapewear or "control" anything.

### Прямоугольник

- If the user wants more waist: a belt, a tucked-in knit, a pleated midi, a peplum, or volume in
  the trousers or skirt. If not, keep a clean straight line.
- Layers work well: long vest, shirt-jacket, cardigan, straight coat.
- Necklines: crew, collar, halter; choose what feels comfortable.
- Avoid adding volume at both the top and the bottom at once unless that is the intended look.

### Перевёрнутый треугольник

- Soften the shoulder line: raglan sleeves, V or scoop necklines, softer shoulder seams, vertical details.
- Bottoms: wide-leg, pleated, A-line, lighter colours or more volume than the top.
- Outer layer: single-breasted, straight or slightly A-line; avoid heavy epaulettes and stiff wide
  shoulders if the user wants balance.
- Do not call broad shoulders "masculine" or "too much".

### Не знаю / не указано

- No shape rules. Use the fit checklist below and the user's own preferences.

## Fit checklist

Use this for every outfit, with or without a shape:

- Shoulder seam sits near the shoulder bone; the sleeve does not pull across the back.
- A buttoned jacket closes without pulling; you can hug someone in it.
- Waistband is comfortable when sitting; no need to suck in.
- Trousers break once at the shoe; the rise lets you sit and walk.
- Skirt or dress lets you take a normal step and sit.
- Layers leave room for a sweater without compressing the arms.
- If a piece fails the checklist, choose another one instead of asking the user to change their body.

## Wording

- Say "line", "balance", "proportion", "ease", "structure", "vertical", "comfort", "movement".
- Say "if you want definition" or "if you prefer ease", not "you should".
- Never comment on weight, size, age, health, pregnancy or attractiveness.
- Never promise that a garment will "fix" or "hide" a body.
- If the user says a shape name about themselves, use their words and do not argue.
- If the user asks for a shape analysis from a photo, say that this skill does not diagnose from photos;
  offer measurements or a self-described shape instead.

## Output for the stylist

Add one short block to the outfit prompt, for example:

```text
Силуэт: груша (по меркам, уверенность средняя).
Учитывай деликатно: поддержи баланс верха и низа, выбирай прямые или широкие брюки,
A-силуэт юбок, верх с мягкой линией плеч; не делай облегающую ткань на бёдрах главной темой.
Не комментируй тело и не называй его проблемным.
```

Use at most 3 shape rules in one request. If the user did not provide a shape, add nothing.
