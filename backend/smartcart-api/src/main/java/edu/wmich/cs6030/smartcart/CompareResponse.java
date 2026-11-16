
package edu.wmich.cs6030.smartcart;

import java.util.List;
import java.util.Map;

public record CompareResponse(
        String sourceModel,
        List<Comparison> comparisons
) {
    public record Comparison(
        String candidateModel,
        String retailer,
        String classification,
        List<String> reasons,
        Map<String, List<String>> evidence,
        java.math.BigDecimal price,
        String currency,
        String url
) {}
}

