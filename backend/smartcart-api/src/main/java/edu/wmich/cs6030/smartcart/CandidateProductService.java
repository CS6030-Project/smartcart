package edu.wmich.cs6030.smartcart;

import java.util.List;

public interface CandidateProductService {

    List<ProductRequest> findCandidates(ProductRequest source);
}
