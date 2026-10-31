# Kibbe styling layer

Load this file together with one style file (street, classy, minimalism or casual)
when the app has a Kibbe type for the user. It does not replace the style file. It
adjusts line, volume, fabric, detail, pattern scale and length inside the style the
user picked.

## Priority order

1. The user's explicit request.
2. Occasion and weather.
3. The style file: its formula, rules and failure modes.
4. Body shape, from the `bodyshape` skill, for proportion: rise, lengths, where the
   volume sits, waist point.
5. This file: Kibbe adjustments for fabric, structure, detail, pattern scale and
   sharpness.
6. Color type (palette).

If body type and Kibbe disagree on something both touch (neckline, jacket length), the
body type decides. If a Kibbe preference conflicts with a failure mode in the style file,
the failure mode wins. If the type has a preferred formula that the chosen style doesn't have, take the
closest one. Present Kibbe as a guide, not as a rule: never tell the user that a piece
is "wrong for their body".

## Uncertain type

If the input has a runner-up or confidence "low", choose pieces that suit both types.
Use what the two have in common (see the families below), and avoid what either type
avoids.

---

## The five families

| Family | Essence | Line | Fabric | Detail | Pattern | Avoid |
|---|---|---|---|---|---|---|
| Dramatic | sleek, sharp, elongated | long, unbroken, vertical; strong shoulder; sharp angles | smooth, structured (crepe, gabardine, leather, satin) | bold, few, large | large, graphic, high contrast | small ruffles, busy details, short boxy crops, chunky soft knits |
| Natural | relaxed, earthy, easy | broad, blunt, unstructured, layered | textured (tweed, linen, denim, suede, brushed wool, chunky knit) | casual, undone | organic, medium to large, plaid | stiff tailoring, tiny delicate details, high shine, very tight fit |
| Classic | refined, balanced, polished | symmetrical, clean, moderate | medium-weight, smooth, good quality (wool, fine knit, silk) | subtle, understated | simple, subtle stripe, houndstooth | extremes (very oversized, very tight, very ornate), asymmetry |
| Gamine | playful, contrast, energetic | short and compact; mix of sharp and curved | mixed: crisp with soft, texture contrast | lively, small to medium (buttons, pockets) | small to medium, playful, dots, stripes | long unbroken columns, large uncropped volume, shapeless softness |
| Romantic | lush, soft, sensual | curved, flowing, fitted at the waist | soft drape (silk, satin, velvet, fine knit, lace) | gentle, curved (ruching, wrap) | soft florals, tonal, curved | boxy, stiff, harsh angles, rigid sporty pieces |

## The 13 types: what each adds to its family

| Type | Adjustment |
|---|---|
| Dramatic | the family as written: strongest verticals, monochrome columns, sharp shoulders |
| Soft Dramatic | the long line, but with soft drape and lush texture; softer lapels and curved edges; fluid fabrics instead of stiff ones |
| Flamboyant Natural | relaxed layers, but longer, sharper and bolder: long jackets, wider shoulders, bold animal print |
| Natural | the family as written: relaxed layers, textured fabrics, easy straight or wide leg |
| Soft Natural | relaxed but softer: fluid knits, gentle drape, rounded shoulders, lower volume |
| Dramatic Classic | tailored and balanced, with sharper edges and crisp structure; a slightly longer line |
| Classic | the family as written: matched sets, clean tailoring, waist defined at its natural place |
| Soft Classic | tailored but with softer fabrics, gentle drape and rounded edges |
| Flamboyant Gamine | contrast turned up: sharper angles, bolder pairings, strong edges; cropped and fitted |
| Gamine | the family as written: cropped jackets, high waist, short lengths, sharp-with-soft pairings |
| Soft Gamine | playful but softer: fluid fabrics with a cropped shape, rounded details, softer contrast |
| Theatrical Romantic | the soft curved line with extra glamour and length: sleek and long with curves, richer fabrics |
| Romantic | the family as written: wraps, fitted waist, fluid skirts, curved hems, V or sweetheart necklines |

## Formula preferences by family

