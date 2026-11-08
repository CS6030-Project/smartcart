import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "docs" / "api-examples"


class ContractExamples(unittest.TestCase):
    def test_request_has_fields(self):
        data = json.loads((EXAMPLES / "compare-request.example.json").read_text())
        p = data["product"]
        required = ["brand", "model", "category", "retailer", "url", "specifications"]
        self.assertTrue(all(k in p for k in required))
        self.assertTrue(p["url"].startswith("https://"))

    def test_response_has_explanation(self):
        data = json.loads((EXAMPLES / "compare-response.example.json").read_text())
        self.assertTrue(data["comparisons"])
        valid = {"EXACT", "EQUIVALENT", "NEAR_EQUIVALENT", "DIFFERENT"}
        for item in data["comparisons"]:
            self.assertIn(item["classification"], valid)
            self.assertTrue(item["reasons"])


if __name__ == "__main__":
    unittest.main()
