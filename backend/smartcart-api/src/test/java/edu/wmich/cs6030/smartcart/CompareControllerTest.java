
package edu.wmich.cs6030.smartcart;

import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;

class CompareControllerTest {

    @Test
    void shouldReturnMatchingCandidateInApiResponse() {

        ProductRequest.Specifications specs =
                new ProductRequest.Specifications(
                        25.0, "French door", "Stainless", true
                );

        ProductRequest source = new ProductRequest(
                "Retailer A", "https://example.com/source",
                "Acme", "REF-100", "refrigerator",
                null, "USD", specs
        );

        ProductRequest candidate = new ProductRequest(
                "Retailer B", "https://example.com/candidate",
                "Acme", "REF-100", "refrigerator",
                null, "USD", specs
        );

        CandidateProductService candidateService =
                ignored -> List.of(candidate);

        CompareController controller = new CompareController(
                new MatchingService(),
                candidateService
        );

        CompareResponse response =
                controller.compare(new CompareRequest(source));

        assertEquals("REF-100", response.sourceModel());
        assertEquals(1, response.comparisons().size());
        assertEquals(
                "EXACT",
                response.comparisons().get(0).classification()
        );
        assertEquals(
                "Retailer B",
                response.comparisons().get(0).retailer()
        );
    }
}

