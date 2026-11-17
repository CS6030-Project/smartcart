
package edu.wmich.cs6030.smartcart;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.context.annotation.Profile;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
@Profile("db")
public class PostgresCandidateProductService implements CandidateProductService {

    private final JdbcTemplate jdbcTemplate;
    private final ObjectMapper objectMapper;

    public PostgresCandidateProductService(
            JdbcTemplate jdbcTemplate,
            ObjectMapper objectMapper) {
        this.jdbcTemplate = jdbcTemplate;
        this.objectMapper = objectMapper;
    }

    @Override
    public List<ProductRequest> findCandidates(ProductRequest source) {
        if (source == null || source.brand() == null
                || source.brand().isBlank()) {
            return List.of();
        }

        String sql = """
		SELECT retailer, source_url, manufacturer AS brand, manufacturer_model AS model,
                       category, price_usd, currency, specifications
                FROM catalog.api_product_offers
		WHERE lower(manufacturer) = lower(?)
		  AND (CAST(? AS TEXT) IS NULL OR category = ?)
		  AND (CAST(? AS TEXT) IS NULL OR source_url <> ?)
                ORDER BY
			CASE WHEN lower(manufacturer_model) = lower(?) THEN 0 ELSE 1 END,
                    collected_at DESC
                LIMIT 50
                """;

        return jdbcTemplate.query(
                sql,
                (rs, rowNum) -> {
                    String json = rs.getString("specifications");

                    ProductRequest.Specifications specs;
                    try {
                        specs = objectMapper.readValue(
                                json, ProductRequest.Specifications.class);
                    } catch (Exception e) {
                        throw new IllegalStateException(
                                "Invalid product specifications JSON", e);
                    }

                    return new ProductRequest(
                            rs.getString("retailer"),
                            rs.getString("source_url"),
                            rs.getString("brand"),
                            rs.getString("model"),
                            rs.getString("category"),
                            rs.getBigDecimal("price_usd"),
                            rs.getString("currency"),
                            specs
                    );
                },
                source.brand(),
                source.category(), source.category(),
                source.url(), source.url(),
                source.model()
        );
    }
}
