package edu.wmich.cs6030.smartcart;

import org.springframework.stereotype.Service;
import java.util.List;

@Service
public class DefaultCandidateProductService implements CandidateProductService {

    @Override
    public List<ProductRequest> findCandidates(ProductRequest source) {
        return List.of();
    }
}
