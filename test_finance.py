"""Regression coverage for ledger imports, unknown values and portable exports."""

import json
import unittest
from datetime import date
import pandas as pd
from analytics import parse_amounts, grouped_data
from finance import (
    ledger_frame,
    monthly_snapshot,
    read_month_csv,
    export_workspace,
    restore_workspace,
    dashboard_html,
)


class FinanceTests(unittest.TestCase):
    def test_currency_parsing_and_invalid_values(self):
        d = parse_amounts(
            pd.Series(["₱ 1,200.50", "-25", "USD 45.00", "1,2", "bad", ""])
        )
        self.assertEqual(d[:3].tolist(), [1200.5, -25, 45])
        self.assertTrue(d[3:].isna().all())

    def test_month_title_and_explicit_year(self):
        d, title = read_month_csv(
            b"September\nDate,Description,Amount,Paid?\n5-Sep,Internet,1499,Yes\n"
        )
        self.assertEqual(title, "September")
        result = ledger_frame(
            d,
            {
                "Amount": "Amount",
                "Date": "Date",
                "Description": "Description",
                "Payment Status": "Paid?",
            },
            "D-Mon (year from import month)",
            "Bill",
            "bills.csv",
            date(2026, 9, 1),
        )
        self.assertEqual(result.iloc[0]["Month"], "2026-09")
        self.assertEqual(result.iloc[0]["Payment Status"], "Paid")

    def test_missing_coverage_and_unknown_status(self):
        d = pd.DataFrame(
            {
                "Date": ["2026-09-02", "2026-09-03"],
                "Amount": ["100", "200"],
                "Paid?": ["Yes", "maybe"],
            }
        )
        ledger = ledger_frame(
            d,
            {"Amount": "Amount", "Date": "Date", "Payment Status": "Paid?"},
            record_type="Bill",
        )
        snap = monthly_snapshot(
            ledger,
            {"2026-09": {"Income": 1000, "Net Worth": 3000}},
            ["2026-09", "2026-10"],
        )
        self.assertEqual(snap.iloc[0]["Bills"], 300)
        self.assertEqual(snap.iloc[0]["Unpaid Bills"], 0)
        self.assertEqual(snap.iloc[0]["Unknown Bill Status"], 200)
        self.assertTrue(pd.isna(snap.iloc[0]["Expenses"]))
        self.assertIsNone(snap.iloc[0]["Recorded Cash Flow"])
        self.assertTrue(pd.isna(snap.iloc[1]["Bills"]))

    def test_roundtrip_and_payload_validation(self):
        d = pd.DataFrame({"Amount": ["120", "bad"], "Date": ["2026-09-02", "bad"]})
        ledger = ledger_frame(d, {"Amount": "Amount", "Date": "Date"})
        snapshots = {"2026-09": {"Income": 2500, "Net Worth": None}}
        restored, saved, currency = restore_workspace(
            export_workspace(ledger, snapshots, "PHP")
        )
        self.assertEqual(len(restored), 2)
        self.assertTrue(pd.isna(restored.iloc[1].Amount))
        self.assertEqual(saved, snapshots)
        with self.assertRaises(ValueError):
            restore_workspace(b"[]")
        bad = json.loads(export_workspace(ledger, snapshots, "PHP"))
        bad["snapshots"]["2026-09"]["Income"] = "fake"
        with self.assertRaises(ValueError):
            restore_workspace(json.dumps(bad).encode())

    def test_grouped_totals_exclude_invalid_amounts(self):
        result, invalid = grouped_data(
            pd.DataFrame({"kind": ["A", "A", "B"], "value": ["1,000", "bad", "10"]}),
            "kind",
            "value",
            "Sum",
        )
        self.assertEqual(invalid, 1)
        self.assertEqual(result.set_index("Group").loc["A", "Value"], 1000)

    def test_html_safely_embeds_literal_descriptions(self):
        d = pd.DataFrame(
            {"Amount": ["12"], "Description": ["</script><script>bad()</script>"]}
        )
        ledger = ledger_frame(
            d,
            {"Amount": "Amount", "Description": "Description"},
            import_month=date(2026, 9, 1),
        )
        exported = dashboard_html(ledger, {}, "PHP", ["2026-09"]).decode()
        self.assertNotIn("</script><script>bad()", exported)
        self.assertIn("\\u003c/script\\u003e", exported)
        self.assertNotIn('src="https://', exported)


if __name__ == "__main__":
    unittest.main()
