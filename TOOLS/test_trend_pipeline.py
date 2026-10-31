import copy
import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import trend_pipeline as tp  # noqa: E402

NOW = datetime(2026, 10, 28, 12, 0, tzinfo=timezone.utc)
A = "https://a.example/story"
B = "https://b.example/story"
C = "https://c.example/runway"
D = "https://d.example/new-in"
E = "https://e.example/old"
F = "https://f.example/future"


def make_registry():
    return tp.build_registry([
        {"url": A, "publisher": "Alpha", "publisher_group": "Alpha Group",
         "source_type": "editorial", "publish_date": "2026-10-01", "season_covered": None,
         "text": "Deep burgundy and sculpted layers."},
        {"url": B, "publisher": "Beta", "publisher_group": "Beta Media",
         "source_type": "editorial", "publish_date": "2026-09-20", "season_covered": None,
         "text": "Leather and burgundy return."},
        {"url": C, "publisher": "Gamma", "publisher_group": "Gamma Runway",
         "source_type": "runway_report", "publish_date": "2026-03-01", "season_covered": "AW2026",
         "text": "Waisted coats and deep colour."},
        {"url": D, "publisher": "Delta", "publisher_group": "Delta Retail",
         "source_type": "retailer", "publish_date": "2026-10-20", "season_covered": None,
         "text": "New burgundy bags."},
        {"url": E, "publisher": "Epsilon", "publisher_group": "Epsilon Media",
         "source_type": "editorial", "publish_date": "2026-06-01", "season_covered": None,
         "text": "Too old for the 90-day window."},
        {"url": F, "publisher": "Zeta", "publisher_group": "Zeta Media",
         "source_type": "editorial", "publish_date": "2026-11-10", "season_covered": None,
         "text": "Future dated."},
    ])


def make_brief():
    context, runway = tp.build_context(6, now=NOW)
    trend = {
        "id": "burgundy-accent",
        "category": "color",
        "longevity": "lasting",
        "name": "Burgundy accent",
        "description": "Deep burgundy adds warmth to neutral outfits.",
        "status": "confirmed",
        "editorial_sources": [A, B, C],
        "retail_sources": [D],
        "fading_sources": [],
        "editorial_count": 3,
        "retail_count": 1,
        "fading_signals": 0,
        "conflict": False,
        "conflict_note": "",
        "confidence": 0.85,
        "pairs_well_with": ["sculpted-waist"],
        "style_tip": "Use one burgundy layer with olive or charcoal.",
    }
    second = copy.deepcopy(trend)
    second.update({
        "id": "sculpted-waist",
        "category": "silhouette",
        "name": "Sculpted waist",
        "description": "A defined waist returns through belts and tailored coats.",
        "pairs_well_with": ["burgundy-accent"],
        "style_tip": "Belt a long coat, keep the layers underneath clean.",
    })
    brief = {
        "schema_version": tp.SCHEMA_VERSION,
        "generated_on": "2026-10-28",
        "run_context": {
            "season": context["SEASON_LABEL"],
            "hemisphere": "northern",
            "documents_received": 6,
        },
        "overall_direction": "The season moves toward deep colour and sculpted layers. Practical outerwear stays central.",
        "capsule_formula": {
            "basics_percent": None,
            "statement_percent": None,
            "ratio_source_url": None,
            "notes": "",
        },
        "sources_used": [A, B, C, D],
        "sources_ignored": [
            {"url": E, "reason": "too_old"},
            {"url": F, "reason": "future_date"},
        ],
        "trends": [trend, second],
        "palette": {
            "accent_colors": [{"name": "Burgundy", "hex": "#6B1F2A"}],
            "base_neutrals": [
                {"name": "Olive", "hex": "#556B2F"},
                {"name": "Charcoal", "hex": "#36454F"},
            ],
            "proven_pairings": [["burgundy", "olive"], ["burgundy", "charcoal"]],
        },
        "outdated_to_avoid": [
            "skinny jeans",
            "all-beige minimalism",
            "millennial pink",
            "2016-2020 Instagram-era looks",
        ],
        "revived_items": [],
    }
    return brief, context, runway


