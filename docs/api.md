# Draft comparison API

**Endpoint:** `POST /api/v1/compare`

- Example request: [`api-examples/compare-request.example.json`](api-examples/compare-request.example.json)
- Example response: [`api-examples/compare-response.example.json`](api-examples/compare-response.example.json)

The request describes the product the user is viewing: retailer, URL, brand, model, category, price and known specifications.

The response lists matching candidates, their classification and reasons. The proposed four classifications are `EXACT`, `EQUIVALENT`, `NEAR_EQUIVALENT` and `DIFFERENT`.

If there is too little reliable information, the API must indicate **insufficient evidence** instead of making an unsupported match. This can be represented separately from the four match classes.

**Important:** These JSON files are synthetic examples used to agree on the format. The API contract and classification rules will be finalized by the team before integration.
