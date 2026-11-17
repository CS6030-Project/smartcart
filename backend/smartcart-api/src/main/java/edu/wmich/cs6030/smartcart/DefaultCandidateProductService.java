package edu.wmich.cs6030.smartcart;

import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Service;
import java.util.List;

@Service
@Profile("local")
public class DefaultCandidateProductService implements CandidateProductService {

    @Override
    public List<ProductRequest> findCandidates(ProductRequest source) {
        return List.of();
    }
}
