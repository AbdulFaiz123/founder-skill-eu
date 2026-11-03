import json
import os
import shutil
import tempfile
import unittest

from _load import load, example

plan = load("founder-plan", "compile")


class Compile(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        with open(os.path.join(self.d, "idea.md"), "w") as fh:
            fh.write("# Moos Matcha Bar\n\nA walk-in matcha cafe at Rosenthaler Platz, Berlin.\n")

    def tearDown(self):
        shutil.rmtree(self.d)

    def numbers(self, **change):
        with open(example("founder-cfo", "example.json")) as fh:
            s = json.load(fh)
        s.update(change)
        with open(os.path.join(self.d, "numbers.json"), "w") as fh:
            json.dump(s, fh)

    def panel(self, buys, n=100):
        os.makedirs(os.path.join(self.d, "panel"), exist_ok=True)
        with open(os.path.join(self.d, "panel", "results.json"), "w") as fh:
            json.dump({"buys": buys, "passes": n - buys, "answered": n, "buy_rate": buys / float(n)}, fh)

    def test_no_numbers_is_incomplete(self):
        v, text = plan.compile_plan(self.d)
        self.assertEqual(v, "Incomplete")
        self.assertIn("run /founder-cfo", text)

    def test_good_numbers_and_panel_is_profitable(self):
        self.numbers()
        self.panel(40)
        v, text = plan.compile_plan(self.d)
        self.assertEqual(v, "Profitable")
        self.assertTrue(text.startswith("# Moos Matcha Bar · Business plan"))
        self.assertIn("| Profit margin at plan | 41% per cup |", text)
        self.assertIn("| Price | 5,90 € a cup (4,96 € net, 19% VAT) |", text)
        self.assertNotIn("$", text)
        self.assertIn("40 buy · 60 pass", text)
        self.assertIn("- The buyer panel: run /founder-consumer", text.replace("## Not done yet", ""))

    def test_a_weak_panel_means_not_yet(self):
        self.numbers()
        self.panel(12)
        v, text = plan.compile_plan(self.d)
        self.assertEqual(v, "Not yet")
        self.assertIn("✗ 12 of 100 simulated buyers buy", text)

    def test_losing_money_means_not_yet(self):
        self.numbers(price="1,50")
        v, _ = plan.compile_plan(self.d)
        self.assertEqual(v, "Not yet")

    def test_missing_costs_are_incomplete_not_profitable(self):
        # audit bug 1: {"price": 100, "plan_per_day": 1} used to compile to Profitable
        with open(os.path.join(self.d, "numbers.json"), "w") as fh:
            json.dump({"price": 100, "plan_per_day": 1, "vat_rate": 0.19}, fh)
        v, text = plan.compile_plan(self.d)
        self.assertEqual(v, "Incomplete")
        self.assertIn("missing variable, fixed_monthly, startup", text)

    def test_outgrowing_kleinunternehmer_is_not_yet(self):
        self.numbers(kleinunternehmer=True)
        self.panel(40)
        v, text = plan.compile_plan(self.d)
        self.assertEqual(v, "Not yet")
        self.assertIn("Kleinunternehmer", text)


if __name__ == "__main__":
    unittest.main()
