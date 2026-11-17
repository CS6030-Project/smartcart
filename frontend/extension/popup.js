document.addEventListener("DOMContentLoaded", () => {
    const button = document.getElementById("myButton");

    if (button) {
        button.addEventListener("click", control_function);
    } else {
        console.error('Button with id "myButton" was not found.');
    }
});


// MAIN FUNCTION
async function control_function() {
    try {
        const [tabUrl, tabId] = await getUrlId();

        if (!tabUrl || !tabId) {
            urlDisplayChange(null);
            console.error("No valid active tab.");
            return;
        }

        urlDisplayChange(tabUrl);

        const name = getNameFromUrl(tabUrl);

        let brand = null;
        let model = null;

        switch (name) {
            case "walmart":
                [brand, model] = await getWalmartProduct(tabId);

                brandDisplayChange(brand);
                modelDisplayChange(model);
		const json = await getJson(brand, model);
		if (json) {
    			json.forEach(offer => {
        			console.error(`${offer.retailer}: ${offer.price} (discount: ${offer.discount}, used: ${offer.used})`);
    			});
		} else {
		    console.error("No offers returned from API.");
		}
		break;

            default:
                console.error("Web page isn't supported:", tabUrl);
                brandDisplayChange(null);
                modelDisplayChange(null);
                break;
        }

    } catch (error) {
        console.error("Control function error:", error);
        brandDisplayChange(null);
        modelDisplayChange(null);
    }
}

// GET JSON FROM REST API
async function getJson(brand, model) {
    if (!brand || !model) {
        console.error("getJson: missing brand or model", { brand, model });
        return null;
    }

    try {
        const safeBrand = encodeURIComponent(brand.trim().toLowerCase());
        const safeModel = encodeURIComponent(model.trim().toUpperCase());

        const url = `http://127.0.0.1:5000/${safeBrand}/${safeModel}`;
        console.error("Fetching:", url);

        const response = await fetch(url, {
            method: "GET",
            headers: { "Accept": "application/json" }
        });

        console.error("STATUS:", response.status);

        if (!response.ok) {
            console.error(`API returned ${response.status} for ${url}`);
            return null;
        }

        const data = await response.json();
        console.error("PARSED JSON:", data);
        return data;

    } catch (error) {
        console.error("Failed to fetch JSON:", error);
        return null;
    }
}

// GET ACTIVE TAB URL AND ID
async function getUrlId() {
    const tabs = await chrome.tabs.query({
        active: true,
        currentWindow: true
    });

    if (tabs && tabs.length > 0 && tabs[0].id) {
        return [tabs[0].url, tabs[0].id];
    }

    return [null, null];
}


// DISPLAY URL
function urlDisplayChange(url) {
    const element = document.getElementById("scanned-url");

    if (element) {
        element.textContent = url || "No valid active tab";
    }
}


// DISPLAY BRAND
function brandDisplayChange(brand) {
    // Support both the original misspelled ID and the corrected ID.
    const element =
        document.getElementById("scanned-brand");

    if (element) {
        element.textContent = brand || "No product found";
    } else {
        console.error("Brand display element was not found.");
    }
}


// DISPLAY MODEL
function modelDisplayChange(model) {
    const element = document.getElementById("scanned-model");

    if (element) {
        element.textContent = model || "No model found";
    }
}


// IDENTIFY WEBSITE
function getNameFromUrl(url) {
    try {
        const hostname = new URL(url).hostname.toLowerCase();

        if (
            hostname === "walmart.com" ||
            hostname.endsWith(".walmart.com")
        ) {
            return "walmart";
        }

        return null;

    } catch (error) {
        console.error("Invalid URL:", error);
        return null;
    }
}


