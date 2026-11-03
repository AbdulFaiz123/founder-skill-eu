import json
import math
import unittest

from _load import load, example

ue = load("founder-cfo", "unit_economics")


def spec():
    with open(example("founder-cfo", "example.json"), encoding="utf-8") as fh:
        return json.load(fh)


class UnitEconomics(unittest.TestCase):
    def test_example_reproduces_the_plan(self):
        a = ue.analyse(spec())
        self.assertAlmostEqual(a["net_price"], 5.90 / 1.19, places=6)
        self.assertAlmostEqual(a["contribution"], 3.57, places=2)
        self.assertEqual(round(a["margin_at_plan"] * 100), 41)
        self.assertEqual(math.ceil(a["breakeven_per_day"]), 111)
        self.assertEqual(round(a["year1_profit"]), 103018)
        self.assertEqual(a["startup"], 27750)
        self.assertEqual(a["payback_month"], 7)
        self.assertEqual(round(a["cash_needed"]), 29958)
        self.assertEqual(a["flags"], [])
        self.assertEqual(a["missing"], [])

    def test_price_below_variable_cost_is_flagged(self):
        s = spec()
        s["price"] = "1,50"
        a = ue.analyse(s)
        self.assertTrue(math.isinf(a["breakeven_per_day"]))
        self.assertTrue(any("loses money" in f for f in a["flags"]))

    def test_breakeven_above_capacity_is_flagged(self):
        s = spec()
        s["capacity_per_day"] = 100
        a = ue.analyse(s)
        self.assertTrue(any("capacity is 100" in f for f in a["flags"]))

    def test_what_ifs_move_the_right_way(self):
        base = ue.analyse(spec())
        cheaper = ue.analyse(spec(), price=base["price"] * 0.9)
        fewer = ue.analyse(spec(), volume=0.8)
        self.assertLess(cheaper["year1_profit"], base["year1_profit"])
        self.assertGreater(cheaper["breakeven_per_day"], base["breakeven_per_day"])
        self.assertLess(fewer["year1_profit"], base["year1_profit"])
        self.assertEqual(len(ue.sensitivity(spec())), 4)

    def test_bad_input_is_refused_not_guessed(self):
        s = spec()
        s["ramp_per_day"] = [100] * 11
        with self.assertRaises(ue.NumbersError):
            ue.analyse(s)
        s = spec()
        del s["price"]
        with self.assertRaises(ue.NumbersError):
            ue.analyse(s)
        s = spec()
        s["variable"][0]["cost"] = "lots"
        with self.assertRaises(ue.NumbersError):
            ue.analyse(s)

    def test_report_mentions_the_key_numbers(self):
        s = spec()
        text = ue.report(s, ue.analyse(s))
        for needle in ("3,57 €", "111 cups a day", "**41%**", "103.018 €", "month 7", "-0,94 €",
                       "2.600 € gross + 546 € employer costs"):
            self.assertIn(needle, text)
        s["number_format"] = "en"
        self.assertIn("€103,018", ue.report(s, ue.analyse(s)))


class EU(unittest.TestCase):
    def test_vat_is_not_revenue(self):
        s = {"price": 11.9, "vat_rate": 0.19, "variable": [], "fixed_monthly": [], "startup": [],
             "plan_per_day": 1, "days_per_month": 10}
        a = ue.analyse(s)
        self.assertAlmostEqual(a["net_price"], 10.0)
        self.assertAlmostEqual(a["year1_revenue"], 1200.0)
        self.assertAlmostEqual(a["year1_vat"], 228.0)
        b2b = ue.analyse(dict(s, price=10, price_includes_vat=False))
        self.assertAlmostEqual(b2b["net_price"], 10.0)
        self.assertAlmostEqual(ue.analyse(dict(s, vat_rate=19))["net_price"], 10.0)

    def test_vat_rate_is_required_unless_kleinunternehmer(self):
        s = spec()
        del s["vat_rate"]
        with self.assertRaises(ue.NumbersError):
            ue.analyse(s)
        a = ue.analyse(dict(s, kleinunternehmer=True))
        self.assertAlmostEqual(a["net_price"], 5.90)

    def test_kleinunternehmer_limit_is_flagged(self):
        small = {"price": 10, "kleinunternehmer": True, "variable": [], "fixed_monthly": [], "startup": [],
                 "plan_per_day": 5, "days_per_month": 25}   # 1.250 EUR a month, 15.000 a year
        self.assertIsNone(ue.analyse(small)["kleinunternehmer_lost_month"])
        big = dict(small, plan_per_day=20)                    # 5.000 a month: passes 25.000 in month 6
        a = ue.analyse(big)
        self.assertEqual(a["kleinunternehmer_lost_month"], 6)
        self.assertTrue(any("Kleinunternehmer" in f for f in a["flags"]))

    def test_payroll_adds_employer_costs(self):
        s = {"price": 10, "vat_rate": 0, "variable": [], "fixed_monthly": [], "startup": [], "plan_per_day": 1,
             "payroll": [{"gross_monthly": 1000}, {"gross_monthly": "603", "kind": "minijob"}]}
        self.assertAlmostEqual(ue.analyse(s)["fixed_monthly"], 1000 * 1.21 + 603 * 1.31)
        s["payroll_oncost"] = {"regular": 0.2}
        self.assertAlmostEqual(ue.analyse(s)["fixed_monthly"], 1200 + 603 * 1.31)
        s["payroll"][0]["kind"] = "intern"
        with self.assertRaises(ue.NumbersError):
            ue.analyse(s)

    def test_missing_cost_sections_are_reported(self):
        a = ue.analyse({"price": 100, "plan_per_day": 1, "vat_rate": 0.19})
        self.assertEqual(a["missing"], ["variable", "fixed_monthly", "startup"])
        self.assertTrue(any("Missing" in f for f in a["flags"]))
        a = ue.analyse({"price": 100, "plan_per_day": 1, "vat_rate": 0.19, "variable": [], "startup": [],
                        "payroll": [{"gross_monthly": 500}]})
        self.assertEqual(a["missing"], [])


class ParseAmount(unittest.TestCase):
    def test_both_styles(self):
        for raw, want in (("5,90", 5.9), ("5.90", 5.9), ("1.234,56", 1234.56), ("1,234.56", 1234.56),
                          ("€ 6,50", 6.5), ("6,50 €", 6.5), ("1.234.567", 1234567), ("0,500", 0.5),
                          ("12", 12), (7, 7), (2.5, 2.5), ("1'234.50", 1234.5), ("-3,5", -3.5)):
            self.assertAlmostEqual(ue.parse_amount(raw), want, msg=raw)

    def test_ambiguous_and_junk_are_refused(self):
        for raw in ("1.234", "1,234", "lots", "", "1,2,3", True, None):
            with self.assertRaises(ue.NumbersError, msg=raw):
                ue.parse_amount(raw)


if __name__ == "__main__":
    unittest.main()
