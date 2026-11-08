# Draft API contract (review together before coding)

`POST /api/v1/compare`

Request example: `contracts/compare-request.example.json`
Response example: `contracts/compare-response.example.json`

A source product contains: retailer, source URL, brand, model, category, price, currency, and observed specifications. Comparisons contain candidate identity, classification, reasons and supporting evidence.

Rules to agree on:
- Exact requires verified variant identity and no contradictory evidence.
- Equivalent and Near-equivalent are different categories; define attribute priority by product category.
- Missing evidence is not an invented match. Consider an `INSUFFICIENT_EVIDENCE` response status.
- All fixture data in starter files is synthetic and for contract tests, not claimed retailer observations.
