

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
	
	assertEquals(
        	"USD",
        	response.comparisons().get(0).currency()
	);

	assertEquals(
        	"https://example.com/candidate",
        	response.comparisons().get(0).url()
	);

	assertEquals(
        	null,
        	response.comparisons().get(0).price()
	);
	
    }
@Test
void shouldReturnExactMatchesBeforeEquivalentMatches() {
    ProductRequest.Specifications specs =
            new ProductRequest.Specifications(
                    25.0, "French door", "Stainless", true
            );

    ProductRequest source = new ProductRequest(
            "Retailer A", "https://example.com/source",
            "Acme", "REF-100", "refrigerator",
            null, "USD", specs
    );

    ProductRequest equivalent = new ProductRequest(
            "Retailer B", "https://example.com/equivalent",
            "Acme", "REF-200", "refrigerator",
            null, "USD", specs
    );

    ProductRequest exact = new ProductRequest(
            "Retailer C", "https://example.com/exact",
            "Acme", "REF-100", "refrigerator",
            null, "USD", specs
    );

    CandidateProductService candidateService =
            ignored -> List.of(equivalent, exact);

    CompareController controller = new CompareController(
            new MatchingService(),
            candidateService
    );

    CompareResponse response =
            controller.compare(new CompareRequest(source));

    assertEquals(2, response.comparisons().size());

    assertEquals(
            "EXACT",
            response.comparisons().get(0).classification()
    );

    assertEquals(
            "EQUIVALENT",
            response.comparisons().get(1).classification()
    );
}

@Test
void shouldHandleProductWithOnlyBrandAndModel() {
    ProductRequest source = new ProductRequest(
            null, null, "Samsung", "RF28R7201SR",
            null, null, null, null
    );

    ProductRequest candidate = new ProductRequest(
            "Best Buy", "https://example.com/candidate",
            "Samsung", "RF28R7201SR",
            "refrigerator", null, "USD", null
    );

    CandidateProductService candidateService =
            ignored -> List.of(candidate);

    CompareController controller = new CompareController(
            new MatchingService(),
            candidateService
    );

    CompareResponse response =
            controller.compare(new CompareRequest(source));

    assertEquals("RF28R7201SR", response.sourceModel());
    assertEquals(1, response.comparisons().size());

    assertEquals(
            "EXACT",
            response.comparisons().get(0).classification()
    );
}

}

