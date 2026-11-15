
package edu.wmich.cs6030.smartcart;

import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
public class CompareController {

    @PostMapping("/api/v1/compare")
    public CompareResponse compare(@RequestBody CompareRequest request) {
        return new CompareResponse(
                request.product().model(),
                List.of()
        );
    }
}