"Prefer" means choose first. "Care" means use only with the adjustments in the table above.

| Family | Street (A–J) | Classy (A–F) | Minimalism (A–F) | Casual (A–G) |
|---|---|---|---|---|
| Dramatic | prefer A, F, J; care C, G, H | prefer F, A, C; care B | prefer F, E, C, D; B with a sharp blazer | prefer A, E, D; care C, G |
| Natural | prefer B, C, G, H; care D | prefer A, F; care D, E | prefer B, F; care C | prefer A, C, D, G; care E |
| Classic | prefer A, D, F; care G, H, I | prefer A, B, C, D; care E | prefer A, D, F; care B | prefer B, A, F; care C, G |
| Gamine | prefer A, D, E, H, I, J; care C, F | prefer B, D, A; care C, F | prefer A, D; care C, F | prefer F, B, C (cropped), G; care A, D |
| Romantic | prefer D, E, I, J (fitted); care C, G | prefer D, E, A; care B, F | prefer C, A (wrap), E (soft); care B | prefer B (wrap), D (soft skirt), E (soft knit); care C, G |

## With the bodyshape skill

The `bodyshape` skill stays the only source of rules for body shape. This file does not
repeat them. The shape names it uses are: песочные часы, груша, яблоко, прямоугольник,
перевёрнутый треугольник, and "не знаю" (no shape rules).

| Topic | Decided by |
|---|---|
| Rise, top and jacket length, hem length, where the volume sits, waist point, neckline shape | body shape (`bodyshape` skill) |
| Fabric, how structured or soft a piece is, detail scale, pattern scale, how sharp the overall look is | Kibbe type (this file) |
| Palette | color type |

Wording rules of the `bodyshape` skill apply here too: say "line", "balance",
"proportion", "ease", "structure"; never "hide", "slim", "flatter", "problem area";
"if you want definition", not "you should". The user's comfort and own words win. Use at
most 3 shape rules and at most 3 Kibbe rules in one request.

How to resolve common combinations (options, not corrections):

| Kibbe family + shape | Resolution |
|---|---|
| Natural + груша | keep the relaxed layers; end them at the high hip or below the hip; texture and light on the upper half; straight or wide leg in a softer fabric |
| Natural + яблоко | long open layers (long cardigan, blazer worn open), V neck, straight or wide leg; textured but draping fabric |
| Dramatic + груша | keep the long vertical line; add some structure at the shoulder; long coats, wide leg with a long hem |
| Dramatic + перевёрнутый треугольник | keep the sleek verticals; soft shoulder line; columns with volume at the hem; flare or wide leg |
| Classic + прямоугольник | keep the tailoring; if the user wants a waist, add a belt, a tuck or a nipped blazer |
| Classic + яблоко | tailored but skimming; straight jacket worn open; V neck; soft waistband |
| Gamine + яблоко | structured short jacket with an open front; if cropped, worn open; short or knee skirts if the user likes them |
| Gamine + груша | cropped jacket and high waist are fine; some presence at the shoulder; pleated or A-line short skirt |
| Romantic + перевёрнутый треугольник | wrap with a V neckline and soft shoulder; full or flared skirts; draped fabric |
| Romantic + прямоугольник | wrap and fitted waist if the user wants definition, ruching, curved hems, peplum |

For other combinations, use Kibbe for fabric and detail and the `bodyshape` skill for
proportion.

## How to apply

1. Choose the style file's formula as usual, using this table to pick the formula.
2. Choose pieces: fabric, neckline, detail and pattern scale from the family row and
   the type's adjustment.
3. Check length and shoe against the style file's rules first, then against the
   family's avoid list.
4. If the user also has a body shape, adjust rise, lengths and waist point with the
   `bodyshape` skill (see "With the bodyshape skill" above).
5. Add one line to the output format:

   `5. Fit note: one sentence on how the outfit suits the Kibbe type (line, fabric, detail) and the body shape (proportion).`

   Leave out whichever the user doesn't have. Never comment on the body.

Example: *"Soft Natural, casual formula A: the long coat keeps the relaxed line, and the
brushed wool and loose knit keep it soft."*
