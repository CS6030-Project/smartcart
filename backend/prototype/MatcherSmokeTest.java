package smartcart.prototype;

import static smartcart.prototype.ProductMatcher.*;

/** Run from scripts/check.sh; synthetic examples for early rule tests. */
public final class MatcherSmokeTest {
    private static Product item(String category, String brand, String model, String configuration,
                                String finish, Double capacity, Boolean ice) {
        return new Product(category,brand,model,configuration,finish,capacity,ice);
    }
    private static void check(Label expected, Result found) {
        if (found.label() != expected) throw new AssertionError("Expected "+expected+" but got "+found);
        System.out.println("PASS " + expected + " :: " + found.explanation());
    }
    public static void main(String[] args) {
        Product a=item("refrigerator","Acme","REF-100","French door","Stainless",25.0,true);
        check(Label.EXACT,compare(a,item("refrigerator","Acme","REF-100","French door","Stainless",25.0,true)));
        check(Label.EQUIVALENT,compare(a,item("refrigerator","Acme","REF-101","French door","Stainless",25.1,true)));
        check(Label.NEAR_EQUIVALENT,compare(a,item("refrigerator","Acme","REF-102","French door","Black",25.1,true)));
        check(Label.DIFFERENT,compare(a,item("television","Acme","TV-5","LED","Black",25.0,true)));
        check(Label.INSUFFICIENT_EVIDENCE,compare(a,item("refrigerator","Acme","","French door",null,null,null)));
        System.out.println("All five starter matching checks passed.");
    }
}
