
package edu.wmich.cs6030.smartcart;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.RowMapper;

import java.math.BigDecimal;
import java.sql.ResultSet;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

class PostgresCandidateProductServiceTest {

    private final JdbcTemplate jdbcTemplate = mock(JdbcTemplate.class);
    private final PostgresCandidateProductService service =
            new PostgresCandidateProductService(
                    jdbcTemplate, new ObjectMapper());

    @Test
    void missingBrandReturnsNoCandidates() {
        ProductRequest source = new ProductRequest(
                "Amazon", "https://example.com/source",
                null, "RF100", "refrigerator",
                null, "USD", null);

        assertTrue(service.findCandidates(source).isEmpty());
        verifyNoInteractions(jdbcTemplate);
    }

    @Test
    void nullSourceReturnsNoCandidates() {
        assertTrue(service.findCandidates(null).isEmpty());
        verifyNoInteractions(jdbcTemplate);
    }

    @Test
    void queryUsesSourceFields() {
        ProductRequest source = new ProductRequest(
                "Amazon", "https://example.com/source",
                "Acme", "RF100", "refrigerator",
                new BigDecimal("1200.00"), "USD", null);

        when(jdbcTemplate.query(
                anyString(),
                org.mockito.ArgumentMatchers
                        .<RowMapper<ProductRequest>>any(),
                any(Object[].class)))
                .thenReturn(List.of());

        assertTrue(service.findCandidates(source).isEmpty());

        verify(jdbcTemplate).query(
                argThat(sql ->
                        sql.contains("catalog.api_product_offers")
                        && sql.contains("LIMIT 50")
                        && sql.contains("source_url <>")),
                org.mockito.ArgumentMatchers
                        .<RowMapper<ProductRequest>>any(),
                eq("Acme"),
                eq("refrigerator"),
                eq("refrigerator"),
                eq("https://example.com/source"),
                eq("https://example.com/source"),
                eq("RF100"));
    }

    @Test
    void mapsDatabaseRowToProductRequest() throws Exception {
        ProductRequest source = new ProductRequest(
                "Amazon", "https://example.com/source",
                "Acme", "RF100", "refrigerator",
                null, "USD", null);

        ResultSet rs = mock(ResultSet.class);

        when(rs.getString("retailer")).thenReturn("Walmart");
        when(rs.getString("source_url"))
                .thenReturn("https://example.com/candidate");
        when(rs.getString("brand")).thenReturn("Acme");
        when(rs.getString("model")).thenReturn("RF100");
        when(rs.getString("category")).thenReturn("refrigerator");
        when(rs.getString("currency")).thenReturn("USD");
        when(rs.getBigDecimal("price_usd"))
                .thenReturn(new BigDecimal("1099.99"));
        when(rs.getString("specifications")).thenReturn("""
                {
                  "capacityCubicFeet": 25.0,
                  "configuration": "French door",
                  "finish": "Stainless",
                  "iceMaker": true
                }
                """);

        when(jdbcTemplate.query(
                anyString(),
                org.mockito.ArgumentMatchers
                        .<RowMapper<ProductRequest>>any(),
                any(Object[].class)))
                .thenAnswer(invocation -> {
                    RowMapper<ProductRequest> mapper =
                            invocation.getArgument(1);
                    return List.of(mapper.mapRow(rs, 0));
                });

        List<ProductRequest> candidates =
                service.findCandidates(source);

        assertEquals(1, candidates.size());

        ProductRequest candidate = candidates.get(0);

        assertEquals("Walmart", candidate.retailer());
        assertEquals("RF100", candidate.model());
        assertEquals(new BigDecimal("1099.99"), candidate.price());
        assertEquals(25.0,
                candidate.specifications().capacityCubicFeet());
        assertEquals("French door",
                candidate.specifications().configuration());
        assertEquals("Stainless",
                candidate.specifications().finish());
        assertTrue(candidate.specifications().iceMaker());
    }
}
