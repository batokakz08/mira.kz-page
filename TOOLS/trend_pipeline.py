"""Trend brief pipeline: context, prompt, validation and weekly lifecycle.

The LLM only proposes content. Counts, status, conflict and confidence are
recomputed here from the source registry, so the model cannot invent them.
"""

from __future__ import annotations

import json
import math
import re
from datetime import datetime, timezone
from typing import Any, Callable, Iterable

SCHEMA_VERSION = "2.1"
MAX_AGE = {"editorial": 90, "runway_report": 270, "retailer": 30}
EDITORIAL_TYPES = {"editorial", "runway_report"}
CATEGORIES = {"color", "silhouette", "garment", "fabric", "print", "accessory", "shoe"}
LONGEVITY = {"lasting", "micro"}
REASONS = {"too_old", "off_season", "future_date", "duplicate", "no_trend_content", "unverifiable"}
OUTDATED_BASELINE = {
    "skinny jeans": "skinny jeans",
    "all-beige minimalism": "all-beige minimalism",
    "millennial pink": "millennial pink",
    "2016-2020 instagram-era looks": "2016-2020 instagram-era looks",
}
HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")
KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
MAX_WORDS = 20
MAX_DIRECTION_WORDS = 120
MAX_NOTES_WORDS = 30
NEED = {
    "schema_version", "generated_on", "run_context", "overall_direction",
    "capsule_formula", "sources_used", "sources_ignored", "trends",
    "palette", "outdated_to_avoid",
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_date(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.strptime(value.strip(), "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def build_context(n_docs: int, hemisphere: str = "northern", now: datetime | None = None,
                  language: str = "Russian") -> tuple[dict[str, Any], list[str]]:
    """Return prompt context and the accepted runway season labels.

    Northern hemisphere follows the retail calendar: AW starts in September,
    SS starts in March. Southern hemisphere is shifted by six months.
    """
    now = now or utc_now()
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    hemisphere = hemisphere.lower().strip()
    if hemisphere not in {"northern", "southern"}:
        raise ValueError("hemisphere must be 'northern' or 'southern'")

    month = now.month
    if hemisphere == "northern":
        if month in (9, 10, 11, 12):
            season, season_year = "AW", now.year
        elif month in (1, 2):
            season, season_year = "AW", now.year - 1
        else:
            season, season_year = "SS", now.year
    else:
        if month in (9, 10, 11, 12):
            season, season_year = "SS", now.year
        elif month in (1, 2):
            season, season_year = "SS", now.year - 1
        else:
            season, season_year = "AW", now.year

    target = f"{season}{season_year}"
    following = f"SS{season_year + 1}" if season == "AW" else f"AW{season_year}"
    runway = [target, following]
    human = {"AW": "autumn/winter", "SS": "spring/summer"}[season]
    context = {
        "CURRENT_DATE": now.strftime("%Y-%m-%d"),
        "SEASON": human,
        "YEAR": season_year,
        "SEASON_LABEL": target,
        "HEMISPHERE": hemisphere,
        "N": n_docs,
        "ACCEPTED_RUNWAY_SEASONS": ", ".join(runway),
        "LANGUAGE": language,
    }
    return context, runway


def build_registry(documents: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Build a URL-keyed registry. Duplicate URLs must be deduped first."""
    registry: dict[str, dict[str, Any]] = {}
    for index, doc in enumerate(documents, 1):
        if not isinstance(doc, dict):
            raise ValueError(f"document {index} is not an object")
        url = doc.get("url")
        if not isinstance(url, str) or not url.strip():
            raise ValueError(f"document {index} has no URL")
        if url in registry:
            raise ValueError(f"duplicate URL: {url}; dedupe documents before analysis")
        source_type = doc.get("source_type")
        if isinstance(source_type, str):
            source_type = source_type.strip().lower()
        publisher_group = doc.get("publisher_group")
        if isinstance(publisher_group, str):
            publisher_group = publisher_group.strip()
        season_covered = doc.get("season_covered")
        if isinstance(season_covered, str):
            season_covered = season_covered.strip()
        registry[url] = {
            "id": f"d{index}",
            "url": url,
            "publisher": doc.get("publisher"),
            "publisher_group": publisher_group,
            "source_type": source_type,
            "publish_date": doc.get("publish_date"),
            "season_covered": season_covered,
            "text": doc.get("text", ""),
        }
    return registry


def doc_issue(doc: dict[str, Any], now: datetime, runway_seasons: list[str]) -> str | None:
    """Return the ignore reason for an ineligible document, or None if eligible."""
    if not isinstance(doc, dict):
        return "unverifiable"
    source_type = doc.get("source_type")
    if not doc.get("publisher_group") or source_type not in MAX_AGE:
        return "unverifiable"
    published = _parse_date(doc.get("publish_date"))
    if published is None:
        return "unverifiable"
    if published > now:
        return "future_date"
    age = (now - published).days
    if age > MAX_AGE[source_type]:
        return "too_old"
    if source_type == "runway_report":
        season = doc.get("season_covered")
        if not season:
            return "unverifiable"
        if season not in runway_seasons:
            return "off_season"
    return None


def eligible(doc: dict[str, Any], now: datetime, runway_seasons: list[str]) -> bool:
    return doc_issue(doc, now, runway_seasons) is None


def expected_confidence(n: int, retail: int, runway: bool, conflict: bool) -> float:
    if n <= 0:
        return 0.05
    score = {1: 0.30, 2: 0.50, 3: 0.70}.get(n, 0.80)
    score += 0.10 * (retail >= 1) + 0.05 * runway - 0.20 * conflict
    return min(max(score, 0.05), 0.95)


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_number(value: Any) -> bool:
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(float(value)))


def _words(value: Any) -> int:
    return len(value.split()) if isinstance(value, str) else 0


def _sentences(value: Any) -> int:
    if not isinstance(value, str):
        return 0
    return len([part for part in re.split(r"(?<=[.!?])\s+", value.strip()) if part])


def _url_list(value: Any) -> list[str] | None:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        return None
    return value


def validate(raw: Any, registry: dict[str, dict[str, Any]], runway_seasons: list[str],
             context: dict[str, Any], now: datetime | None = None) -> tuple[dict[str, Any] | None, list[str]]:
    """Validate and recompute derived fields. Never raises on malformed model output."""
    errors: list[str] = []
    now = now or _parse_date(context.get("CURRENT_DATE")) or utc_now()
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    if not isinstance(raw, str):
        return None, ["output must be a JSON string"]

    text = raw.strip()
    if not (text.startswith("{") and text.endswith("}")):
        return None, ["output must be a bare JSON object: no markdown fences or surrounding text"]
    try:
        brief = json.loads(text, parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
    except (json.JSONDecodeError, ValueError) as error:
        return None, [f"invalid JSON: {error}"]
    if not isinstance(brief, dict):
        return None, ["output must be a JSON object"]

    missing = NEED - set(brief)
    if missing:
        return None, [f"missing top-level keys: {sorted(missing)}"]

    if brief.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION!r}")
    if brief.get("generated_on") != context.get("CURRENT_DATE"):
        errors.append("generated_on must equal context CURRENT_DATE")

    run_context = brief.get("run_context")
    if not isinstance(run_context, dict):
        errors.append("run_context must be an object")
    else:
        if run_context.get("season") != context.get("SEASON_LABEL"):
            errors.append(f"run_context.season must be {context.get('SEASON_LABEL')!r}")
        if run_context.get("hemisphere") != context.get("HEMISPHERE"):
            errors.append(f"run_context.hemisphere must be {context.get('HEMISPHERE')!r}")
        if run_context.get("documents_received") != len(registry):
            errors.append(f"documents_received must be {len(registry)}")

    direction = brief.get("overall_direction")
    if not isinstance(direction, str) or not direction.strip():
        errors.append("overall_direction must be a non-empty string")
    else:
        if not 2 <= _sentences(direction) <= 3:
            errors.append("overall_direction must be 2-3 sentences")
        if _words(direction) > MAX_DIRECTION_WORDS:
            errors.append(f"overall_direction over {MAX_DIRECTION_WORDS} words")

    used_list = _url_list(brief.get("sources_used"))
    if used_list is None:
        errors.append("sources_used must be a list of URLs")
        used_list = []
    used = set(used_list)
    if len(used_list) != len(used):
        errors.append("sources_used contains duplicate URLs")

    ignored_value = brief.get("sources_ignored")
    ignored_list: list[dict[str, Any]] = []
    if not isinstance(ignored_value, list):
        errors.append("sources_ignored must be a list")
    else:
        for item in ignored_value:
            if not isinstance(item, dict) or not isinstance(item.get("url"), str) or not isinstance(item.get("reason"), str):
                errors.append("sources_ignored items need string url and reason")
            else:
                ignored_list.append(item)
    ignored = {item["url"] for item in ignored_list}
    if len(ignored_list) != len(ignored):
        errors.append("sources_ignored contains duplicate URLs")

    if used & ignored:
        errors.append("a URL is both used and ignored")
    unknown = (used | ignored) - set(registry)
    unaccounted = set(registry) - (used | ignored)
    if unknown:
        errors.append(f"unknown URLs: {sorted(unknown)}")
    if unaccounted:
        errors.append(f"unaccounted URLs: {sorted(unaccounted)}")

    for url in used & set(registry):
        issue = doc_issue(registry[url], now, runway_seasons)
        if issue:
            errors.append(f"ineligible source used ({issue}): {url}")

    for item in ignored_list:
        url, reason = item["url"], item["reason"]
        if reason not in REASONS:
            errors.append(f"bad ignore reason for {url}: {reason}")
            continue
        doc = registry.get(url)
        if doc is None:
            continue
        issue = doc_issue(doc, now, runway_seasons)
        if reason == "duplicate":
            original = item.get("duplicate_of")
            if not isinstance(original, str) or original not in registry or original == url:
                errors.append(f"duplicate {url} needs a different duplicate_of URL from the registry")
            elif original not in used:
                errors.append(f"duplicate {url} points to a source that is not used")
        elif issue is not None and reason != issue:
            errors.append(f"{url} must be ignored as {issue!r}, not {reason!r}")
        elif issue is None and reason != "no_trend_content":
            errors.append(f"eligible source {url} must be used or ignored as no_trend_content")

    capsule = brief.get("capsule_formula")
    if not isinstance(capsule, dict):
        errors.append("capsule_formula must be an object")
    else:
        basics = capsule.get("basics_percent")
        statement = capsule.get("statement_percent")
        ratio = capsule.get("ratio_source_url")
        notes = capsule.get("notes", "")
        if not isinstance(notes, str):
            errors.append("capsule_formula.notes must be a string")
        elif _words(notes) > MAX_NOTES_WORDS:
            errors.append(f"capsule_formula.notes over {MAX_NOTES_WORDS} words")
        if basics is None and statement is None:
            if ratio is not None:
                errors.append("ratio_source_url must be null when percentages are null")
        elif not (_is_int(basics) and _is_int(statement)
                  and 0 <= basics <= 100 and 0 <= statement <= 100
                  and basics + statement == 100):
            errors.append("capsule_formula percentages must be integers 0-100 summing to 100")
        elif not isinstance(ratio, str) or ratio not in used:
            errors.append("capsule_formula must cite a used ratio_source_url")

    trends_value = brief.get("trends")
    trends: list[dict[str, Any]] = []
    if not isinstance(trends_value, list):
        errors.append("trends must be a list")
    elif not trends_value:
        errors.append("trends must not be empty")
    else:
        for item in trends_value:
            if not isinstance(item, dict):
                errors.append("every trend must be an object")
            else:
                trends.append(item)

    seen: set[str] = set()
    pair_checks: list[tuple[str, list[str]]] = []
    for trend in trends:
        tid = trend.get("id")
        if not isinstance(tid, str) or not KEBAB.match(tid):
            errors.append(f"trend {tid!r}: id must be kebab-case")
            tid = str(tid)
        elif tid in seen:
            errors.append(f"trend {tid}: duplicate id")
        seen.add(tid)

        name = trend.get("name")
        if not isinstance(name, str) or not name.strip() or len(name) > 80:
            errors.append(f"trend {tid}: name must be a non-empty string up to 80 chars")
        if trend.get("category") not in CATEGORIES:
            errors.append(f"trend {tid}: bad category")
        if trend.get("longevity") not in LONGEVITY:
            errors.append(f"trend {tid}: longevity must be 'lasting' or 'micro'")
        for field in ("description", "style_tip"):
            value = trend.get(field)
            if not isinstance(value, str) or not 1 <= _words(value) <= MAX_WORDS:
                errors.append(f"trend {tid}: {field} must be 1-{MAX_WORDS} words")

        editorial = _url_list(trend.get("editorial_sources"))
        retail = _url_list(trend.get("retail_sources"))
        if editorial is None:
            errors.append(f"trend {tid}: editorial_sources must be a list of URLs")
            editorial = []
        if retail is None:
            errors.append(f"trend {tid}: retail_sources must be a list of URLs")
            retail = []
        if len(editorial) != len(set(editorial)):
            errors.append(f"trend {tid}: duplicate editorial URL")
        if len(retail) != len(set(retail)):
            errors.append(f"trend {tid}: duplicate retail URL")
        if not editorial:
            errors.append(f"trend {tid}: needs at least 1 editorial URL")

        for url in editorial:
            doc = registry.get(url)
            if not doc:
                errors.append(f"trend {tid}: unknown editorial URL {url}")
            elif doc.get("source_type") not in EDITORIAL_TYPES:
                errors.append(f"trend {tid}: not an editorial/runway source {url}")
            elif url not in used:
                errors.append(f"trend {tid}: editorial URL not in sources_used {url}")
            elif doc_issue(doc, now, runway_seasons):
                errors.append(f"trend {tid}: ineligible editorial URL {url}")
        for url in retail:
            doc = registry.get(url)
            if not doc:
                errors.append(f"trend {tid}: unknown retail URL {url}")
            elif doc.get("source_type") != "retailer":
                errors.append(f"trend {tid}: not a retailer source {url}")
            elif url not in used:
                errors.append(f"trend {tid}: retail URL not in sources_used {url}")
            elif doc_issue(doc, now, runway_seasons):
                errors.append(f"trend {tid}: ineligible retail URL {url}")

        publisher_groups = {
            registry[url]["publisher_group"] for url in editorial
            if url in registry and registry[url].get("publisher_group")
        }
        editorial_count = len(publisher_groups)
        retail_count = len({
            registry[url]["publisher_group"] for url in retail
            if url in registry and registry[url].get("publisher_group")
        })
        if trend.get("editorial_count") != editorial_count:
            errors.append(f"trend {tid}: editorial_count must be {editorial_count}")
        if trend.get("retail_count") != retail_count:
            errors.append(f"trend {tid}: retail_count must be {retail_count}")

        fading = _url_list(trend.get("fading_sources"))
        if fading is None:
            errors.append(f"trend {tid}: fading_sources must be a list of URLs")
            fading = []
        if len(fading) != len(set(fading)):
            errors.append(f"trend {tid}: duplicate fading URL")
        for url in fading:
            if url not in editorial:
                errors.append(f"trend {tid}: fading URL must also be in editorial_sources {url}")
        fading_groups = {
            registry[url]["publisher_group"] for url in fading
            if url in registry and registry[url].get("publisher_group")
        }
        fading_signals = len(fading_groups)
        if not _is_int(trend.get("fading_signals")) or trend.get("fading_signals") != fading_signals:
            errors.append(f"trend {tid}: fading_signals must be {fading_signals}")

        supporting = editorial_count - fading_signals
        status = ("fading" if fading_signals * 2 > editorial_count
                  else "confirmed" if supporting >= 3 else "emerging")
        if trend.get("status") != status:
            errors.append(f"trend {tid}: status must be {status!r}")
        conflict = fading_signals > 0 and supporting > 0
        if trend.get("conflict") is not conflict:
            errors.append(f"trend {tid}: conflict must be {str(conflict).lower()}")
        note = trend.get("conflict_note")
        if not isinstance(note, str):
            errors.append(f"trend {tid}: conflict_note must be a string")
        elif conflict:
            if not 1 <= _words(note) <= MAX_WORDS:
                errors.append(f"trend {tid}: conflict_note must be 1-{MAX_WORDS} words")
        elif note.strip():
            errors.append(f"trend {tid}: conflict_note must be empty when there is no conflict")

        runway = any(
            registry.get(url, {}).get("source_type") == "runway_report"
            for url in editorial
        )
        confidence = expected_confidence(editorial_count, retail_count, runway, conflict)
        if not _is_number(trend.get("confidence")) or abs(float(trend["confidence"]) - confidence) > 0.011:
            errors.append(f"trend {tid}: confidence must be {confidence:.2f}")

        pairs = trend.get("pairs_well_with")
        if not isinstance(pairs, list) or not all(isinstance(item, str) for item in pairs):
            errors.append(f"trend {tid}: pairs_well_with must be a list of trend ids")
        elif len(pairs) != len(set(pairs)) or tid in pairs:
            errors.append(f"trend {tid}: pairs_well_with must be unique and exclude itself")
        else:
            pair_checks.append((tid, pairs))

    for tid, pairs in pair_checks:
        for other in pairs:
            if other not in seen:
                errors.append(f"trend {tid}: pairs_well_with unknown trend {other}")

    palette = brief.get("palette")
    color_names: set[str] = set()
    if not isinstance(palette, dict):
        errors.append("palette must be an object")
    else:
        for key in ("accent_colors", "base_neutrals"):
            colors = palette.get(key)
            if not isinstance(colors, list) or not colors:
                errors.append(f"palette.{key} must be a non-empty list")
                continue
            for color in colors:
                if not isinstance(color, dict):
                    errors.append(f"palette.{key} item must be an object")
                    continue
                name = color.get("name")
                if not isinstance(name, str) or not name.strip() or len(name) > 40:
                    errors.append(f"palette.{key}: color name is invalid")
                else:
                    color_names.add(name.strip().lower())
                if not isinstance(color.get("hex"), str) or not HEX.match(color["hex"]):
                    errors.append(f"palette.{key}: hex must be #RRGGBB")
        pairings = palette.get("proven_pairings")
        if not isinstance(pairings, list):
            errors.append("palette.proven_pairings must be a list")
        else:
            for pair in pairings:
                if not (isinstance(pair, list) and len(pair) == 2 and all(isinstance(item, str) for item in pair)):
                    errors.append("palette.proven_pairings items must be pairs of strings")
                else:
                    for name in pair:
                        if name.strip().lower() not in color_names:
                            errors.append(f"palette.proven_pairings uses unknown color {name!r}")

    outdated = brief.get("outdated_to_avoid")
    if not isinstance(outdated, list) or not all(isinstance(item, str) for item in outdated):
        errors.append("outdated_to_avoid must be a list of strings")
        outdated = []
    normalized_outdated = {item.strip().lower() for item in outdated}
    if len(normalized_outdated) != len(outdated):
        errors.append("outdated_to_avoid contains duplicates")

    revived_value = brief.get("revived_items", [])
    revived: dict[str, list[str]] = {}
    if not isinstance(revived_value, list):
        errors.append("revived_items must be a list")
    else:
        for item in revived_value:
            if not isinstance(item, dict) or not isinstance(item.get("item"), str):
                errors.append("revived_items items need an item string")
                continue
            label = item["item"].strip().lower()
            if label not in OUTDATED_BASELINE:
                errors.append(f"revived item is not in the outdated baseline: {item['item']!r}")
                continue
            if label in revived:
                errors.append(f"duplicate revived item: {item['item']!r}")
                continue
            sources = _url_list(item.get("sources"))
            if not sources:
                errors.append(f"revived item {item['item']!r} needs source URLs")
                continue
            for url in sources:
                doc = registry.get(url)
                if (url not in used or not doc
                        or doc.get("source_type") not in EDITORIAL_TYPES
                        or doc_issue(doc, now, runway_seasons)):
                    errors.append(f"revived item {item['item']!r} needs an eligible editorial source {url}")
            revived[label] = sources

    for label in OUTDATED_BASELINE:
        if label in revived:
            if label in normalized_outdated:
                errors.append(f"revived item {label!r} must not be in outdated_to_avoid")
        elif label not in normalized_outdated:
            errors.append(f"outdated_to_avoid must include {label!r}")

    return (None if errors else brief), errors


PROMPT_TEMPLATE = r"""You are a fashion trend analyst. Your output is read by a program. Output JSON only.

CONTEXT (filled by the pipeline, do not change)
- Today (UTC): {{CURRENT_DATE}}
- Target wearing season: {{SEASON}} {{YEAR}}, {{HEMISPHERE}} hemisphere ({{SEASON_LABEL}})
- Accepted runway seasons: {{ACCEPTED_RUNWAY_SEASONS}}
- Documents received: {{N}}
- Write all human-readable text in {{LANGUAGE}}. Keep JSON keys and enum values in English.

Each document starts with a header line:
[DOC id] url | publisher | publisher_group | source_type | publish_date | season_covered

SOURCE ELIGIBILITY
- editorial: publish_date within 90 days of today.
- runway_report: within 270 days of today AND season_covered is in the accepted runway seasons.
- retailer: within 30 days of today.
- Missing or unparseable publish_date, source_type or publisher_group: ignore as "unverifiable".
- Any source that cannot be verified must be ignored, never used.
- Use ONLY the provided documents. Never use your memory of past trends.
- EVERY received document must appear exactly once, either in sources_used or in sources_ignored.
- If a document is a duplicate or syndicated copy, put it in sources_ignored with reason "duplicate" and duplicate_of set to the used URL.

COUNTING
- editorial_sources: URLs of eligible editorial and runway_report documents discussing the trend.
- retail_sources: URLs of eligible retailer documents. Retailer pages never count as editorial.
- editorial_count = number of DISTINCT publisher_group values in editorial_sources.
  Several documents from one publisher_group count once. Syndicated or near-identical text counts once.
- retail_count = number of DISTINCT publisher_group values in retail_sources.
- Every trend needs at least 1 editorial URL. Retail-only signals are omitted.
- Cite URLs exactly as given in the input. Never invent or edit a URL.

FADING AND STATUS
- fading_sources: URLs from editorial_sources that explicitly call the trend out, over, or declining.
  The validator counts DISTINCT publisher_group values in this list. Do not count the same publisher twice.
- supporting = editorial_count - fading_signals.
- status = "fading" if fading_signals*2 > editorial_count;
  else "confirmed" if supporting >= 3; else "emerging".
- conflict = true if fading_signals > 0 AND supporting > 0. Then describe the disagreement in
  conflict_note (max 20 words); otherwise conflict_note = "".

CONFIDENCE (computed from the fields above)
- n = editorial_count: n=1 -> 0.30, n=2 -> 0.50, n=3 -> 0.70, n>=4 -> 0.80
- +0.10 if retail_count >= 1; +0.05 if any editorial source is a runway_report;
  -0.20 if conflict. Clamp to 0.05-0.95.

CONTENT RULES
- Dimensions: colors, silhouettes/garments, fabrics, prints (abstract, graphic), accessories,
  shoes, overall mood, how capsule wardrobes are changing.
- longevity: "lasting" for a direction across silhouettes, colours or seasons;
  "micro" for one garment, accessory or short-lived detail.
- Treat skinny jeans, all-beige minimalism, millennial pink and 2016-2020 Instagram-era looks
  as outdated unless the documents say they are back. If a document says one is back, put it in
  revived_items with its editorial URL and leave it out of outdated_to_avoid.
- Paraphrase; never quote. description and style_tip: max 20 words each.
- capsule_formula: fill only if a document states a basics/statement ratio (integers summing
  to 100, ratio_source_url = that document). Otherwise set all three to null.
- palette hex values are a visual mapping, not a source claim.
- No body judgments: do not mention weight, age, size, shape or "flattering" areas.

OUTPUT FORMAT
A single bare JSON object. No markdown fences, no text before or after. All keys present;
use [] instead of null for lists.
{
  "schema_version": "2.1",
  "generated_on": "YYYY-MM-DD",
  "run_context": {"season": "{{SEASON_LABEL}}", "hemisphere": "{{HEMISPHERE}}", "documents_received": {{N}}},
  "overall_direction": "2-3 sentences",
  "capsule_formula": {"basics_percent": null, "statement_percent": null,
                      "ratio_source_url": null, "notes": ""},
  "sources_used": ["url"],
  "sources_ignored": [{"url": "", "reason": "too_old|off_season|future_date|duplicate|no_trend_content|unverifiable",
                       "duplicate_of": null}],
  "trends": [{
    "id": "kebab-case",
    "category": "color|silhouette|garment|fabric|print|accessory|shoe",
    "longevity": "lasting|micro",
    "name": "",
    "description": "",
    "status": "emerging|confirmed|fading",
    "editorial_sources": ["url"],
    "retail_sources": ["url"],
    "fading_sources": ["url"],
    "editorial_count": 0,
    "retail_count": 0,
    "fading_signals": 0,
    "conflict": false,
    "conflict_note": "",
    "confidence": 0.0,
    "pairs_well_with": ["other-trend-id"],
    "style_tip": ""
  }],
  "palette": {
    "accent_colors": [{"name": "", "hex": "#RRGGBB"}],
    "base_neutrals": [{"name": "", "hex": "#RRGGBB"}],
    "proven_pairings": [["color a", "color b"]]
  },
  "outdated_to_avoid": ["skinny jeans", "all-beige minimalism", "millennial pink",
                        "2016-2020 Instagram-era looks"],
  "revived_items": [{"item": "skinny jeans", "sources": ["url"]}]
}"""


def render_prompt(context: dict[str, Any], registry: dict[str, dict[str, Any]],
                  template: str = PROMPT_TEMPLATE) -> str:
    prompt = template
    for key, value in context.items():
        prompt = prompt.replace("{{" + key + "}}", str(value))

    docs = []
    for doc in registry.values():
        header = (
            f"[DOC {doc['id']}] url={doc['url']} | publisher={doc.get('publisher')} | "
            f"publisher_group={doc.get('publisher_group')} | source_type={doc.get('source_type')} | "
            f"publish_date={doc.get('publish_date')} | season_covered={doc.get('season_covered')}"
        )
        docs.append(header + "\n" + str(doc.get("text", "")))
    return prompt + "\n\nDOCUMENTS\n\n" + "\n\n".join(docs)


def run_analysis(prompt: str, call_llm: Callable[[str], str],
                 registry: dict[str, dict[str, Any]], runway_seasons: list[str],
                 context: dict[str, Any], now: datetime | None = None,
                 max_retries: int = 2) -> dict[str, Any] | None:
    """Call the model, validate, and retry with errors. Return None on failure."""
    current_prompt = prompt
    for _ in range(max_retries + 1):
        try:
            raw = call_llm(current_prompt)
        except Exception as error:
            errors = [f"model call failed: {type(error).__name__}: {error}"]
        else:
            brief, errors = validate(raw, registry, runway_seasons, context, now)
            if brief is not None:
                return brief
        current_prompt += (
            "\n\nYour previous output failed validation:\n- " + "\n- ".join(errors)
            + "\nReturn the corrected JSON object only."
        )
    return None


def run_key(brief: dict[str, Any]) -> str:
    date = _parse_date(brief.get("generated_on"))
    if date is None:
        raise ValueError("brief.generated_on must be YYYY-MM-DD")
    year, week, _ = date.isocalendar()
    return f"{year}-W{week:02d}"


def apply_lifecycle(brief: dict[str, Any],
                    history: dict[str, dict[str, dict[str, Any]]]) -> dict[str, Any]:
    """Copy the current week's lifecycle labels into the brief trends in place."""
    if not isinstance(brief, dict) or not isinstance(history, dict):
        return brief
    try:
        key = run_key(brief)
    except ValueError:
        return brief
    week = history.get(key)
    if not isinstance(week, dict):
        return brief
    trends = brief.get("trends")
    if not isinstance(trends, list):
        return brief
    for trend in trends:
        if not isinstance(trend, dict):
            continue
        trend_id = trend.get("id")
        if not isinstance(trend_id, str):
            continue
        record = week.get(trend_id)
        if isinstance(record, dict) and isinstance(record.get("lifecycle"), str):
            trend["lifecycle"] = record["lifecycle"]
    return brief


def update_tracking(brief: dict[str, Any], registry: dict[str, dict[str, Any]],
                    history: dict[str, dict[str, dict[str, Any]]] | None,
                    share_delta: float = 0.10,
                    max_missing_runs: int = 3) -> dict[str, dict[str, dict[str, Any]]]:
    """Return a new weekly history. The brief itself is not modified."""
    history = history or {}
    key = run_key(brief)
    generated_on = brief.get("generated_on")

    publishers = {
        registry[url]["publisher_group"]
        for url in brief.get("sources_used", [])
        if url in registry and registry[url].get("source_type") in EDITORIAL_TYPES
        and registry[url].get("publisher_group")
    }
    denominator = max(len(publishers), 1)

    previous_keys = sorted(existing for existing in history if existing < key)
    previous = history[previous_keys[-1]] if previous_keys else {}
    same_week = history.get(key, {})

    current: dict[str, dict[str, Any]] = {}
    for trend in brief.get("trends", []):
        if not isinstance(trend, dict):
            continue
        trend_id = trend.get("id")
        if not isinstance(trend_id, str) or not trend_id:
            continue
        share = round((trend.get("editorial_count") or 0) / denominator, 3)
        old = previous.get(trend_id)
        if old is None:
            lifecycle = "new"
        elif trend.get("status") == "fading":
            lifecycle = "declining"
        else:
            old_share = old.get("share")
            if not isinstance(old_share, (int, float)):
                old_share = 0.0
            delta = share - old_share
            lifecycle = ("rising" if delta >= share_delta
                         else "declining" if delta <= -share_delta else "stable")
        old_first_seen = old.get("first_seen") if old else None
        same_week_first_seen = same_week.get(trend_id, {}).get("first_seen")
        first_seen = old_first_seen or same_week_first_seen or generated_on
        current[trend_id] = {
            "share": share,
            "status": trend.get("status"),
            "lifecycle": lifecycle,
            "first_seen": first_seen,
            "last_seen": generated_on,
            "missing_runs": 0,
        }

    for trend_id, old in {**same_week, **previous}.items():
        if trend_id in current:
            continue
        missing = old.get("missing_runs", 0)
        if not isinstance(missing, int) or isinstance(missing, bool):
            missing = 0
        if missing + 1 < max_missing_runs:
            current[trend_id] = {
                **old,
                "share": 0.0,
                "lifecycle": "absent",
                "first_seen": old.get("first_seen") or generated_on,
                "missing_runs": missing + 1,
            }

    return {**history, key: current}


__all__ = [
    "SCHEMA_VERSION", "MAX_AGE", "EDITORIAL_TYPES", "CATEGORIES", "LONGEVITY",
    "REASONS", "OUTDATED_BASELINE", "build_context", "build_registry", "doc_issue",
    "eligible", "expected_confidence", "validate", "render_prompt", "run_analysis",
    "run_key", "update_tracking", "apply_lifecycle", "PROMPT_TEMPLATE",
]