class ContextTests(unittest.TestCase):
    def test_northern_october(self):
        context, runway = tp.build_context(6, now=NOW)
        self.assertEqual(context["CURRENT_DATE"], "2026-10-28")
        self.assertEqual(context["SEASON_LABEL"], "AW2026")
        self.assertEqual(context["SEASON"], "autumn/winter")
        self.assertEqual(runway, ["AW2026", "SS2027"])

    def test_northern_january(self):
        context, runway = tp.build_context(1, now=datetime(2026, 1, 15, tzinfo=timezone.utc))
        self.assertEqual(context["SEASON_LABEL"], "AW2025")
        self.assertEqual(runway, ["AW2025", "SS2026"])

    def test_northern_april_and_august(self):
        for month in (4, 8):
            context, runway = tp.build_context(1, now=datetime(2026, month, 15, tzinfo=timezone.utc))
            self.assertEqual(context["SEASON_LABEL"], "SS2026")
            self.assertEqual(runway, ["SS2026", "AW2026"])

    def test_southern_october(self):
        context, runway = tp.build_context(1, hemisphere="southern", now=NOW)
        self.assertEqual(context["SEASON_LABEL"], "SS2026")
        self.assertEqual(runway, ["SS2026", "AW2026"])

    def test_bad_hemisphere(self):
        with self.assertRaises(ValueError):
            tp.build_context(1, hemisphere="equator", now=NOW)


class RegistryAndEligibilityTests(unittest.TestCase):
    def test_registry_requires_unique_urls(self):
        with self.assertRaises(ValueError):
            tp.build_registry([{"url": A}, {"url": A}])
        with self.assertRaises(ValueError):
            tp.build_registry([{"publisher": "No URL"}])

    def test_doc_issue(self):
        registry = make_registry()
        _, runway = tp.build_context(6, now=NOW)
        self.assertIsNone(tp.doc_issue(registry[A], NOW, runway))
        self.assertEqual(tp.doc_issue(registry[E], NOW, runway), "too_old")
        self.assertEqual(tp.doc_issue(registry[F], NOW, runway), "future_date")
        bad = {"source_type": "editorial", "publish_date": "not-a-date",
               "publisher_group": "X"}
        self.assertEqual(tp.doc_issue(bad, NOW, runway), "unverifiable")
        off = {"source_type": "runway_report", "publish_date": "2026-09-01",
               "publisher_group": "X", "season_covered": "SS2026"}
        self.assertEqual(tp.doc_issue(off, NOW, runway), "off_season")
        no_season = {"source_type": "runway_report", "publish_date": "2026-09-01",
                     "publisher_group": "X", "season_covered": None}
        self.assertEqual(tp.doc_issue(no_season, NOW, runway), "unverifiable")

    def test_expected_confidence(self):
        self.assertEqual(tp.expected_confidence(1, 0, False, False), 0.30)
        self.assertEqual(tp.expected_confidence(2, 1, False, False), 0.60)
        self.assertEqual(tp.expected_confidence(3, 0, True, False), 0.75)
        self.assertEqual(tp.expected_confidence(4, 1, True, True), 0.75)
        self.assertEqual(tp.expected_confidence(0, 0, False, False), 0.05)


