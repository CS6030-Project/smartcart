import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

class ContractExamples(unittest.TestCase):
    def test_request_has_fields(self):
        data = json.loads((ROOT/'contracts/compare-request.example.json').read_text())
        p = data['product']
        self.assertTrue(all(k in p for k in ['brand','model','category','retailer','url','specifications']))
        self.assertTrue(p['url'].startswith('https://'))

    def test_response_has_explanation(self):
        data = json.loads((ROOT/'contracts/compare-response.example.json').read_text())
        self.assertTrue(data['comparisons'])
        for item in data['comparisons']:
            self.assertIn(item['classification'], {'EXACT','EQUIVALENT','NEAR_EQUIVALENT','DIFFERENT'})
            self.assertTrue(item['reasons'])

if __name__ == '__main__':
    unittest.main()
