import json
import os
import shutil
import tempfile
import unittest

from _load import load, example

panel = load("founder-consumer", "panel")


def customer():
    with open(example("founder-consumer", "customer.example.json"), encoding="utf-8") as fh:
        return json.load(fh)


class Deal(unittest.TestCase):
    def test_same_seed_same_cards(self):
        self.assertEqual(panel.deal(customer(), 100, 7), panel.deal(customer(), 100, 7))
        self.assertNotEqual(panel.deal(customer(), 100, 7), panel.deal(customer(), 100, 8))

    def test_quotas_are_exact_and_names_unique(self):
        cards = panel.deal(customer(), 100, 3)
        segs = {}
        for c in cards:
            segs[c["segment"]] = segs.get(c["segment"], 0) + 1
        self.assertEqual(segs, {"Student or trainee": 25, "Early-career professional": 45,
                                "Senior professional or tech worker": 30})
        self.assertEqual(len({c["name"] for c in cards}), 100)
        self.assertEqual(cards[0]["id"], "P001")
        self.assertEqual(cards[-1]["id"], "P100")
        for c in cards:
            seg = next(s for s in customer()["segments"] if s["name"] == c["segment"])
            self.assertTrue(seg["income"][0] - 500 <= c["income"] <= seg["income"][1] + 500)
            self.assertIn(c["objection"], customer()["objections"])

    def test_bad_profile_is_refused(self):
        c = customer()
        del c["objections"]
        with self.assertRaises(panel.PanelError):
            panel.deal(c)


class Flow(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        panel.init(self.d, example("founder-consumer", "customer.example.json"),
                   example("founder-consumer", "pitch.example.md"), n=20, seed=5)

    def tearDown(self):
        shutil.rmtree(self.d)

    def answer(self, pid, buys, code="price", **extra):
        a = {"id": pid, "buys": buys, "reason_code": code, "reason": "because %s" % pid,
             "purchases_first_month": 4 if buys else 0, "would_change_my_mind": "" if buys else "a lower price"}
        a.update(extra)
        with open(os.path.join(self.d, "answers", pid + ".json"), "w") as fh:
            json.dump(a, fh)

    def test_briefs_carry_the_card_and_the_pitch(self):
        waves = panel.write_briefs(self.d, wave=10)
        self.assertEqual([len(w) for w in waves], [10, 10])
        with open(waves[0][0][1], encoding="utf-8") as fh:
            brief = fh.read()
        self.assertIn("Moos Matcha Bar", brief)
        self.assertIn('"id": "P001"', brief)
        self.assertIn("Do not be agreeable", brief)
        self.assertIn("Berlin, around Rosenthaler Platz", brief)
        self.assertRegex(brief, r"You earn about [0-9.]+ € a year")
        self.assertNotIn("$", brief)

    def test_answered_buyers_get_no_new_brief(self):
        self.answer("P001", True, "quality")
        ids = [j[0] for w in panel.write_briefs(self.d) for j in w]
        self.assertNotIn("P001", ids)
        self.assertEqual(len(ids), 19)

    def test_check_and_tally(self):
        for i in range(1, 21):
            pid = "P%03d" % i
            self.answer(pid, i <= 8, "quality" if i <= 8 else ("price" if i <= 15 else "habit"))
        # one broken answer: wrong reason code
        self.answer("P020", False, "vibes")
        probs = dict(panel.check(self.d))
        self.assertEqual(list(probs), ["P020"])
        res = panel.tally(self.d)
        self.assertEqual((res["buys"], res["passes"], res["answered"]), (8, 11, 19))
        self.assertEqual(res["why_not"][0][0], "price")
        self.assertEqual(res["why_not"][0][1], 7)
        self.assertEqual(res["skipped"][0][0], "P020")
        text = panel.results_md(res)
        self.assertIn("**8 buy · 11 pass**", text)
        self.assertIn("not customers", text)

    def test_save_files_a_printed_answer_and_refuses_junk(self):
        reply = 'Here is my answer:\n```json\n{"id": "P002", "buys": false, "reason_code": "price", "reason": "too much"}\n```'
        panel.save(self.d, "P002", reply)
        self.assertNotIn("P002", dict(panel.check(self.d)))
        with self.assertRaises(panel.PanelError):
            panel.save(self.d, "P003", '{"id": "P003", "buys": "maybe", "reason_code": "price", "reason": "x"}')
        self.assertEqual(dict(panel.check(self.d))["P003"], "missing")
        with self.assertRaises(panel.PanelError):
            panel.save(self.d, "P999", '{"id": "P999"}')

    def test_tally_with_no_answers_refuses(self):
        with self.assertRaises(panel.PanelError):
            panel.tally(self.d)

    def test_price_answers_with_decimal_commas_count(self):
        for i in range(1, 21):
            self.answer("P%03d" % i, True, "quality", price_too_cheap="2,50", price_cheap=4,
                        price_expensive="6.50", price_too_expensive=8)
        self.assertEqual(panel.tally(self.d)["price_answers"], 20)
        self.assertIsNone(panel._num("1.234"))

    def write_pitch(self, text):
        p = os.path.join(self.d, "pitch2.md")
        with open(p, "w") as fh:
            fh.write(text)
        return p

    def test_reinit_with_a_new_pitch_starts_clean_and_compares(self):
        # audit bug 2: a re-test must not reuse the old answers
        for i in range(1, 21):
            self.answer("P%03d" % i, i <= 5)
        res = panel.tally(self.d)
        panel._write_json(os.path.join(self.d, "results.json"), res)
        panel.init(self.d, example("founder-consumer", "customer.example.json"),
                   self.write_pitch("Moos Matcha Bar, now 4,90 € a cup."), n=20, seed=5)
        self.assertEqual(len(dict(panel.check(self.d))), 20)            # nobody has answered the new pitch
        self.assertEqual(sum(len(w) for w in panel.write_briefs(self.d)), 20)
        run1 = os.path.join(self.d, "runs", "run-1")
        self.assertTrue(os.path.exists(os.path.join(run1, "answers", "P001.json")))
        with open(os.path.join(self.d, "briefs", "P001.md"), encoding="utf-8") as fh:
            self.assertIn("4,90", fh.read())
        for i in range(1, 21):
            self.answer("P%03d" % i, i <= 12)
        panel._write_json(os.path.join(self.d, "results.json"), panel.tally(self.d))
        before, after = panel.compare(self.d)
        self.assertEqual((before["buys"], after["buys"]), (5, 12))
        self.assertIn("| after | 20 | 12 | 60% | 5 |", panel.compare_md(before, after))


class Quick(unittest.TestCase):
    def test_quick_deals_20(self):
        # audit bug 4: --quick used to be ignored
        d = tempfile.mkdtemp()
        try:
            rc = panel.main(["--dir", d, "init", "--customer", example("founder-consumer", "customer.example.json"),
                             "--pitch", example("founder-consumer", "pitch.example.md"), "--quick", "--seed", "1"])
            self.assertEqual(rc, 0)
            with open(os.path.join(d, "personas.json")) as fh:
                self.assertEqual(len(json.load(fh)), 20)
        finally:
            shutil.rmtree(d)


if __name__ == "__main__":
    unittest.main()