// WALMART PRODUCT EXTRACTION
async function getWalmartProduct(tabId) {
    try {
        const injections = await chrome.scripting.executeScript({
            target: {
                tabId: tabId
            },

            func: async () => {

                // Wait for an element to appear on the LIVE page.
                function waitForElement(selector, timeout = 15000) {
                    return new Promise((resolve, reject) => {
                        const start = Date.now();

                        const interval = setInterval(() => {
                            const element =
                                document.querySelector(selector);

                            if (element) {
                                clearInterval(interval);
                                resolve(element);
                                return;
                            }

                            if (Date.now() - start >= timeout) {
                                clearInterval(interval);
                                reject(
                                    new Error(
                                        "Timed out waiting for: " + selector
                                    )
                                );
                            }
                        }, 200);
                    });
                }


                // Normalize values extracted from Walmart.
                function cleanValue(value) {
                    if (value === null || value === undefined) {
                        return null;
                    }

                    if (typeof value === "object") {
                        if (value.name) {
                            return cleanValue(value.name);
                        }

                        if (value.value) {
                            return cleanValue(value.value);
                        }

                        return null;
                    }

                    const result = String(value)
                        .replace(/\s+/g, " ")
                        .trim();

                    return result || null;
                }


                // Extract a value from a specification label/value pair.
                function normalizeLabel(value) {
                    return String(value || "")
                        .replace(/[:\s]+/g, " ")
                        .trim()
                        .toLowerCase();
                }


                function extractFromRows() {
                    let brand = null;
                    let model = null;

                    // Standard HTML tables and Walmart role-based rows.
                    const rows = document.querySelectorAll(
                        "tr, [role='row']"
                    );

                    for (const row of rows) {
                        const cells = Array.from(
                            row.querySelectorAll(
                                "th, td, [role='cell'], [role='gridcell']"
                            )
                        );

                        if (cells.length >= 2) {
                            const label = normalizeLabel(
                                cells[0].innerText
                            );

                            const value = cleanValue(
                                cells.slice(1)
                                    .map(cell => cell.innerText)
                                    .join(" ")
                            );

                            if (label === "brand" && value) {
                                brand = value;
                            }

                            if (
                                (label === "model" ||
                                 label === "model number") &&
                                value
                            ) {
                                model = value;
                            }
                        }
                    }


                    // Definition lists: <dt>Brand</dt><dd>...</dd>
                    const terms = document.querySelectorAll("dt");

                    for (const term of terms) {
                        const label = normalizeLabel(term.innerText);
                        const value = cleanValue(
                            term.nextElementSibling?.innerText
                        );

                        if (label === "brand" && value) {
                            brand = value;
                        }

                        if (
                            (label === "model" ||
                             label === "model number") &&
                            value
                        ) {
                            model = value;
                        }
                    }


                    // Look for visible label/value pairs.
                    const labelElements = document.querySelectorAll(
                        "span, div, p, dt, strong"
                    );

                    for (const element of labelElements) {
                        const label = normalizeLabel(
                            element.innerText
                        );

                        if (
                            label !== "brand" &&
                            label !== "model" &&
                            label !== "model number"
                        ) {
                            continue;
                        }

                        const valueElement =
                            element.nextElementSibling;

                        const value = cleanValue(
                            valueElement?.innerText
                        );

                        if (label === "brand" && value && !brand) {
                            brand = value;
                        }

                        if (
                            (label === "model" ||
                             label === "model number") &&
                            value &&
                            !model
                        ) {
                            model = value;
                        }
                    }

                    return { brand, model };
                }


                // Search Walmart's embedded product data.
                function extractFromNextData() {
                    const script = document.getElementById(
                        "__NEXT_DATA__"
                    );

                    if (!script) {
                        return {
                            brand: null,
                            model: null,
                            found: false
                        };
                    }

                    try {
                        const json = JSON.parse(script.textContent);

                        const data =
                            json?.props?.pageProps?.initialData?.data;

                        const product = data?.product || {};

                        let brand = cleanValue(product.brand);
                        let model = cleanValue(product.model);

                        // Search specification arrays and nested objects.
                        function searchSpecifications(obj, depth = 0) {
                            if (
                                !obj ||
                                typeof obj !== "object" ||
                                depth > 15
                            ) {
                                return;
                            }

                            if (Array.isArray(obj)) {
                                for (const item of obj) {
                                    searchSpecifications(
                                        item,
                                        depth + 1
                                    );
                                }
                                return;
                            }

                            const label =
                                obj.name ??
                                obj.label ??
                                obj.key ??
                                obj.attributeName;

                            const value =
                                obj.value ??
                                obj.values ??
                                obj.attributeValue;

                            const normalized = normalizeLabel(label);

                            if (normalized === "brand" && !brand) {
                                brand = cleanValue(value);
                            }

                            if (
                                (normalized === "model" ||
                                 normalized === "model number") &&
                                !model
                            ) {
                                model = cleanValue(value);
                            }

                            for (const key of Object.keys(obj)) {
                                searchSpecifications(
                                    obj[key],
                                    depth + 1
                                );
                            }
                        }

                        searchSpecifications(data);

                        return {
                            brand,
                            model,
                            found: true
                        };

                    } catch (error) {
                        console.error(
                            "Could not parse Walmart product JSON:",
                            error
                        );

                        return {
                            brand: null,
                            model: null,
                            found: false
                        };
                    }
                }


                // Extract values from visible page text as a fallback.
                function extractFromPageText() {
                    const text = (
                        document.body.innerText || ""
                    ).replace(/\r/g, "");

                    const lines = text
                        .split("\n")
                        .map(line => line.trim())
                        .filter(Boolean);

                    let brand = null;
                    let model = null;

                    for (let i = 0; i < lines.length; i++) {
                        const line = lines[i];

                        const brandMatch = line.match(
                            /^Brand\s*:?\s*(.*)$/i
                        );

                        const modelMatch = line.match(
                            /^Model(?:\s+Number)?\s*:?\s*(.*)$/i
                        );

                        if (brandMatch) {
                            brand =
                                cleanValue(brandMatch[1]) ||
                                cleanValue(lines[i + 1]);
                        }

                        if (modelMatch) {
                            model =
                                cleanValue(modelMatch[1]) ||
                                cleanValue(lines[i + 1]);
                        }
                    }

                    return { brand, model };
                }


                try {
                    // STEP 1: Wait for the first chevron.
                    const chevron = await waitForElement(
                        "i.ld.ld-ChevronDown.pa0"
                    );

                    // STEP 2: Click the first button.
                    const firstTrigger =
                        chevron.closest(
                            "button, [role='button'], a"
                        ) || chevron;

                    firstTrigger.click();

                    console.log(
                        "Walmart: first specifications button clicked."
                    );


                    // STEP 3: Wait for the second button.
                    const secondButton = await waitForElement(
                        ".ld_CJ.ld_CP.pl0.underline.ph3"
                    );

                    // STEP 4: Click the second button.
                    secondButton.click();

                    console.log(
                        "Walmart: second specifications button clicked."
                    );


                    // STEP 5: Wait for the information to load.
                    let result = {
                        brand: null,
                        model: null
                    };

                    const start = Date.now();
                    const timeout = 15000;

                    while (Date.now() - start < timeout) {

                        // First try embedded product data.
                        const embedded = extractFromNextData();

                        // Then try the visible specification rows.
                        const rows = extractFromRows();

                        // Finally try visible page text.
                        const pageText = extractFromPageText();

                        result.brand =
                            rows.brand ||
                            embedded.brand ||
                            pageText.brand ||
                            result.brand;

                        result.model =
                            rows.model ||
                            embedded.model ||
                            pageText.model ||
                            result.model;

                        if (result.brand && result.model) {
                            break;
                        }

                        await new Promise(resolve =>
                            setTimeout(resolve, 500)
                        );
                    }


                    console.log(
                        "Walmart final extraction:",
                        result
                    );

                    return {
                        ok: true,
                        brand: result.brand,
                        model: result.model,
                        pageTitle: document.title,
                        url: location.href
                    };

                } catch (error) {
                    return {
                        ok: false,
                        error: error.message,
                        pageTitle: document.title,
                        url: location.href
                    };
                }
            }
        });


        // Read the result returned by the active tab.
        const result = injections?.[0]?.result;

        console.log("Walmart injection result:", result);

        if (!result || !result.ok) {
            console.error(
                "Walmart extraction failed:",
                result
            );

            return [null, null];
        }

        console.log("Brand:", result.brand);
        console.log("Model:", result.model);

        return [
            result.brand || null,
            result.model || null
        ];

    } catch (error) {
        console.error("Walmart extraction error:", error);
        return [null, null];
    }
}

