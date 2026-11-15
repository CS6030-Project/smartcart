package edu.wmich.cs6030.smartcart;

/** A deliberately small matching baseline, not a production classifier. */
public final class ProductMatcher {
    public enum Label { EXACT, EQUIVALENT, NEAR_EQUIVALENT, DIFFERENT, INSUFFICIENT_EVIDENCE }
    public record Product(String category, String brand, String model, String configuration,
                          String finish, Double capacityCubicFeet, Boolean iceMaker) { }
    public record Result(Label label, String explanation) { }

    private static String norm(String s) {
        return s == null ? "" : s.trim().replaceAll("\\s+", " ").toLowerCase();
    }
    private static boolean same(String a, String b) { return norm(a).equals(norm(b)); }
    private static boolean has(String s) { return s != null && !s.trim().isEmpty(); }

    public static Result compare(Product a, Product b) {
        if (!has(a.category()) || !has(b.category()))
            return new Result(Label.INSUFFICIENT_EVIDENCE, "Missing product category");
        if (!same(a.category(), b.category()))
            return new Result(Label.DIFFERENT, "Different product categories");
        if (!has(a.brand()) || !has(b.brand()))
            return new Result(Label.INSUFFICIENT_EVIDENCE, "Missing manufacturer");
        if (has(a.configuration()) && has(b.configuration()) && !same(a.configuration(), b.configuration()))
            return new Result(Label.DIFFERENT, "Different product configurations");
        boolean modelMatch = has(a.model()) && has(b.model()) && same(a.model(), b.model());
        boolean brandMatch = same(a.brand(), b.brand());
        boolean capacityComparable = a.capacityCubicFeet() != null && b.capacityCubicFeet() != null;
        boolean capacityClose = capacityComparable && Math.abs(a.capacityCubicFeet()-b.capacityCubicFeet()) <= 0.3;
        boolean capacitySame = capacityComparable
        && Double.compare(a.capacityCubicFeet(), b.capacityCubicFeet()) == 0;


	 boolean finishComparable = has(a.finish()) && has(b.finish());
        boolean finishSame = finishComparable && same(a.finish(), b.finish());
        boolean iceComparable = a.iceMaker() != null && b.iceMaker() != null;
        boolean iceSame = iceComparable && a.iceMaker().equals(b.iceMaker());
        if (modelMatch && brandMatch && capacitySame && finishSame
        		&& iceComparable && iceSame
        		&& has(a.configuration()) && has(b.configuration()))
    		return new Result(Label.EXACT, "Same model and observed variant attributes agree");
        if (!capacityComparable || !has(a.configuration()) || !has(b.configuration()) || !iceComparable || !finishComparable)
            return new Result(Label.INSUFFICIENT_EVIDENCE, "Missing required comparison attributes");
        if (brandMatch && capacitySame && finishSame && iceSame)
            return new Result(Label.EQUIVALENT, "Different identity; key observed features are aligned");
        if (brandMatch && capacityClose)
            return new Result(Label.NEAR_EQUIVALENT, "Same category and similar capacity, but features differ");
        return new Result(Label.DIFFERENT, "Material differences in observed attributes");
    }
    private ProductMatcher() { }
}
