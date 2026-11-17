# Draft comparison API

**Endpoint:** `POST /api/v1/compare`

- Example request: [`api-examples/compare-request.example.json`](api-examples/compare-request.example.json)
- Example response: [`api-examples/compare-response.example.json`](api-examples/compare-response.example.json)

## Request

The request describes the product the user is viewing.

Supported fields include retailer, URL, brand, model, category, price, currency, and specifications.

The backend accepts requests containing only a brand and model. Missing optional product attributes are represented as null.

## Response

The response contains the source model and a list of candidate comparisons.

Each comparison includes the candidate model, retailer, classification, reasons, evidence, price, currency, and URL.

## Match classifications

- `EXACT`: Same brand and model, with no conflicting known attributes.
- `EQUIVALENT`: Different product identity, but key observed specifications match.
- `NEAR_EQUIVALENT`: Similar products with some differences in observed specifications.
- `INSUFFICIENT_EVIDENCE`: Not enough reliable information to determine a match.
- `DIFFERENT`: Material differences prevent a match.

Missing specifications do not automatically prevent an `EXACT` classification when brand and model match.

Known conflicting attributes can prevent an `EXACT` classification.

## Result ordering

The backend sorts comparisons in this order:

1. `EXACT`
2. `EQUIVALENT`
3. `NEAR_EQUIVALENT`
4. `INSUFFICIENT_EVIDENCE`
5. `DIFFERENT`

## Current implementation status

The matching algorithm and comparison endpoint are implemented.

Candidate retrieval currently uses a placeholder service that returns an empty list. Database integration and retrieval of competing retailer listings are pending.

**Important:** The example JSON files contain synthetic data. The API contract and classification rules remain subject to team agreement before integration.
