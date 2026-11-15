
package edu.wmich.cs6030.smartcart;

import java.math.BigDecimal;

public record ProductRequest(
        String retailer,
        String url,
        String brand,
        String model,
        String category,
        BigDecimal price,
        String currency,
        Specifications specifications
) {
    public record Specifications(
            Double capacityCubicFeet,
            String configuration,
            String finish,
            Boolean iceMaker
    ) {}
}