class ValidatorTests(unittest.TestCase):
    def setUp(self):
        self.registry = make_registry()
        self.brief, self.context, self.runway = make_brief()

    def validate(self, brief):
        return tp.validate(json.dumps(brief, ensure_ascii=False), self.registry,
                           self.runway, self.context, NOW)

    def assert_invalid(self, brief, needle):
        result, errors = self.validate(brief)
        self.assertIsNone(result, errors)
        self.assertTrue(any(needle in error for error in errors),
                        f"{needle!r} not in {errors}")

    def test_valid_brief(self):
        result, errors = self.validate(self.brief)
        self.assertEqual(errors, [])
        self.assertIsNotNone(result)

    def test_schema_and_context(self):
        bad = copy.deepcopy(self.brief)
        bad["schema_version"] = "1.0"
        self.assert_invalid(bad, "schema_version")
        bad = copy.deepcopy(self.brief)
        bad["generated_on"] = "2026-10-27"
        self.assert_invalid(bad, "generated_on")
        bad = copy.deepcopy(self.brief)
        bad["run_context"]["season"] = "SS2026"
        self.assert_invalid(bad, "run_context.season")
        bad = copy.deepcopy(self.brief)
        bad["run_context"]["documents_received"] = 5
        self.assert_invalid(bad, "documents_received")

    def test_recomputed_counts_and_status(self):
        for field, value, needle in (
            ("editorial_count", 4, "editorial_count"),
            ("retail_count", 0, "retail_count"),
            ("status", "emerging", "status"),
            ("confidence", 0.70, "confidence"),
        ):
            bad = copy.deepcopy(self.brief)
            bad["trends"][0][field] = value
            self.assert_invalid(bad, needle)

    def test_fading_is_recounted_from_urls(self):
        bad = copy.deepcopy(self.brief)
        trend = bad["trends"][0]
        trend.update({
            "fading_sources": [A],
            "fading_signals": 2,
        })
        self.assert_invalid(bad, "fading_signals must be 1")

        bad = copy.deepcopy(self.brief)
        trend = bad["trends"][0]
        trend.update({
            "fading_sources": [A],
            "fading_signals": 1,
            "status": "emerging",
            "conflict": True,
            "conflict_note": "One publisher calls it over while two support it.",
            "confidence": 0.65,
        })
        result, errors = self.validate(bad)
        self.assertEqual(errors, [])
        self.assertIsNotNone(result)

        bad = copy.deepcopy(self.brief)
        bad["trends"][0]["fading_sources"] = [D]
        self.assert_invalid(bad, "fading URL must also be in editorial_sources")

    def test_sources_accounting(self):
        bad = copy.deepcopy(self.brief)
        bad["sources_ignored"] = [{"url": E, "reason": "too_old"}]
        self.assert_invalid(bad, "unaccounted")
        bad = copy.deepcopy(self.brief)
        bad["sources_ignored"].append({"url": A, "reason": "too_old"})
        self.assert_invalid(bad, "both used and ignored")
        bad = copy.deepcopy(self.brief)
        bad["sources_used"].append(A)
        self.assert_invalid(bad, "duplicate URLs")
        bad = copy.deepcopy(self.brief)
        bad["sources_ignored"][0]["reason"] = "no_trend_content"
        self.assert_invalid(bad, "too_old")
        bad = copy.deepcopy(self.brief)
        bad["sources_ignored"][1]["reason"] = "too_old"
        self.assert_invalid(bad, "future_date")

    def test_duplicate_reason_needs_target(self):
        dup = "https://dup.example/story"
        registry = dict(self.registry)
        registry[dup] = {
            "id": "d7", "url": dup, "publisher": "Dup", "publisher_group": "Dup Group",
            "source_type": "editorial", "publish_date": "2026-10-01",
            "season_covered": None, "text": "Syndicated copy.",
        }
        context = {**self.context, "N": 7}
        brief = copy.deepcopy(self.brief)
        brief["run_context"]["documents_received"] = 7
        brief["sources_ignored"].append({"url": dup, "reason": "duplicate"})
        result, errors = tp.validate(json.dumps(brief, ensure_ascii=False), registry,
                                     self.runway, context, NOW)
        self.assertIsNone(result)
        self.assertTrue(any("duplicate_of" in error for error in errors), errors)

        brief["sources_ignored"][-1]["duplicate_of"] = A
        result, errors = tp.validate(json.dumps(brief, ensure_ascii=False), registry,
                                     self.runway, context, NOW)
        self.assertEqual(errors, [])
        self.assertIsNotNone(result)

        brief["sources_ignored"][-1]["duplicate_of"] = dup
        result, errors = tp.validate(json.dumps(brief, ensure_ascii=False), registry,
                                     self.runway, context, NOW)
        self.assertIsNone(result)
        self.assertTrue(any("duplicate_of" in error for error in errors), errors)

    def test_trend_urls_must_be_eligible_and_typed(self):
        bad = copy.deepcopy(self.brief)
        bad["trends"][0]["editorial_sources"] = [A, B, E]
        bad["sources_used"].append(E)
        self.assert_invalid(bad, "ineligible editorial URL")
        bad = copy.deepcopy(self.brief)
        bad["trends"][0]["editorial_sources"] = [A, B, D]
        self.assert_invalid(bad, "not an editorial/runway source")
        bad = copy.deepcopy(self.brief)
        bad["trends"][0]["retail_sources"] = [A]
        self.assert_invalid(bad, "not a retailer source")

    def test_capsule_formula(self):
        bad = copy.deepcopy(self.brief)
        bad["capsule_formula"] = {"basics_percent": 60, "statement_percent": 50,
                                  "ratio_source_url": A, "notes": ""}
        self.assert_invalid(bad, "summing to 100")
        bad = copy.deepcopy(self.brief)
        bad["capsule_formula"] = {"basics_percent": -10, "statement_percent": 110,
                                  "ratio_source_url": A, "notes": ""}
        self.assert_invalid(bad, "summing to 100")
        bad = copy.deepcopy(self.brief)
        bad["capsule_formula"] = {"basics_percent": True, "statement_percent": 99,
                                  "ratio_source_url": A, "notes": ""}
        self.assert_invalid(bad, "summing to 100")
        bad = copy.deepcopy(self.brief)
        bad["capsule_formula"] = {"basics_percent": None, "statement_percent": None,
                                  "ratio_source_url": A, "notes": ""}
        self.assert_invalid(bad, "ratio_source_url must be null")
        good = copy.deepcopy(self.brief)
        good["capsule_formula"] = {"basics_percent": 70, "statement_percent": 30,
                                   "ratio_source_url": D, "notes": "Retailer ratio."}
        result, errors = self.validate(good)
        self.assertEqual(errors, [])
        self.assertIsNotNone(result)

    def test_direction_and_revival(self):
        bad = copy.deepcopy(self.brief)
        bad["overall_direction"] = "One sentence only."
        self.assert_invalid(bad, "2-3 sentences")
        bad = copy.deepcopy(self.brief)
        bad["outdated_to_avoid"].remove("millennial pink")
        self.assert_invalid(bad, "millennial pink")
        good = copy.deepcopy(self.brief)
        good["outdated_to_avoid"].remove("skinny jeans")
        good["revived_items"] = [{"item": "skinny jeans", "sources": [A]}]
        result, errors = self.validate(good)
        self.assertEqual(errors, [])
        self.assertIsNotNone(result)
        bad = copy.deepcopy(good)
        bad["revived_items"][0]["sources"] = [D]
        self.assert_invalid(bad, "eligible editorial source")
        bad = copy.deepcopy(good)
        bad["outdated_to_avoid"].append("skinny jeans")
        self.assert_invalid(bad, "must not be in outdated_to_avoid")

    def test_pairs_and_palette(self):
        bad = copy.deepcopy(self.brief)
        bad["trends"][0]["pairs_well_with"] = ["missing-trend"]
        self.assert_invalid(bad, "unknown trend")
        bad = copy.deepcopy(self.brief)
        bad["trends"][0]["pairs_well_with"] = ["burgundy-accent"]
        self.assert_invalid(bad, "exclude itself")
        bad = copy.deepcopy(self.brief)
        bad["palette"]["accent_colors"] = []
        self.assert_invalid(bad, "accent_colors")
        bad = copy.deepcopy(self.brief)
        bad["palette"]["accent_colors"][0]["hex"] = "#FFF"
        self.assert_invalid(bad, "hex must be #RRGGBB")
        bad = copy.deepcopy(self.brief)
        bad["palette"]["proven_pairings"].append(["burgundy", "silver"])
        self.assert_invalid(bad, "unknown color")

    def test_malformed_outputs_do_not_crash(self):
        cases = [
            None,
            123,
            "[]",
            "{}",
            "not json",
            json.dumps({**self.brief, "sources_used": {}}),
            json.dumps({**self.brief, "sources_ignored": "x"}),
            json.dumps({**self.brief, "trends": "x"}),
            json.dumps({**self.brief, "trends": [[]]}),
            json.dumps({**self.brief, "palette": []}),
            json.dumps({**self.brief, "run_context": "x"}),
            json.dumps({**self.brief, "capsule_formula": "x"}),
            json.dumps({**self.brief, "outdated_to_avoid": "x"}),
            json.dumps({**self.brief, "trends": [{**self.brief["trends"][0], "pairs_well_with": [[]]}]}),
        ]
        for raw in cases:
            with self.subTest(raw=str(raw)[:60]):
                result, errors = tp.validate(raw, self.registry, self.runway, self.context, NOW)
                self.assertIsNone(result)
                self.assertTrue(errors)

    def test_prompt_rendering(self):
        prompt = tp.render_prompt(self.context, self.registry)
        self.assertIn("[DOC d1]", prompt)
        self.assertIn(A, prompt)
        self.assertNotIn("{{CURRENT_DATE}}", prompt)
        self.assertNotIn("{{SEASON_LABEL}}", prompt)
        self.assertIn('"fading_sources"', prompt)
        self.assertIn('"longevity"', prompt)
        self.assertIn('"revived_items"', prompt)


class RunAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.registry = make_registry()
        self.brief, self.context, self.runway = make_brief()
        self.prompt = tp.render_prompt(self.context, self.registry)

    def test_first_valid_output(self):
        calls = []

        def call(prompt):
            calls.append(prompt)
            return json.dumps(self.brief, ensure_ascii=False)

        result = tp.run_analysis(self.prompt, call, self.registry, self.runway, self.context, NOW)
        self.assertIsNotNone(result)
        self.assertEqual(len(calls), 1)

    def test_retry_after_bad_output(self):
        calls = []

        def call(prompt):
            calls.append(prompt)
            return "not json" if len(calls) == 1 else json.dumps(self.brief, ensure_ascii=False)

        result = tp.run_analysis(self.prompt, call, self.registry, self.runway, self.context, NOW)
        self.assertIsNotNone(result)
        self.assertEqual(len(calls), 2)
        self.assertIn("failed validation", calls[1])

    def test_retry_after_exception(self):
        calls = []

        def call(prompt):
            calls.append(prompt)
            if len(calls) == 1:
                raise RuntimeError("network down")
            return json.dumps(self.brief, ensure_ascii=False)

        result = tp.run_analysis(self.prompt, call, self.registry, self.runway, self.context, NOW)
        self.assertIsNotNone(result)
        self.assertEqual(len(calls), 2)

    def test_gives_up(self):
        result = tp.run_analysis(self.prompt, lambda prompt: "not json", self.registry,
                                 self.runway, self.context, NOW, max_retries=1)
        self.assertIsNone(result)


