
package edu.wmich.cs6030.smartcart;

import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

import java.util.ArrayList;
import java.util.List;

@RestController
public class CompareController {
	private final MatchingService matchingService;
	private final CandidateProductService candidateProductService;

	public CompareController(
        	MatchingService matchingService,
        	CandidateProductService candidateProductService) {

    	this.matchingService = matchingService;
    	this.candidateProductService = candidateProductService;
}
    @PostMapping("/api/v1/compare")
    public CompareResponse compare(@RequestBody CompareRequest request) {
	ProductMatcher.Product source = matchingService.toMatcherProduct(request.product());
	List<ProductRequest> candidates = candidateProductService.findCandidates(request.product());
	List<CompareResponse.Comparison> comparisons = new ArrayList<>();
	for (ProductRequest candidate : candidates) {
    		ProductMatcher.Product candidateProduct =
            		matchingService.toMatcherProduct(candidate);

    		ProductMatcher.Result result =
            		matchingService.compare(source, candidateProduct);

		comparisons.add(new CompareResponse.Comparison(
        		candidate.model(),
        		candidate.retailer(),
        		result.label().name(),
        		List.of(result.explanation()),
        		java.util.Map.of(),
        		candidate.price(),
        		candidate.currency(),
        		candidate.url()
		));
}

        comparisons.sort(
                java.util.Comparator.comparingInt(
                        comparison -> switch (comparison.classification()) {
                            case "EXACT" -> 0;
                            case "EQUIVALENT" -> 1;
                            case "NEAR_EQUIVALENT" -> 2;
                            case "INSUFFICIENT_EVIDENCE" -> 3;
                            case "DIFFERENT" -> 4;
                            default -> 5;
                        }
                )
        );

        return new CompareResponse(
                request.product().model(),
                comparisons
        );
    }
}

