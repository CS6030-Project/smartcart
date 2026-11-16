package edu.wmich.cs6030.smartcart;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;

class ProductMatcherTest {

    @Test
    void identicalProductsShouldBeExact() {

        ProductMatcher.Product source = new ProductMatcher.Product(
                "refrigerator",
                "Acme",
                "REF-100",
                "French door",
                "Stainless",
                25.0,
                true
        );

        ProductMatcher.Product candidate = new ProductMatcher.Product(
                "refrigerator",
                "Acme",
                "REF-100",
                "French door",
                "Stainless",
                25.0,
                true
        );

        ProductMatcher.Result result =
                ProductMatcher.compare(source, candidate);

        assertEquals(ProductMatcher.Label.EXACT, result.label());
    }
    @Test
    void differentModelsWithMatchingSpecificationsShouldBeEquivalent() {

        ProductMatcher.Product source = new ProductMatcher.Product(
                "refrigerator",
                "Acme",
                "REF-100",
                "French door",
                "Stainless",
                25.0,
                true
        );

        ProductMatcher.Product candidate = new ProductMatcher.Product(
                "refrigerator",
                "Acme",
                "REF-101",
                "French door",
                "Stainless",
                25.0,
                true
        );

        ProductMatcher.Result result =
                ProductMatcher.compare(source, candidate);

        assertEquals(ProductMatcher.Label.EQUIVALENT, result.label());
    }
    @Test
    void similarProductsWithDifferentFinishesShouldBeNearEquivalent() {

        ProductMatcher.Product source = new ProductMatcher.Product(
                "refrigerator",
                "Acme",
                "REF-100",
                "French door",
                "Stainless",
                25.0,
                true
        );

        ProductMatcher.Product candidate = new ProductMatcher.Product(
                "refrigerator",
                "Acme",
                "REF-102",
                "French door",
                "Black",
                25.1,
                true
        );

        ProductMatcher.Result result =
                ProductMatcher.compare(source, candidate);

        assertEquals(ProductMatcher.Label.NEAR_EQUIVALENT, result.label());
    }
    @Test
    void differentConfigurationsShouldBeDifferent() {

        ProductMatcher.Product source = new ProductMatcher.Product(
                "refrigerator",
                "Acme",
                "REF-100",
                "French door",
                "Stainless",
                25.0,
                true
        );

        ProductMatcher.Product candidate = new ProductMatcher.Product(
                "refrigerator",
                "Acme",
                "REF-103",
                "Side by side",
                "Stainless",
                25.0,
                true
        );

        ProductMatcher.Result result =
                ProductMatcher.compare(source, candidate);

        assertEquals(ProductMatcher.Label.DIFFERENT, result.label());
    }
    @Test
    void missingCapacityShouldReturnInsufficientEvidence() {

        ProductMatcher.Product source = new ProductMatcher.Product(
                "refrigerator",
                "Acme",
                "REF-100",
                "French door",
                "Stainless",
                25.0,
                true
        );

        ProductMatcher.Product candidate = new ProductMatcher.Product(
                "refrigerator",
                "Acme",
                "REF-104",
                "French door",
                "Stainless",
                null,
                true
        );

        ProductMatcher.Result result =
                ProductMatcher.compare(source, candidate);

        assertEquals(
                ProductMatcher.Label.INSUFFICIENT_EVIDENCE,
                result.label()
        );
    }
    @Test
    void missingIceMakerShouldNotBeExact() {

        ProductMatcher.Product source = new ProductMatcher.Product(
                "refrigerator",
                "Acme",
                "REF-100",
                "French door",
                "Stainless",
                25.0,
                true
        );

        ProductMatcher.Product candidate = new ProductMatcher.Product(
                "refrigerator",
                "Acme",
                "REF-100",
                "French door",
                "Stainless",
                25.0,
                null
        );

        ProductMatcher.Result result =
                ProductMatcher.compare(source, candidate);

        assertEquals(
                ProductMatcher.Label.EXACT,
                result.label()
        );
    }
    @Test
    void missingConfigurationShouldReturnInsufficientEvidence() {

        ProductMatcher.Product source = new ProductMatcher.Product(
                "refrigerator",
                "Acme",
                "REF-100",
                "French door",
                "Stainless",
                25.0,
                true
        );

        ProductMatcher.Product candidate = new ProductMatcher.Product(
                "refrigerator",
                "Acme",
                "REF-100",
                null,
                "Stainless",
                25.0,
                true
        );

        ProductMatcher.Result result =
                ProductMatcher.compare(source, candidate);

        assertEquals(
                ProductMatcher.Label.EXACT,
                result.label()
        );
    }
    @Test
    void sameModelWithDifferentCapacitiesShouldNotBeExact() {

        ProductMatcher.Product source = new ProductMatcher.Product(
                "refrigerator",
                "Acme",
                "REF-100",
                "French door",
                "Stainless",
                25.0,
                true
        );

        ProductMatcher.Product candidate = new ProductMatcher.Product(
                "refrigerator",
                "Acme",
                "REF-100",
                "French door",
                "Stainless",
                25.2,
                true
        );

        ProductMatcher.Result result =
                ProductMatcher.compare(source, candidate);

        assertEquals(
                ProductMatcher.Label.NEAR_EQUIVALENT,
                result.label()
        );
    }
    @Test
    void differentManufacturersShouldNotBeEquivalent() {

        ProductMatcher.Product source = new ProductMatcher.Product(
                "refrigerator",
                "Acme",
                "REF-100",
                "French door",
                "Stainless",
                25.0,
                true
        );

        ProductMatcher.Product candidate = new ProductMatcher.Product(
                "refrigerator",
                "OtherBrand",
                "REF-100",
                "French door",
                "Stainless",
                25.0,
                true
        );

        ProductMatcher.Result result =
                ProductMatcher.compare(source, candidate);

        assertEquals(
                ProductMatcher.Label.DIFFERENT,
                result.label()
        );
    }

@Test
void sameBrandAndModelWithoutSpecificationsShouldBeExact() {
    ProductMatcher.Product source = new ProductMatcher.Product(
            null, "Samsung", "RF28R7201SR",
            null, null, null, null
    );

    ProductMatcher.Product candidate = new ProductMatcher.Product(
            null, "Samsung", "RF28R7201SR",
            null, null, null, null
    );

    ProductMatcher.Result result =
            ProductMatcher.compare(source, candidate);

    assertEquals(ProductMatcher.Label.EXACT, result.label());
}

@Test
void sameModelWithConflictingIceMakerShouldNotBeExact() {
    ProductMatcher.Product source = new ProductMatcher.Product(
            "refrigerator", "Samsung", "RF28R7201SR",
            "French door", "Stainless", 28.0, true
    );

    ProductMatcher.Product candidate = new ProductMatcher.Product(
            "refrigerator", "Samsung", "RF28R7201SR",
            "French door", "Stainless", 28.0, false
    );

    ProductMatcher.Result result =
            ProductMatcher.compare(source, candidate);

    assertEquals(ProductMatcher.Label.NEAR_EQUIVALENT, result.label());
}

}