class TrackingTests(unittest.TestCase):
    def setUp(self):
        self.registry = make_registry()
        self.brief, _, _ = make_brief()

    def test_first_run_and_idempotency(self):
        history = tp.update_tracking(self.brief, self.registry, None)
        key = tp.run_key(self.brief)
        self.assertEqual(key, "2026-W44")
        record = history[key]["burgundy-accent"]
        self.assertEqual(record["lifecycle"], "new")
        self.assertEqual(record["first_seen"], "2026-10-28")
        self.assertEqual(record["share"], 1.0)
        again = tp.update_tracking(self.brief, self.registry, history)
        self.assertEqual(again[key], history[key])

    def test_rising_stable_and_absent(self):
        low = copy.deepcopy(self.brief)
        low["trends"][0]["editorial_count"] = 2
        low["trends"][0]["status"] = "emerging"
        history = tp.update_tracking(low, self.registry, None)
        self.assertEqual(history["2026-W44"]["burgundy-accent"]["share"], 0.667)
        rising = copy.deepcopy(self.brief)
        rising["generated_on"] = "2026-11-04"
        history = tp.update_tracking(rising, self.registry, history)
        self.assertEqual(history["2026-W45"]["burgundy-accent"]["lifecycle"], "rising")

        stable = copy.deepcopy(rising)
        stable["generated_on"] = "2026-11-11"
        history = tp.update_tracking(stable, self.registry, history)
        self.assertEqual(history["2026-W46"]["burgundy-accent"]["lifecycle"], "stable")

        absent = copy.deepcopy(stable)
        absent["generated_on"] = "2026-11-18"
        absent["trends"] = []
        history = tp.update_tracking(absent, self.registry, history)
        record = history["2026-W47"]["burgundy-accent"]
        self.assertEqual(record["lifecycle"], "absent")
        self.assertEqual(record["missing_runs"], 1)
        self.assertEqual(record["first_seen"], "2026-10-28")

        absent2 = copy.deepcopy(absent)
        absent2["generated_on"] = "2026-11-25"
        history = tp.update_tracking(absent2, self.registry, history)
        self.assertEqual(history["2026-W48"]["burgundy-accent"]["missing_runs"], 2)

        absent3 = copy.deepcopy(absent)
        absent3["generated_on"] = "2026-12-02"
        history = tp.update_tracking(absent3, self.registry, history)
        self.assertNotIn("burgundy-accent", history["2026-W49"])

    def test_apply_lifecycle(self):
        low = copy.deepcopy(self.brief)
        low["trends"][0]["editorial_count"] = 2
        history = tp.update_tracking(low, self.registry, None)
        brief = copy.deepcopy(low)
        result = tp.apply_lifecycle(brief, history)
        self.assertIs(result, brief)
        self.assertEqual(brief["trends"][0]["lifecycle"], "new")

        rising = copy.deepcopy(self.brief)
        rising["generated_on"] = "2026-11-04"
        rising["trends"][0]["editorial_count"] = 3
        history = tp.update_tracking(rising, self.registry, history)
        tp.apply_lifecycle(rising, history)
        self.assertEqual(rising["trends"][0]["lifecycle"], "rising")

        missing = copy.deepcopy(self.brief)
        tp.apply_lifecycle(missing, {})
        self.assertNotIn("lifecycle", missing["trends"][0])

    def test_old_records_without_fields(self):
        history = {"2026-W43": {"legacy": {"first_seen": "2026-09-01"}}}
        result = tp.update_tracking(self.brief, self.registry, history)
        self.assertEqual(result["2026-W44"]["legacy"]["lifecycle"], "absent")
        self.assertEqual(result["2026-W44"]["legacy"]["missing_runs"], 1)

    def test_bad_run_key(self):
        bad = copy.deepcopy(self.brief)
        bad["generated_on"] = "28.10.2026"
        with self.assertRaises(ValueError):
            tp.run_key(bad)
        with self.assertRaises(ValueError):
            tp.update_tracking(bad, self.registry, {})


if __name__ == "__main__":
    unittest.main(verbosity=2)
