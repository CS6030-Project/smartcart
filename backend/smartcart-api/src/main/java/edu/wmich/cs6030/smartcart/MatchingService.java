
package edu.wmich.cs6030.smartcart;

import org.springframework.stereotype.Service;

@Service
public class MatchingService {

    public ProductMatcher.Result compare(
            ProductMatcher.Product source,
            ProductMatcher.Product candidate) {

        return ProductMatcher.compare(source, candidate);
    }

    public ProductMatcher.Product toMatcherProduct(ProductRequest request) {

        ProductRequest.Specifications specs = request.specifications();

        return new ProductMatcher.Product(
                request.category(),
                request.brand(),
                request.model(),
                specs == null ? null : specs.configuration(),
                specs == null ? null : specs.finish(),
                specs == null ? null : specs.capacityCubicFeet(),
                specs == null ? null : specs.iceMaker()
        );
    }
}


