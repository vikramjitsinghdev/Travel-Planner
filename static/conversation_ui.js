/*
 * ============================================================
 * WANDERLUST — CONVERSATION-FIRST PLANNER UI
 * ============================================================
 *
 * This file is loaded AFTER static/script.js.
 *
 * It changes only the presentation of the Plan Trip workflow.
 *
 * Backend remains:
 *
 * user input
 *     ↓
 * app.py
 *     ↓
 * main.py
 *     ↓
 * MoodAgent
 *     ↓
 * TravelAgent
 *     ↓
 * ResearchAgent
 *     ↓
 * TravelAgent verification/enrichment
 *     ↓
 * main.py
 *     ↓
 * frontend
 *
 * The frontend experience becomes:
 *
 * USER REQUEST
 *     ↓
 * WANDERLUST THINKING
 *     ↓
 * THREE DESTINATION OPTIONS
 *     ↓
 * USER SELECTS ONE
 *     ↓
 * DESTINATION DETAILS
 *     ↓
 * CONFIRMATION
 *     ↓
 * DESTINATION LOCKED
 *
 * This file also fixes attraction objects rendering as:
 *
 *     [object Object]
 *
 * by normalizing attraction objects before rendering them.
 */


/* ============================================================
   CONVERSATION STATE
   ============================================================ */

(function () {

    "use strict";


    const conversationState = {

        thinkingRow: null,

        optionsRow: null,

        selectedRow: null,

        confirmationRow: null,

        confirmed: false

    };


    /* ========================================================
       BASIC HELPERS
       ======================================================== */

    function byId(id) {

        return document.getElementById(id);

    }


    function text(
        value,
        fallback = ""
    ) {

        if (
            value === null ||
            value === undefined
        ) {

            return fallback;

        }


        const result =
            String(value).trim();


        return result || fallback;

    }


    function safeEscape(value) {

        if (
            typeof escapeHtml ===
            "function"
        ) {

            return escapeHtml(
                String(value ?? "")
            );

        }


        return String(value ?? "")

            .replaceAll(
                "&",
                "&amp;"
            )

            .replaceAll(
                "<",
                "&lt;"
            )

            .replaceAll(
                ">",
                "&gt;"
            )

            .replaceAll(
                '"',
                "&quot;"
            )

            .replaceAll(
                "'",
                "&#039;"
            );

    }


    /* ========================================================
       DESTINATION HELPERS
       ======================================================== */

    function destinationName(
        candidate
    ) {

        return text(

            candidate?.destination ??

            candidate?.name ??

            candidate?.city ??

            candidate?.title,

            "Unknown destination"

        );

    }


    function destinationCountry(
        candidate
    ) {

        return text(

            candidate?.country ??

            candidate?.destination_country ??

            candidate?.location?.country,

            ""

        );

    }


    function destinationDescription(
        candidate
    ) {

        return text(

            candidate?.basic_info ??

            candidate?.description ??

            candidate?.summary ??

            candidate?.basic_information ??

            candidate?.overview ??

            candidate?.reason,

            "No destination description was provided."

        );

    }


    /* ========================================================
       FIX [object Object]
       ========================================================

       ResearchAgent may return:

       {
           "name": "Lake Louise",
           "description": "..."
       }

       instead of:

       "Lake Louise"

       Rendering the object directly causes:

       [object Object]

       This converts both formats into readable strings.
    ======================================================== */

    function normalizeAttraction(
        item
    ) {

        if (
            item === null ||
            item === undefined
        ) {

            return null;

        }


        if (
            typeof item === "string" ||
            typeof item === "number"
        ) {

            const result =
                String(item).trim();


            return result || null;

        }


        if (
            typeof item === "object"
        ) {

            const name =
                text(

                    item.name ??

                    item.title ??

                    item.attraction ??

                    item.place ??

                    item.location,

                    ""

                );


            const description =
                text(

                    item.description ??

                    item.summary ??

                    item.reason,

                    ""

                );


            if (
                name &&
                description
            ) {

                return (
                    `${name} — ${description}`
                );

            }


            if (name) {

                return name;

            }


            if (description) {

                return description;

            }


            return null;

        }


        return null;

    }


    function attractions(
        candidate
    ) {

        const source =

            candidate?.major_attractions ??

            candidate?.attractions ??

            candidate?.points_of_interest ??

            [];


        if (
            !Array.isArray(source)
        ) {

            return [];

        }


        return source

            .map(
                normalizeAttraction
            )

            .filter(Boolean)

            .slice(
                0,
                6
            );

    }


    function attractionImage(candidate, index) {
        const source =
            candidate?.major_attractions ??
            candidate?.attractions ??
            candidate?.points_of_interest ??
            [];

        const item = Array.isArray(source) ? source[index] : null;

        // Research agents may return attraction images in several common shapes.
        // Normalize them here so the card renderer receives a usable URL string.
        const candidates = [];

        const addImageValue = value => {
            if (typeof value === "string" && value.trim()) {
                candidates.push(value.trim());
                return;
            }
            if (value && typeof value === "object" && !Array.isArray(value)) {
                const nested =
                    value.url ?? value.image_url ?? value.imageUrl ??
                    value.src ?? value.original ?? value.large ?? value.medium;
                if (typeof nested === "string" && nested.trim()) candidates.push(nested.trim());
            }
        };

        if (item && typeof item === "object") {
            [
                item.image_url, item.imageUrl, item.photo_url, item.photoUrl,
                item.thumbnail_url, item.thumbnailUrl, item.image, item.photo,
                item.thumbnail, item.picture, item.cover_image, item.coverImage
            ].forEach(addImageValue);

            [
                ...(Array.isArray(item.photos) ? item.photos : []),
                ...(Array.isArray(item.images) ? item.images : []),
                ...(Array.isArray(item.image_urls) ? item.image_urls : [])
            ].forEach(addImageValue);
        }

        const sharedImages =
            candidate?.attraction_images ??
            candidate?.attractionImages ??
            candidate?.major_attraction_images ??
            candidate?.majorAttractionImages;

        if (Array.isArray(sharedImages)) addImageValue(sharedImages[index]);

        return candidates.find(url => /^https?:\/\//i.test(url)) || candidates[0] || "";
    }

    function attractionImageFallbacks(candidate, index) {
        const source = candidate?.major_attractions ?? candidate?.attractions ?? candidate?.points_of_interest ?? [];
        const item = Array.isArray(source) ? source[index] : null;
        const values = [];
        const add = value => {
            if (typeof value === "string" && /^https?:\/\//i.test(value.trim())) values.push(value.trim());
            else if (value && typeof value === "object") {
                const url = value.url ?? value.image_url ?? value.imageUrl ?? value.src ?? value.original ?? value.large;
                if (typeof url === "string" && /^https?:\/\//i.test(url.trim())) values.push(url.trim());
            }
        };
        if (item && typeof item === "object") {
            [item.image_url, item.imageUrl, item.photo_url, item.thumbnail_url, item.image, item.photo, item.thumbnail].forEach(add);
            [...(Array.isArray(item.photos) ? item.photos : []),
             ...(Array.isArray(item.images) ? item.images : []),
             ...(Array.isArray(item.image_urls) ? item.image_urls : [])].forEach(add);
        }
        const shared = candidate?.attraction_images ?? candidate?.attractionImages ?? candidate?.major_attraction_images ?? candidate?.majorAttractionImages;
        if (Array.isArray(shared)) add(shared[index]);
        const primary = attractionImage(candidate, index);
        return [...new Set(values)].filter(url => url !== primary);
    }



    /* ========================================================
       IMAGE HELPERS
       ======================================================== */

    function images(
        candidate
    ) {

        const output = [];

        const seen =
            new Set();


        function add(
            value
        ) {

            if (
                typeof value !==
                "string"
            ) {

                return;

            }


            const url =
                value.trim();


            if (
                !url ||
                seen.has(url)
            ) {

                return;

            }


            seen.add(url);

            output.push(url);

        }


        const fields = [
            candidate?.images,
            candidate?.image_urls,
            candidate?.photos,
            candidate?.gallery,
            candidate?.research?.images,
            candidate?.research_result?.images
        ];


        fields.forEach(
            field => {

                if (typeof field === "string") {
                    add(field);
                    return;
                }

                if (!Array.isArray(field)) return;

                field.forEach(
                    item => {

                        if (
                            typeof item ===
                            "string"
                        ) {

                            add(item);

                            return;

                        }


                        if (
                            item &&
                            typeof item ===
                            "object"
                        ) {

                            add(

                                item.image_url ??

                                item.url ??

                                item.src ??

                                item.image?.url ??

                                item.image?.image_url

                            );

                        }

                    }
                );

            }
        );


        [
            candidate?.image_url,
            candidate?.imageUrl,
            candidate?.image,
            candidate?.thumbnail_url,
            candidate?.thumbnail,
            candidate?.cover_image,
            candidate?.image?.url,
            candidate?.image?.image_url,
            candidate?.image?.src,
            candidate?.research?.image_url,
            candidate?.research_result?.image_url
        ].forEach(add);

        return output.slice(0, 8);

    }


    /* ========================================================
       COORDINATES
       ======================================================== */

    function coordinates(
        candidate
    ) {

        const value =

            candidate?.map_coordinates ??

            candidate?.coordinates ??

            candidate?.location?.coordinates ??

            candidate?.map?.coordinates;


        if (!value) {

            return null;

        }


        if (
            Array.isArray(value) &&
            value.length >= 2
        ) {

            const latitude =
                Number(value[0]);

            const longitude =
                Number(value[1]);


            if (
                Number.isFinite(
                    latitude
                ) &&
                Number.isFinite(
                    longitude
                )
            ) {

                return {

                    latitude,

                    longitude

                };

            }

        }


        if (
            typeof value ===
            "object"
        ) {

            const latitude =
                Number(

                    value.latitude ??

                    value.lat

                );


            const longitude =
                Number(

                    value.longitude ??

                    value.lng ??

                    value.lon

                );


            if (
                Number.isFinite(
                    latitude
                ) &&
                Number.isFinite(
                    longitude
                )
            ) {

                return {

                    latitude,

                    longitude

                };

            }

        }


        return null;

    }


    /* ========================================================
       COST
       ======================================================== */

    function estimatedCost(
        candidate
    ) {

        const possibleValues = [

            candidate?.cost_estimates?.total,

            candidate?.cost_estimates?.estimated_total,

            candidate?.research?.cost_estimates?.total,

            candidate?.research_result?.cost_estimates?.total,

            candidate?.estimated_cost,

            candidate?.research_estimate

        ];


        for (
            const value
            of possibleValues
        ) {

            if (
                typeof value ===
                "number" &&
                Number.isFinite(
                    value
                )
            ) {

                return value;

            }


            if (
                typeof value ===
                "string"
            ) {

                const numeric =
                    Number(

                        value.replace(
                            /[^0-9.\-]/g,
                            ""
                        )

                    );


                if (
                    Number.isFinite(
                        numeric
                    )
                ) {

                    return numeric;

                }

            }

        }


        return null;

    }


    function money(
        value
    ) {

        if (
            value === null ||
            value === undefined ||
            !Number.isFinite(
                Number(value)
            )
        ) {

            return "Not available";

        }


        return new Intl.NumberFormat(
            undefined,
            {

                style:
                    "currency",

                currency:
                    "CAD",

                maximumFractionDigits:
                    0

            }
        ).format(
            Number(value)
        );

    }



    /* ========================================================
       SMART BUDGET ESTIMATES
       ======================================================== */

    function costAmount(entry) {
        if (entry === null || entry === undefined) return null;
        const raw = (typeof entry === "object")
            ? (entry.amount ?? entry.value ?? entry.estimated_cost)
            : entry;
        if (raw === null || raw === undefined || raw === "") return null;
        const amount = (typeof raw === "number")
            ? raw
            : Number(String(raw).replace(/[^0-9.\-]/g, ""));
        return Number.isFinite(amount) && amount >= 0 ? amount : null;
    }

    function budgetEstimateData(candidate) {
        const costs = candidate?.cost_estimates
            ?? candidate?.research?.cost_estimates
            ?? candidate?.research_result?.cost_estimates
            ?? {};
        // Older research responses use these legacy fields. Preserve their values
        // for display, but don't multiply them unless their unit is known.
        const firstDefined = (...values) => values.find(value =>
            value !== undefined && value !== null && value !== ""
        );
        const normalizedCosts = {
            ...costs,
            travel_to_destination: firstDefined(
                costs.travel_to_destination, candidate?.traveling_cost,
                candidate?.travel_cost, candidate?.transportation_cost
            ),
            accommodation_per_night: firstDefined(
                costs.accommodation_per_night, candidate?.residence_cost,
                candidate?.accommodation_cost
            ),
            food_per_day: firstDefined(
                costs.food_per_day, candidate?.average_food_cost,
                candidate?.food_cost
            ),
            local_transport_per_day: firstDefined(
                costs.local_transport_per_day, candidate?.daily_average_travel_cost,
                candidate?.local_transport_cost
            )
        };
        const travelers = Math.max(1, Number(basicTripData?.travelers) || 1);
        const days = Math.max(1, Number(basicTripData?.duration_days) || 1);
        const nights = Math.max(0, Number(basicTripData?.duration_nights ?? basicTripData?.nights ?? (days - 1)));
        const budget = Number(basicTripData?.budget);
        const entries = [
            ["Travel to destination", costs.travel_to_destination, "travel"],
            ["Accommodation", costs.accommodation_per_night, "night"],
            ["Food", costs.food_per_day, "food"],
            ["Local transport", costs.local_transport_per_day, "local"]
        ].map(([label, entry, kind]) => {
            const amount = costAmount(entry);
            const basis = typeof entry === "object" ? text(entry.basis, "") : "";
            const currency = typeof entry === "object" ? text(entry.currency, "CAD").toUpperCase() : "CAD";
            const basisLower = basis.toLowerCase();
            let groupEstimate = null;
            if (amount !== null) {
                if (kind === "travel" && /per person|per traveler|per traveller|each person|round.?trip per person/.test(basisLower)) {
                    groupEstimate = amount * travelers;
                } else if (kind === "travel" && /total for group|whole group|group total|total trip/.test(basisLower)) {
                    groupEstimate = amount;
                } else if (kind === "night" && /per night|per room|nightly/.test(basisLower)) {
                    groupEstimate = amount * nights;
                } else if (kind === "night" && /per person per night|per traveller per night|per traveler per night/.test(basisLower)) {
                    groupEstimate = amount * travelers * nights;
                } else if ((kind === "food" || kind === "local") && /per person|per traveler|per traveller|per day per person|daily per person/.test(basisLower)) {
                    groupEstimate = amount * travelers * days;
                } else if ((kind === "food" || kind === "local") && /per day|daily/.test(basisLower)) {
                    groupEstimate = amount * days;
                } else if (/total for group|whole group|group total|total trip/.test(basisLower)) {
                    groupEstimate = amount;
                }
            }
            return { label, amount, basis, currency, groupEstimate };
        });
        const currencies = [...new Set(entries.filter(item => item.groupEstimate !== null).map(item => item.currency))];
        const currencyConsistent = currencies.length <= 1;
        const calculable = entries.filter(item => item.groupEstimate !== null);
        const knownSubtotal = calculable.length
            ? calculable.reduce((sum, item) => sum + item.groupEstimate, 0)
            : null;
        const complete = entries.every(item => item.groupEstimate !== null) && currencyConsistent;
        const explicitTotalEntry = costs.total ?? costs.estimated_total;
        const explicitTotal = costAmount(explicitTotalEntry);
        const explicitTotalBasis = typeof explicitTotalEntry === "object" ? text(explicitTotalEntry.basis, "").toLowerCase() : "";
        const explicitTotalIsTripWide = /full trip|whole trip|all categories|all expenses|group total|total for group/.test(explicitTotalBasis);
        const estimatedTotal = complete
            ? (explicitTotal !== null && explicitTotalIsTripWide ? explicitTotal : knownSubtotal)
            : knownSubtotal;
        const hasBudget = Number.isFinite(budget) && budget > 0;
        const difference = hasBudget && complete && estimatedTotal !== null ? budget - estimatedTotal : null;
        const knownDifference = hasBudget && !complete && knownSubtotal !== null ? budget - knownSubtotal : null;
        return {
            entries, calculable, knownSubtotal, estimatedTotal, complete, currencyConsistent,
            hasBudget, budget, travelers, days, nights, difference, knownDifference,
            perPerson: estimatedTotal !== null ? estimatedTotal / travelers : null,
            missing: entries.filter(item => item.groupEstimate === null)
        };
    }

    function renderBudgetEstimate(candidate) {
        const data = budgetEstimateData(candidate);
        const currency = text(basicTripData?.currency, "CAD").toUpperCase();
        const formatMoney = (amount, code = currency) => {
            if (amount === null || amount === undefined || !Number.isFinite(Number(amount))) return "Not available";
            try {
                return new Intl.NumberFormat(undefined, {
                    style: "currency", currency: /^[A-Z]{3}$/.test(code) ? code : "CAD",
                    maximumFractionDigits: 0
                }).format(Number(amount));
            } catch (_) {
                return `${Math.round(Number(amount))} ${currency}`;
            }
        };
        const rows = data.entries.map(item => {
            const amountLabel = item.amount === null
                ? "Price not available"
                : `${formatMoney(item.amount, item.currency)}${item.basis ? ` <small>· ${safeEscape(item.basis)}</small>` : ` <small>· unit not specified</small>`}${item.groupEstimate !== null ? `<small class="wl-budget-calculated">Estimated group cost: ${formatMoney(item.groupEstimate, item.currency)}</small>` : ""}`;
            return `<div class="wl-smart-budget-row"><span>${safeEscape(item.label)}</span><strong>${amountLabel}</strong></div>`;
        }).join("");
        let status = `<div class="wl-smart-budget-status neutral">Not enough usable pricing data to judge the full trip cost yet.</div>`;
        if (data.complete && data.estimatedTotal !== null && data.hasBudget) {
            if (data.difference >= 0) {
                status = `<div class="wl-smart-budget-status good"><strong>${formatMoney(data.difference)} under budget</strong><span>Estimated trip total: ${formatMoney(data.estimatedTotal)} · ${formatMoney(data.perPerson)} per person</span></div>`;
            } else {
                status = `<div class="wl-smart-budget-status over"><strong>${formatMoney(Math.abs(data.difference))} over budget</strong><span>Estimated trip total: ${formatMoney(data.estimatedTotal)} · ${formatMoney(data.perPerson)} per person</span></div>`;
            }
        } else if (data.knownSubtotal !== null) {
            const subtotalText = data.hasBudget && data.knownDifference !== null && data.knownDifference < 0
                ? `${formatMoney(Math.abs(data.knownDifference))} in known costs already exceeds your budget`
                : "Known-cost subtotal only — full trip affordability is not yet known";
            status = `<div class="wl-smart-budget-status neutral"><strong>${formatMoney(data.knownSubtotal)} known-cost subtotal</strong><span>${formatMoney(data.knownSubtotal / data.travelers)} per person · ${subtotalText}</span></div><p class="wl-smart-budget-note">Do not treat the unallocated difference as money remaining. Missing or unclear prices must be estimated before we can say the trip is under budget.</p>`;
        }
        if (!data.currencyConsistent) {
            status += `<p class="wl-smart-budget-note">The available prices use different currencies. Convert them to one currency before comparing the total with your budget.</p>`;
        }
        const missing = data.missing.map(item => item.label.toLowerCase());
        const tips = [];
        if (data.difference !== null && data.difference < 0) {
            tips.push("Compare accommodation options and flexible travel dates first; these often have the largest effect on total cost.");
            tips.push("Keep must-do attractions and reduce optional paid activities before removing experiences that matter to you.");
        } else if (data.complete && data.difference !== null && data.difference >= 0) {
            tips.push("Keep part of the remaining budget as a buffer for price changes, meals, and unexpected costs.");
        }
        if (missing.length) tips.push(`Add a usable price and clear unit for ${missing.join(", ")} before relying on a full-trip estimate.`);
        return `
            <section class="wl-smart-budget" aria-label="Smart trip budget">
                <div class="wl-smart-budget-heading"><div><span class="wl-eyebrow">SMART BUDGET</span><h3>Can this trip fit your budget?</h3></div><span class="wl-budget-pill">${safeEscape(currency)}</span></div>
                <div class="wl-smart-budget-summary">
                    <div><small>YOUR TOTAL BUDGET</small><strong>${data.hasBudget ? formatMoney(data.budget) : "Not set"}</strong></div>
                    <div><small>TRAVELLERS</small><strong>${data.travelers}</strong></div>
                    <div><small>DURATION</small><strong>${data.days} days · ${data.nights} nights</strong></div>
                </div>
                <div class="wl-smart-budget-rows">${rows || `<p class="wl-smart-budget-note">No itemized cost estimates were returned by research yet.</p>`}</div>
                ${status}
                ${tips.length ? `<div class="wl-smart-budget-tips"><strong>Smart recommendations</strong><ul>${tips.map(tip => `<li>${safeEscape(tip)}</li>`).join("")}</ul></div>` : ""}
                <p class="wl-smart-budget-disclaimer">Research estimates are indicative, not live quotes. Confirm prices with providers before booking.</p>
            </section>
        `;
    }

    /* ========================================================
       GET CANDIDATES
       ======================================================== */

    function getPlannerCandidates(
        trip
    ) {

        if (
            typeof getCandidates ===
            "function"
        ) {

            const result =
                getCandidates(
                    trip
                );


            if (
                Array.isArray(result)
            ) {

                return result.slice(
                    0,
                    3
                );

            }

        }


        const candidates =

            trip?.destinations ??

            trip?.candidates ??

            [];


        return Array.isArray(
            candidates
        )

            ? candidates.slice(
                0,
                3
            )

            : [];

    }


    /* ========================================================
       CHAT MESSAGE CREATION
       ======================================================== */

    function appendAssistantBubble(
        html,
        options = {}
    ) {

        const container =
            byId(
                "tripChatMessages"
            );


        if (!container) {

            return null;

        }


        const row =
            document.createElement(
                "div"
            );


        row.className =

            "trip-chat-row assistant" +

            (
                options.wide
                    ? " conversation-wide"
                    : ""
            );


        const wrapper =
            document.createElement(
                "div"
            );


        const bubble =
            document.createElement(
                "div"
            );


        const time =
            document.createElement(
                "div"
            );


        bubble.className =
            "trip-chat-bubble conversation-bubble";


        bubble.innerHTML = html;

        bubble.querySelectorAll("img[data-image-fallbacks]").forEach(image => {
            let fallbacks = [];
            try {
                fallbacks = JSON.parse(image.dataset.imageFallbacks || "[]");
            } catch (_) {
                fallbacks = [];
            }

            image.addEventListener("error", () => {
                const next = fallbacks.shift();
                if (next) {
                    image.src = next;
                    image.dataset.imageFallbacks = JSON.stringify(fallbacks);
                    return;
                }

                image.hidden = true;
                const placeholder = image.parentElement?.querySelector(".wl-image-placeholder");
                if (placeholder) placeholder.hidden = false;
            });
        });

        time.className =
            "trip-chat-time";


        time.textContent =

            new Date()
                .toLocaleTimeString(
                    [],
                    {

                        hour:
                            "2-digit",

                        minute:
                            "2-digit"

                    }
                );


        wrapper.appendChild(
            bubble
        );


        wrapper.appendChild(
            time
        );


        row.appendChild(
            wrapper
        );


        container.appendChild(
            row
        );


        container.scrollTop =
            container.scrollHeight;


        return row;

    }


    function appendUserBubble(
        message
    ) {

        if (
            typeof addUserChatMessage ===
            "function"
        ) {

            addUserChatMessage(
                message
            );

        }

    }


    function removeRow(
        row
    ) {

        if (
            row &&
            row.parentNode
        ) {

            row.parentNode.removeChild(
                row
            );

        }

    }


    /* ========================================================
       THINKING UI
       ======================================================== */

    const thinkingStages = [

        "Understanding your preferences",

        "Finding destinations that fit",

        "Researching the options",

        "Comparing the information"

    ];


    function thinkingMarkup(
        activeStage =
            thinkingStages[0]
    ) {

        return `

            <div
                class="wl-thinking"
            >

                <div
                    class="wl-thinking-title"
                >

                    <span
                        class="wl-thinking-dot"
                    ></span>

                    Wanderlust is thinking

                </div>


                <div
                    class="wl-thinking-stage"
                >
                    ${safeEscape(
                        activeStage
                    )}
                </div>


                <div
                    class="wl-thinking-progress"
                >

                    ${
                        thinkingStages
                            .map(
                                stage => `

                                    <span
                                        class="wl-thinking-step ${
                                            stage ===
                                            activeStage
                                                ? "active"
                                                : ""
                                        }"
                                    >

                                        ${safeEscape(
                                            stage
                                        )}

                                    </span>

                                `
                            )
                            .join("")
                    }

                </div>

            </div>

        `;

    }


    function addThinking() {

        removeRow(
            conversationState.thinkingRow
        );


        conversationState.thinkingRow =

            appendAssistantBubble(

                thinkingMarkup(),

                {
                    wide:
                        false
                }

            );

    }


    function setThinkingStage(
        stage
    ) {

        const row =
            conversationState.thinkingRow;


        if (!row) {

            return;

        }


        const stageNode =
            row.querySelector(
                ".wl-thinking-stage"
            );


        if (stageNode) {

            stageNode.textContent =
                stage;

        }


        row
            .querySelectorAll(
                ".wl-thinking-step"
            )
            .forEach(
                step => {

                    step.classList.toggle(

                        "active",

                        step.textContent
                            .trim() ===
                        stage

                    );

                }
            );


        const messages =
            byId(
                "tripChatMessages"
            );


        if (messages) {

            messages.scrollTop =
                messages.scrollHeight;

        }

    }


    /* ========================================================
       DESTINATION OPTION CARDS
       ======================================================== */

    function addOptionsMessage(candidates) {
        // Remove the previous destination options.
        removeRow(conversationState.optionsRow);

        // Generate the HTML for each destination card.
        const cards = candidates
            .map((candidate, index) => {
                const name = destinationName(candidate);
                const country = destinationCountry(candidate);
                const description = destinationDescription(candidate);

                // Retrieve the primary image and available fallbacks.
                const photoList = images(candidate);
                const photo = photoList[0] || "";

                // Normalize the destination name for comparison.
                const destinationKey = name
                    .toLowerCase()
                    .replace(/\s+/g, " ")
                    .trim();

                // Remove attraction labels that duplicate the destination name.
                const attractionList = attractions(candidate)
                    .filter((item) => {
                        const attractionKey = String(item)
                            .toLowerCase()
                            .replace(/\s+/g, " ")
                            .trim();

                        return (
                            attractionKey !== destinationKey &&
                            !destinationKey.startsWith(attractionKey) &&
                            !attractionKey.startsWith(destinationKey)
                        );
                    })
                    .slice(0, 3);

                // Preserve the existing image markup and fallback attributes.
                const imageMarkup = photo
                    ? `
                        <img
                            class="wl-option-image"
                            src="${safeEscape(photo)}"
                            alt="${safeEscape(name)}"
                            loading="lazy"
                            data-image-fallbacks="${safeEscape(
                                JSON.stringify(photoList.slice(1))
                            )}"
                        >
                    `
                    : "";

                const imagePlaceholder = `
                    <div
                        class="wl-image-placeholder"
                        ${photo ? "hidden" : ""}
                        aria-label="Destination image unavailable"
                    >
                        <span aria-hidden="true">✦</span>
                        <small>Destination preview</small>
                    </div>
                `;

                // Preserve the existing country element and its class.
                const countryMarkup = country
                    ? `
                        <div class="wl-option-country">
                            ${safeEscape(country)}
                        </div>
                    `
                    : "";

                // Limit the description to a reasonable preview length.
                const descriptionText = description.length > 190
                    ? `${description.slice(0, 187)}...`
                    : description;

                // Generate the attraction markup when attractions are available.
                const attractionsMarkup = attractionList.length
                    ? `
                        <div class="wl-option-attractions">
                            ${attractionList
                                .map(
                                    (item) => `
                                        <span>${safeEscape(item)}</span>
                                    `
                                )
                                .join("")}
                        </div>
                    `
                    : "";

                // Return the destination card.
                // The existing HTML structure and CSS class names are preserved.
                return `
                    <article
                        class="wl-option-card"
                        data-option-index="${index}"
                    >
                        <div class="wl-option-image-wrap">
                            ${imageMarkup}
                            ${imagePlaceholder}
                        </div>

                        <div class="wl-option-body">
                            <div class="wl-option-number">
                                ${index + 1}
                            </div>

                            <h3>
                                ${safeEscape(name)}
                            </h3>

                            ${countryMarkup}

                            <p>
                                ${safeEscape(descriptionText)}
                            </p>

                            ${attractionsMarkup}

                            <div class="wl-option-actions">
                                <button
                                    type="button"
                                    class="wl-secondary-button wl-details-button"
                                    data-index="${index}"
                                >
                                    VIEW DETAILS
                                </button>

                                <button
                                    type="button"
                                    class="wl-primary-button wl-select-button"
                                    data-index="${index}"
                                >
                                    SELECT
                                </button>
                            </div>
                        </div>
                    </article>
                `;
            })
            .join("");

        // Display the introduction and destination cards.
        conversationState.optionsRow = appendAssistantBubble(
            `
                <div class="wl-conversation-text">
                    <strong>
                        I've found ${candidates.length}
                        destination${candidates.length === 1 ? "" : "s"}
                        that fit your request.
                    </strong>

                    <span>
                        Take a look at the options below.
                        You can inspect one in more detail or
                        choose the one you'd like to build your trip around.
                    </span>
                </div>

                <div class="wl-options-grid">
                    ${cards}
                </div>
            `,
            {
                wide: true
            }
        );

        // Stop if the conversation bubble could not be created.
        const optionsRow = conversationState.optionsRow;

        if (!optionsRow) {
            return;
        }

        // Attach handlers to the Details buttons.
        optionsRow
            .querySelectorAll(".wl-details-button")
            .forEach((button) => {
                button.addEventListener("click", () => {
                    const index = Number(button.dataset.index);
                    const candidate = currentCandidates[index];

                    if (
                        candidate &&
                        typeof showDestination === "function"
                    ) {
                        showDestination(candidate);
                    }
                });
            });

        // Attach handlers to the Select buttons.
        optionsRow
            .querySelectorAll(".wl-select-button")
            .forEach((button) => {
                button.addEventListener("click", () => {
                    const index = Number(button.dataset.index);

                    selectTrip(index);
                });
            });

        // Scroll the conversation to the newest content.
        const messages = byId("tripChatMessages");

        if (messages) {
            messages.scrollTop = messages.scrollHeight;
        }
    }


    /* ========================================================
       SELECTED DESTINATION MESSAGE
       ======================================================== */

    function renderSelectedConversation(candidate) {
        removeRow(conversationState.selectedRow);
        removeRow(conversationState.confirmationRow);

        const name = destinationName(candidate);
        const country = destinationCountry(candidate);
        const description = destinationDescription(candidate);
        const photoList = images(candidate);
        const photo = photoList[0] || "";
        const attractionList = attractions(candidate).slice(0, 6);
        const coordinate = coordinates(candidate);
        const cost = estimatedCost(candidate);
        const travelers = basicTripData?.travelers ?? "—";
        const destinationType = text(candidate?.type ?? candidate?.category, "Destination");
        const attractionCards = attractionList.map((item, index) => {
            const attractionPhoto = attractionImage(candidate, index);
            return `
                <article class="wl-attraction-card">
                    <div class="wl-attraction-image-wrap">
                        ${attractionPhoto ? `<img class="wl-attraction-image" src="${safeEscape(attractionPhoto)}" alt="${safeEscape(item)}" loading="lazy" data-image-fallbacks="${safeEscape(JSON.stringify(attractionImageFallbacks(candidate, index)))}">` : ""}
                        <div class="wl-image-placeholder" ${attractionPhoto ? "hidden" : ""} aria-label="Attraction image unavailable"><span aria-hidden="true">✦</span><small>Explore this place</small></div>
                    </div>
                    <div class="wl-attraction-copy"><strong>${safeEscape(item)}</strong></div>
                </article>
            `;
        }).join("");

        conversationState.selectedRow = appendAssistantBubble(`
            <section class="wl-destination-detail" aria-label="Selected destination">
                <header class="wl-detail-header">
                    <div class="wl-brand-mark" aria-hidden="true">W</div>
                    <div class="wl-detail-brand"><strong>Wanderlust AI</strong><span>Confirm your destination</span></div>
                    <span class="wl-selected-status"><span aria-hidden="true">✓</span> Selected destination</span>
                </header>

                <div class="wl-destination-hero">
                    <div class="wl-destination-hero-media">
                        ${photo ? `<img class="wl-destination-hero-image" src="${safeEscape(photo)}" alt="${safeEscape(name)}" loading="lazy" data-image-fallbacks="${safeEscape(JSON.stringify(photoList.slice(1)))}">` : ""}
                        <div class="wl-image-placeholder" ${photo ? "hidden" : ""}><span aria-hidden="true">✦</span><small>Destination preview</small></div>
                    </div>
                    <div class="wl-destination-copy">
                        <span class="wl-eyebrow">${safeEscape(destinationType)}</span>
                        <h2>${safeEscape(name)}</h2>
                        ${country ? `<div class="wl-destination-location"><span aria-hidden="true">⌖</span>${safeEscape(country)}</div>` : ""}
                        <p>${safeEscape(description)}</p>
                    </div>
                </div>

                <div class="wl-destination-facts">
                    <div class="wl-fact-card"><span class="wl-fact-icon" aria-hidden="true">♧</span><div><small>TRAVELERS</small><strong>${safeEscape(travelers)}</strong></div></div>
                    <div class="wl-fact-card"><span class="wl-fact-icon" aria-hidden="true">＄</span><div><small>RESEARCH ESTIMATE</small><strong>${safeEscape(money(cost))}</strong></div></div>
                    <div class="wl-fact-card"><span class="wl-fact-icon" aria-hidden="true">⌖</span><div><small>MAP</small><strong>${coordinate ? "Available" : "Not available"}</strong></div></div>
                </div>

                ${renderBudgetEstimate(candidate)}

                ${attractionCards ? `
                    <section class="wl-attractions-section">
                        <div class="wl-section-heading"><div><span class="wl-section-icon" aria-hidden="true">✧</span><h3>Top attractions</h3></div><span class="wl-section-caption">Worth exploring</span></div>
                        <div class="wl-attractions-grid">${attractionCards}</div>
                    </section>
                ` : ""}

                <div class="wl-confirm-actions">
                    <button type="button" class="wl-secondary-button" id="wlChooseAnotherButton"><span aria-hidden="true">←</span> Choose another destination</button>
                    <button type="button" class="wl-primary-button" id="wlConfirmButton"><span aria-hidden="true">✓</span> Confirm ${safeEscape(name)}</button>
                </div>
            </section>
        `, { wide: true });

        conversationState.confirmationRow = null;

        byId("wlChooseAnotherButton")?.addEventListener("click", () => {
            removeRow(conversationState.selectedRow);
            removeRow(conversationState.confirmationRow);
            conversationState.selectedRow = null;
            conversationState.confirmationRow = null;
            addUserChatMessage("I'd like to compare the other options.");
            appendAssistantBubble(`
                <div class="wl-conversation-text">
                    <strong>Of course — let's compare again.</strong>
                    <span>Your three destination options are still available above. Select another destination when you're ready.</span>
                </div>
            `);
            const optionsRow = conversationState.optionsRow;
            optionsRow?.scrollIntoView({ behavior: "smooth", block: "start" });
        });

        byId("wlConfirmButton")?.addEventListener("click", () => {
            window.confirmTrip?.();
        });
    }

    /* ========================================================
       DESTINATION SELECTION
       ======================================================== */

    window.selectTrip =

        function
        selectTripConversation(
            index
        ) {

            const candidate =

                currentCandidates[
                    index
                ];


            if (!candidate) {

                return;

            }


            selectedCandidate =
                candidate;


            /*
             * Highlight the selected destination card.
             */

            conversationState.optionsRow

                ?.querySelectorAll(
                    ".wl-option-card"
                )

                .forEach(
                    (
                        card,
                        cardIndex
                    ) => {

                        card.classList.toggle(

                            "selected",

                            cardIndex ===
                            index

                        );

                    }
                );


            addUserChatMessage(

                `I'd like to go with ${
                    destinationName(
                        candidate
                    )
                }${
                    destinationCountry(
                        candidate
                    )
                        ? `, ${
                            destinationCountry(
                                candidate
                            )
                        }`
                        : ""
                }.`

            );


            renderSelectedConversation(
                candidate
            );


            const selectionPanel =
                byId(
                    "selectionPanel"
                );


            if (selectionPanel) {

                selectionPanel.style.display =
                    "none";

            }


            updateBudgetUI();

        };


    /* ========================================================
       CONFIRM TRIP
       ======================================================== */

    window.confirmTrip =

        function
        confirmTripConversation() {

            if (
                !selectedCandidate
            ) {

                appendAssistantBubble(

                    "Please choose a destination first."

                );

                return;

            }


            const name =
                destinationName(
                    selectedCandidate
                );


            const country =
                destinationCountry(
                    selectedCandidate
                );


            conversationState.confirmed =
                true;


            const confirmButton =
                byId(
                    "wlConfirmButton"
                );


            if (confirmButton) {

                confirmButton.disabled =
                    true;


                confirmButton.textContent =
                    "TRIP CONFIRMED ✓";

            }


            const oldButton =
                byId(
                    "confirmTripButton"
                );


            if (oldButton) {

                oldButton.disabled =
                    true;


                oldButton.textContent =
                    "TRIP SELECTED ✓";

            }


            addUserChatMessage(
                "Yes, let's go with it."
            );


            const photoList = images(selectedCandidate);
            const photo = photoList[0] || "";
            const totalBudget = Number(basicTripData?.budget);
            let estimate = estimatedCost(selectedCandidate);
            if (estimate === null && typeof getEstimatedWorkerCost === "function") {
                try {
                    const workerEstimate = getEstimatedWorkerCost(selectedCandidate);
                    if (workerEstimate !== null && workerEstimate !== undefined && Number.isFinite(Number(workerEstimate))) estimate = Number(workerEstimate);
                } catch (_) {
                    estimate = null;
                }
            }

            const hasBudget = Number.isFinite(totalBudget) && totalBudget > 0;
            const hasEstimate = estimate !== null && Number.isFinite(Number(estimate));
            const remaining = hasBudget && hasEstimate ? totalBudget - Number(estimate) : null;
            const travelers = basicTripData?.travelers ?? "Not specified";
            const duration = basicTripData?.duration_days ? `${basicTripData.duration_days} days` : "Not specified";
            const travelDates = text(basicTripData?.travel_dates, "Flexible dates");
            const departure = text(basicTripData?.departure_location, "Not specified");
            const transport = text(basicTripData?.transportation_preference, "Not specified");
            const accommodation = text(basicTripData?.accommodation_preference, "Not specified");

            const confirmationRow = appendAssistantBubble(`
                <section class="wl-trip-confirmed-card" aria-label="Confirmed trip overview">
                    <div class="wl-confirmed-heading">
                        <span class="wl-check-badge large" aria-hidden="true">✓</span>
                        <div>
                            <span class="wl-confirmed-eyebrow">DESTINATION CONFIRMED</span>
                            <h3>Your trip starts here</h3>
                            <p>${safeEscape(name)}${country ? `, ${safeEscape(country)}` : ""} is now your selected destination.</p>
                        </div>
                    </div>

                    <div class="wl-confirmed-destination">
                        <div class="wl-confirmed-image-wrap">
                            ${photo ? `<img class="wl-confirmed-image" src="${safeEscape(photo)}" alt="${safeEscape(name)}" loading="lazy" data-image-fallbacks="${safeEscape(JSON.stringify(photoList.slice(1)))}">` : ""}
                            <div class="wl-image-placeholder" ${photo ? "hidden" : ""}><span aria-hidden="true">✦</span><small>Destination preview</small></div>
                        </div>
                        <div class="wl-confirmed-destination-copy">
                            <span class="wl-eyebrow">YOUR DESTINATION</span>
                            <h4>${safeEscape(name)}</h4>
                            ${country ? `<span class="wl-destination-location">⌖ ${safeEscape(country)}</span>` : ""}
                            <p>${safeEscape(destinationDescription(selectedCandidate))}</p>
                        </div>
                    </div>

                    <section class="wl-confirmed-section">
                        <div class="wl-confirmed-section-heading"><h4>Trip overview</h4><span>Your current preferences</span></div>
                        <div class="wl-confirmed-facts">
                            <div class="wl-confirmed-fact"><small>TRAVELERS</small><strong>${safeEscape(travelers)}</strong></div>
                            <div class="wl-confirmed-fact"><small>DURATION</small><strong>${safeEscape(duration)}</strong></div>
                            <div class="wl-confirmed-fact"><small>TRAVEL DATES</small><strong>${safeEscape(travelDates)}</strong></div>
                            <div class="wl-confirmed-fact"><small>DEPARTING FROM</small><strong>${safeEscape(departure)}</strong></div>
                            <div class="wl-confirmed-fact"><small>TRANSPORT</small><strong>${safeEscape(transport)}</strong></div>
                            <div class="wl-confirmed-fact"><small>ACCOMMODATION</small><strong>${safeEscape(accommodation)}</strong></div>
                        </div>
                    </section>

                    <section class="wl-confirmed-section wl-confirmed-budget">
                        <div class="wl-confirmed-section-heading"><h4>Budget overview</h4><span>Research estimates only</span></div>
                        <div class="wl-confirmed-budget-grid">
                            <div class="wl-confirmed-budget-metric"><small>TOTAL BUDGET</small><strong>${hasBudget ? safeEscape(money(totalBudget)) : "Not set"}</strong></div>
                            <div class="wl-confirmed-budget-metric"><small>ESTIMATED TRIP COST</small><strong>${hasEstimate ? safeEscape(money(estimate)) : "Not available"}</strong></div>
                            <div class="wl-confirmed-budget-metric"><small>ESTIMATED REMAINING</small><strong>${remaining !== null ? safeEscape(money(remaining)) : "—"}</strong></div>
                        </div>
                        ${hasBudget && hasEstimate ? `<div class="wl-confirmed-budget-track"><span style="width:${Math.min(100, Math.max(0, Number(estimate) / totalBudget * 100))}%"></span></div><p class="wl-confirmed-budget-note">The current research estimate represents ${(Number(estimate) / totalBudget * 100).toFixed(1)}% of your budget. Prices can change.</p>` : `<p class="wl-confirmed-budget-note">Add or review your budget to track estimated costs and remaining funds.</p>`}
                    </section>

                    <div class="wl-confirmed-footer">
                        <p>No bookings or payments have been made. You can continue refining your trip at any time.</p>
                        <button type="button" class="wl-primary-button" id="wlOpenBudgetButton">Open budget management <span aria-hidden="true">→</span></button>
                    </div>
                </section>
            `, { wide: true });

            byId("wlOpenBudgetButton")?.addEventListener("click", () => {
                if (typeof showPage === "function") showPage("budget");
                else document.querySelector('[data-page="budget"]')?.click();
            });

        };


    /* ========================================================
       RENDER TRIP RESULTS OVERRIDE
       ======================================================== */

    window.renderTripResults =

        function
        renderTripResultsConversation(
            trip
        ) {

            const candidates =
                getPlannerCandidates(
                    trip
                );


            currentCandidates =
                candidates;


            const resultsSection =
                byId(
                    "resultsSection"
                );


            if (resultsSection) {

                resultsSection.style.display =
                    "none";

            }


            if (
                candidates.length ===
                3
            ) {

                addOptionsMessage(
                    candidates
                );

            }

        };


    /* ========================================================
       LOAD LAST TRIP OVERRIDE
       ======================================================== */

    window.loadLastTrip =

        function
        loadLastTripConversation() {

            const stored =

                localStorage.getItem(
                    STORAGE_KEYS.lastTrip
                );


            if (!stored) {

                return;

            }


            try {

                const parsed =
                    JSON.parse(
                        stored
                    );


                const candidates =
                    getPlannerCandidates(
                        parsed
                    );


                if (
                    candidates.length !==
                    3
                ) {

                    return;

                }


                currentTrip =
                    parsed;


                currentCandidates =
                    candidates;


                openConversation();


                appendAssistantBubble(

                    `

                        <div
                            class="wl-conversation-text"
                        >

                            <strong>
                                I restored your latest destination search.
                            </strong>


                            <span>
                                Choose one of the options below
                                to continue.
                            </span>

                        </div>

                    `

                );


                addOptionsMessage(
                    candidates
                );

            } catch (error) {

                console.warn(

                    "Unable to restore previous trip result:",

                    error

                );

            }

        };


    /* ========================================================
       CSS
       ======================================================== */

    const style =
        document.createElement(
            "style"
        );


    style.textContent = `
        /* Compact spacing override: preserve the layout and typography, remove only excess gaps. */
        .wl-destination-detail { padding: clamp(14px, 1.6vw, 22px); }
        .wl-detail-header { margin-bottom: 14px; }
        .wl-destination-facts { margin-top: 12px; gap: 10px; }
        .wl-attractions-section { margin-top: 16px; padding-top: 14px; }
        .wl-section-heading { margin-bottom: 10px; }
        .wl-attractions-grid { gap: 10px; }
        .wl-attraction-copy { padding: 10px 11px 11px; }
        .wl-confirm-actions { margin-top: 16px; }
        .wl-confirmed-section { margin-top: 16px; }
        .wl-confirmed-section-heading { margin-bottom: 9px; }
        .wl-confirmed-budget { padding: 14px; }
        .wl-confirmed-footer { margin-top: 16px; padding-top: 14px; }
        .wl-confirmed-destination { margin-bottom: 14px; }
        .wl-confirmed-heading { margin-bottom: 16px; }
        .wl-confirmed-budget-grid { gap: 10px; }

        .trip-chat-row.conversation-wide > div { width: 100%; max-width: 100%; }
        .conversation-bubble { overflow: hidden; }
        .wl-conversation-text {
            display: grid;
            width: 100%;
            gap: 6px;
            margin: 0 0 8px;
            padding: 0;
            line-height: 1.5;
            text-align: left;
            direction: ltr;
        }

        .wl-conversation-text strong,
        .wl-conversation-text span {
            text-align: left;
        }

        .wl-options-grid {
            display: grid;
            width: 100%;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            align-items: stretch;
            gap: 14px;
            margin: 8px 0 0;
            padding: 0;
        }

        .wl-thinking { display: grid; gap: 12px; min-width: 0; padding: 8px 0; }
        .wl-thinking-title { display: flex; align-items: center; gap: 10px; color: #10294a; font-size: 16px; font-weight: 750; }
        .wl-thinking-dot { width: 9px; height: 9px; flex: 0 0 auto; border-radius: 50%; background: #3478f6; animation: wlPulse 1.2s infinite ease-in-out; }
        .wl-thinking-stage { color: #64748b; font-size: 13px; }
        .wl-thinking-progress { display: flex; flex-wrap: wrap; gap: 8px; }
        .wl-thinking-step { padding: 8px 12px; border: 1px solid #e2e8f0; border-radius: 999px; background: #fff; color: #94a3b8; font-size: 12px; }
        .wl-thinking-step.active { border-color: #a9c8ff; background: #eff6ff; color: #1d4ed8; }

        .wl-options-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); align-items: stretch; gap: 16px; margin-top: 16px; }
        .wl-option-card { display: flex; flex-direction: column; min-width: 0; overflow: hidden; border: 1px solid #e1e8f1; border-radius: 18px; background: #fff; box-shadow: 0 5px 18px rgba(15, 41, 74, .035); transition: border-color .18s ease, box-shadow .18s ease, transform .18s ease; }
        .wl-option-card:hover { transform: translateY(-3px); border-color: #b8cff2; box-shadow: 0 12px 26px rgba(15, 41, 74, .09); }
        .wl-option-card.selected { border-color: #2f6df6; box-shadow: 0 0 0 3px rgba(47, 109, 246, .12); }
        .wl-option-image-wrap, .wl-destination-hero-media, .wl-attraction-image-wrap, .wl-confirmed-image-wrap { position: relative; min-width: 0; overflow: hidden; background: #eef4fa; }
        .wl-option-image-wrap { height: clamp(150px, 16vw, 205px); }
        .wl-option-image { display: block; width: 100%; height: 100%; object-fit: cover; background: #eef3f8; }
        .wl-image-placeholder { display: grid; place-content: center; justify-items: center; gap: 8px; width: 100%; min-height: 100%; padding: 16px; box-sizing: border-box; background: linear-gradient(135deg, #edf4fb, #f8fafc); color: #4774a5; text-align: center; }
        .wl-image-placeholder[hidden] { display: none !important; }
        .wl-image-placeholder span { font-size: 28px; line-height: 1; }
        .wl-image-placeholder small { color: #6d829c; font-size: 11px; font-weight: 650; }
.wl-option-body {
    display: flex;
    flex-direction: column;
    align-items: stretch;
    justify-content: flex-start;
    gap: 0;
    padding: 16px;
    text-align: left;
    direction: ltr;
    min-width: 0;
}

.wl-option-number {
    align-self: flex-start;
    margin: 0 0 10px;
}

.wl-option-title {
    width: 100%;
    margin: 0;
    padding: 0;
    text-align: left;
    overflow-wrap: anywhere;
}

.wl-option-country {
    width: 100%;
    margin: 6px 0 0;
    text-align: left;
}

.wl-option-description {
    width: 100%;
    margin: 12px 0;
    text-align: left;
    overflow-wrap: anywhere;
}

.wl-option-attractions span {
    display: block;
    width: 100%;
    box-sizing: border-box;
    padding: 10px;
    border-radius: 9px;
    background: #f1f5f9;
    color: #52647c;
    font-size: 12px;
    line-height: 1.45;
    text-align: left;
    overflow-wrap: anywhere;
}
        .wl-option-actions, .wl-confirm-actions { display: flex; align-items: center; justify-content: flex-end; gap: 10px; flex-wrap: wrap; }
        .wl-option-actions { width: 100%; margin-top: auto; padding-top: 8px; }
        .wl-option-actions button { flex: 1 1 105px; min-height: 42px; }

        .wl-primary-button, .wl-secondary-button { display: inline-flex; align-items: center; justify-content: center; gap: 8px; min-height: 44px; padding: 11px 18px; border-radius: 999px; font: inherit; font-size: 12px; font-weight: 750; line-height: 1.25; text-align: center; cursor: pointer; transition: transform .15s ease, box-shadow .15s ease, background .15s ease; }
        .wl-primary-button { border: 1px solid #e76500; background: #e76500; color: #fff; box-shadow: 0 5px 12px rgba(231, 101, 0, .12); }
        .wl-primary-button:hover { background: #cf5700; box-shadow: 0 7px 17px rgba(231, 101, 0, .2); }
        .wl-secondary-button { border: 1px solid #d7e1ef; background: #fff; color: #10294a; }
        .wl-secondary-button:hover { border-color: #a9bfdd; background: #f8fbff; }
        .wl-primary-button:active, .wl-secondary-button:active { transform: translateY(1px); }
        .wl-primary-button:disabled { opacity: .6; cursor: not-allowed; }

        .wl-destination-detail { width: 100%; max-width: 1180px; margin: 0 auto; padding: clamp(16px, 2.2vw, 28px); border: 1px solid #e7edf5; border-radius: 20px; background: #fff; box-shadow: 0 10px 30px rgba(15, 41, 74, .055); color: #10294a; box-sizing: border-box; text-align: left; }
        .wl-detail-header { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }
        .wl-brand-mark { display: grid; place-items: center; width: 44px; height: 44px; flex: 0 0 auto; border-radius: 50%; background: #08294d; color: #fff; font-size: 23px; font-weight: 800; }
        .wl-detail-brand { display: grid; gap: 3px; min-width: 0; }
        .wl-detail-brand strong { color: #10294a; font-size: 16px; }
        .wl-detail-brand span { color: #7b8da8; font-size: 12px; }
        .wl-selected-status { display: inline-flex; align-items: center; gap: 7px; margin-left: auto; padding: 8px 12px; border-radius: 999px; background: #eaf8ef; color: #16803d; font-size: 12px; font-weight: 650; white-space: nowrap; }
        .wl-selected-status span { display: grid; place-items: center; width: 17px; height: 17px; border-radius: 50%; background: #16803d; color: #fff; font-size: 11px; }
        .wl-destination-hero { display: grid; grid-template-columns: minmax(0, 1.15fr) minmax(260px, .9fr); gap: clamp(18px, 2vw, 30px); align-items: center; }
        .wl-destination-hero-media { height: clamp(220px, 24vw, 330px); border-radius: 15px; }
        .wl-destination-hero-image { display: block; width: 100%; height: 100%; object-fit: cover; background: linear-gradient(135deg, #e5eef9, #f4f7fb); }
        .wl-destination-hero-media .wl-image-placeholder { position: absolute; inset: 0; }
        .wl-destination-copy { min-width: 0; }
        .wl-eyebrow { display: block; margin-bottom: 8px; color: #3478f6; font-size: 11px; font-weight: 800; letter-spacing: .1em; text-transform: uppercase; }
        .wl-destination-copy h2 { margin: 0; color: #10294a; font-size: clamp(23px, 2.1vw, 32px); font-weight: 800; line-height: 1.15; letter-spacing: -.025em; overflow-wrap: anywhere; }
        .wl-destination-location { display: flex; align-items: flex-start; gap: 8px; margin-top: 12px; color: #667993; font-size: 13px; line-height: 1.45; }
        .wl-destination-location span { color: #4c79b7; font-size: 18px; line-height: 1; }
        .wl-destination-copy p { margin: 18px 0 0; color: #5c6f89; font-size: 14px; line-height: 1.65; text-align: left; overflow-wrap: anywhere; }

        .wl-destination-facts { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin-top: 18px; }
        .wl-fact-card { display: flex; align-items: center; gap: 12px; min-width: 0; padding: 16px; border-radius: 13px; background: #f4f7fb; }
        .wl-fact-icon { display: grid; place-items: center; width: 36px; height: 36px; flex: 0 0 auto; border-radius: 10px; background: #fff; color: #245a91; font-size: 20px; }
        .wl-fact-card small { display: block; color: #8091aa; font-size: 10px; font-weight: 750; letter-spacing: .07em; }
        .wl-fact-card strong { display: block; margin-top: 5px; color: #183454; font-size: 13px; line-height: 1.4; overflow-wrap: anywhere; }

        .wl-attractions-section { margin-top: 22px; padding-top: 20px; border-top: 1px solid #e8edf4; }
        .wl-section-heading { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 14px; }
        .wl-section-heading > div { display: flex; align-items: center; gap: 10px; }
        .wl-section-icon { color: #3478f6; font-size: 24px; }
        .wl-section-heading h3 { margin: 0; color: #10294a; font-size: 19px; font-weight: 800; }
        .wl-section-caption { color: #8797ad; font-size: 12px; }
        .wl-attractions-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }
        .wl-attraction-card { min-width: 0; overflow: hidden; border: 1px solid #e8edf4; border-radius: 12px; background: #fff; }
        .wl-attraction-image-wrap { height: 105px; }
        .wl-attraction-image { display: block; width: 100%; height: 100%; object-fit: cover; background: #eef4fa; }
        .wl-attraction-image-wrap .wl-image-placeholder { position: absolute; inset: 0; }
        .wl-attraction-copy { padding: 11px 12px 13px; }
        .wl-attraction-copy strong { display: block; color: #1b3554; font-size: 12px; font-weight: 750; line-height: 1.45; overflow-wrap: anywhere; }
        .wl-destination-detail .wl-confirm-actions { justify-content: center; margin-top: 20px; }
        .wl-destination-detail .wl-confirm-actions .wl-secondary-button { min-width: 220px; }
        .wl-destination-detail .wl-confirm-actions .wl-primary-button { max-width: 100%; min-width: 280px; }
        .wl-confirm-preview { display: grid; grid-template-columns: minmax(120px, 180px) minmax(0, 1fr); gap: 16px; align-items: start; margin: 16px 0; padding: 14px; border: 1px solid #e2e8f0; border-radius: 14px; background: #f8fafc; }
        .wl-confirm-image { display: block; width: 100%; height: 120px; border-radius: 10px; object-fit: cover; }
        .wl-confirm-preview-copy { min-width: 0; text-align: left; }
        .wl-confirm-preview-copy > strong, .wl-confirm-preview-copy > span { display: block; }
        .wl-confirm-preview-copy > strong { color: #10294a; font-size: 18px; line-height: 1.35; }
        .wl-confirm-preview-copy > span { margin-top: 5px; color: #3478f6; font-size: 12px; }
        .wl-confirm-preview-copy p { margin: 10px 0 0; color: #5c6f89; font-size: 13px; line-height: 1.6; text-align: left; }
        .wl-confirm-question { display: grid; gap: 5px; margin-bottom: 12px; text-align: left; }
        .wl-confirm-question strong { color: #10294a; font-size: 18px; }
        .wl-confirm-question span { color: #64748b; font-size: 13px; }
        .wl-confirmed-message { display: flex; align-items: center; gap: 12px; text-align: left; }
        .wl-confirmed-message strong, .wl-confirmed-message span { display: block; }
        .wl-confirmed-message span { margin-top: 4px; color: #64748b; font-size: 13px; }
        .wl-check-badge { display: grid; place-items: center; width: 30px; height: 30px; flex: 0 0 auto; border-radius: 50%; background: #e8f5ee; color: #15803d; font-weight: 900; }
        .wl-check-badge.large { width: 42px; height: 42px; font-size: 18px; }

        .wl-trip-confirmed-card { width: 100%; max-width: 1180px; margin: 0 auto; padding: clamp(16px, 2.2vw, 28px); border: 1px solid #e3ebf5; border-radius: 20px; background: #fff; box-shadow: 0 10px 30px rgba(15, 41, 74, .055); color: #10294a; text-align: left; }
        .wl-confirmed-heading { display: flex; align-items: flex-start; gap: 14px; padding-bottom: 20px; border-bottom: 1px solid #e8edf4; }
        .wl-confirmed-heading h3 { margin: 3px 0 5px; color: #10294a; font-size: clamp(21px, 2vw, 28px); line-height: 1.2; }
        .wl-confirmed-heading p { margin: 0; color: #657891; font-size: 14px; line-height: 1.55; }
        .wl-confirmed-eyebrow { color: #16803d; font-size: 10px; font-weight: 800; letter-spacing: .12em; }
        .wl-confirmed-destination { display: grid; grid-template-columns: minmax(180px, .8fr) minmax(0, 1.2fr); gap: 20px; align-items: stretch; margin-top: 20px; padding: 14px; border: 1px solid #e6edf5; border-radius: 15px; background: #f8fafc; }
        .wl-confirmed-image-wrap { min-height: 190px; border-radius: 11px; }
        .wl-confirmed-image { display: block; width: 100%; height: 100%; min-height: 190px; object-fit: cover; }
        .wl-confirmed-image-wrap .wl-image-placeholder { position: absolute; inset: 0; }
        .wl-confirmed-destination-copy { align-self: center; min-width: 0; padding: 8px 4px; }
        .wl-confirmed-destination-copy h4 { margin: 5px 0 8px; color: #10294a; font-size: clamp(19px, 2vw, 25px); line-height: 1.25; overflow-wrap: anywhere; }
        .wl-confirmed-destination-copy .wl-destination-location { display: block; margin: 0; }
        .wl-confirmed-destination-copy p { margin: 12px 0 0; color: #5c6f89; font-size: 13px; line-height: 1.65; }
        .wl-confirmed-section { margin-top: 22px; }
        .wl-confirmed-section-heading { display: flex; align-items: baseline; justify-content: space-between; gap: 12px; margin-bottom: 12px; }
        .wl-confirmed-section-heading h4 { margin: 0; color: #10294a; font-size: 17px; }
        .wl-confirmed-section-heading span { color: #8797ad; font-size: 11px; }
        .wl-confirmed-facts { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }
        .wl-confirmed-fact, .wl-confirmed-budget-metric { min-width: 0; padding: 14px; border: 1px solid #e5ebf3; border-radius: 11px; background: #fff; }
        .wl-confirmed-fact small, .wl-confirmed-budget-metric small { display: block; color: #8292a8; font-size: 9px; font-weight: 800; letter-spacing: .07em; }
        .wl-confirmed-fact strong, .wl-confirmed-budget-metric strong { display: block; margin-top: 7px; color: #173655; font-size: 13px; line-height: 1.4; overflow-wrap: anywhere; }
        .wl-confirmed-budget { padding: 17px; border: 1px solid #e5ebf3; border-radius: 14px; background: #f8fafc; }
        .wl-confirmed-budget-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }
        .wl-confirmed-budget-metric { background: #fff; }
        .wl-confirmed-budget-track { height: 8px; margin-top: 14px; overflow: hidden; border-radius: 999px; background: #e2e8f0; }
        .wl-confirmed-budget-track span { display: block; height: 100%; border-radius: inherit; background: #3478f6; }
        .wl-confirmed-budget-note { margin: 10px 0 0; color: #6d7f96; font-size: 11px; line-height: 1.55; }
        .wl-confirmed-footer { display: flex; align-items: center; justify-content: space-between; gap: 16px; margin-top: 20px; padding-top: 18px; border-top: 1px solid #e8edf4; }
        .wl-confirmed-footer p { max-width: 560px; margin: 0; color: #7b8da3; font-size: 11px; line-height: 1.55; }
        .wl-confirmed-footer .wl-primary-button { flex: 0 0 auto; }

        @keyframes wlPulse { 0%, 100% { opacity: .35; transform: scale(.85); } 50% { opacity: 1; transform: scale(1); } }

        @media (max-width: 980px) {
            .wl-options-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
            .wl-destination-hero { grid-template-columns: minmax(0, 1fr); }
            .wl-destination-hero-media { height: clamp(210px, 38vw, 320px); }
            .wl-destination-copy p { margin-top: 12px; }
            .wl-confirmed-destination { grid-template-columns: minmax(0, 1fr); }
            .wl-confirmed-image-wrap, .wl-confirmed-image { min-height: 220px; }
        }
        @media (max-width: 640px) {
            .wl-options-grid, .wl-attractions-grid { grid-template-columns: minmax(0, 1fr); }
            .wl-option-image { height: 190px; }
            .wl-option-body { padding: 16px; }
            .wl-destination-detail { padding: 14px; border-radius: 15px; }
            .wl-detail-header { align-items: flex-start; flex-wrap: wrap; }
            .wl-selected-status { margin-left: 0; }
            .wl-brand-mark { width: 38px; height: 38px; font-size: 20px; }
            .wl-destination-hero-media { height: 210px; }
            .wl-destination-facts { grid-template-columns: minmax(0, 1fr); }
            .wl-confirmed-facts, .wl-confirmed-budget-grid { grid-template-columns: minmax(0, 1fr); }
            .wl-confirmed-section-heading, .wl-confirmed-footer { align-items: stretch; flex-direction: column; }
            .wl-confirmed-footer .wl-primary-button { width: 100%; }
            .wl-option-image-wrap { height: 190px; }
            .wl-fact-card { padding: 12px; }
            .wl-attraction-image, .wl-attraction-placeholder { height: 150px; }
            .wl-section-caption { display: none; }
            .wl-destination-detail .wl-confirm-actions { align-items: stretch; }
            .wl-destination-detail .wl-confirm-actions button { width: 100%; min-width: 0; }
            .wl-confirm-preview { grid-template-columns: minmax(0, 1fr); }
            .wl-confirm-image { height: 170px; }
            .wl-confirm-actions button { width: 100%; }
            .wl-thinking-progress { display: grid; grid-template-columns: minmax(0, 1fr); }
            .wl-thinking-step { text-align: center; }
        }
        @media (prefers-reduced-motion: reduce) {
            .wl-thinking-dot { animation: none; }
            .wl-option-card, .wl-primary-button, .wl-secondary-button { transition: none; }
        }
    
        .wl-smart-budget { margin-top: 16px; padding: 16px; border: 1px solid #e2eaf4; border-radius: 16px; background: #f8fbff; color: #10294a; }
        .wl-smart-budget-heading { display:flex; align-items:center; justify-content:space-between; gap:12px; margin-bottom:12px; }
        .wl-smart-budget-heading h3 { margin:4px 0 0; font-size:17px; line-height:1.3; }
        .wl-budget-pill { padding:5px 9px; border-radius:999px; background:#eaf1fc; color:#285b9b; font-size:11px; font-weight:800; }
        .wl-smart-budget-summary { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:8px; margin-bottom:12px; }
        .wl-smart-budget-summary > div { min-width:0; padding:10px; border:1px solid #e5edf7; border-radius:10px; background:#fff; }
        .wl-smart-budget-summary small { display:block; color:#718198; font-size:9px; font-weight:800; letter-spacing:.045em; }
        .wl-smart-budget-summary strong { display:block; margin-top:5px; color:#10294a; font-size:15px; overflow-wrap:anywhere; }
        .wl-smart-budget-rows { display:grid; gap:0; border:1px solid #e5edf7; border-radius:11px; background:#fff; overflow:hidden; }
        .wl-smart-budget-row { display:flex; align-items:flex-start; justify-content:space-between; gap:14px; padding:10px 12px; border-bottom:1px solid #edf2f8; font-size:12px; }
        .wl-smart-budget-row:last-child { border-bottom:0; }
        .wl-smart-budget-row > span { color:#5d6f86; }
        .wl-smart-budget-row > strong { max-width:65%; color:#10294a; text-align:right; font-size:12px; }
        .wl-smart-budget-row small { display:block; margin-top:3px; color:#8492a5; font-size:10px; font-weight:500; }
        .wl-smart-budget-row .wl-budget-calculated { color:#48658a; font-weight:650; }
        .wl-smart-budget-status { display:grid; gap:4px; margin-top:10px; padding:11px 12px; border-radius:10px; font-size:12px; }
        .wl-smart-budget-status > strong { font-size:14px; }
        .wl-smart-budget-status > span { line-height:1.45; }
        .wl-smart-budget-status.good { background:#ecfdf5; color:#047857; }
        .wl-smart-budget-status.over { background:#fff1f2; color:#be123c; }
        .wl-smart-budget-status.neutral { background:#eef4fb; color:#52647c; }
        .wl-smart-budget-note { margin:8px 0 0; color:#64748b; font-size:11px; line-height:1.5; }
        .wl-smart-budget-tips { margin-top:11px; font-size:12px; color:#40546d; }
        .wl-smart-budget-tips > strong { color:#10294a; }
        .wl-smart-budget-tips ul { margin:6px 0 0; padding-left:18px; }
        .wl-smart-budget-tips li { margin:4px 0; line-height:1.45; }
        .wl-smart-budget-disclaimer { margin:10px 0 0; color:#8794a7; font-size:10px; line-height:1.45; }
        @media (max-width: 600px) {
            .wl-smart-budget { padding:12px; }
            .wl-smart-budget-summary { gap:6px; }
            .wl-smart-budget-summary > div { padding:8px; }
            .wl-smart-budget-summary strong { font-size:13px; }
            .wl-smart-budget-row { gap:8px; }
        }
`;


    document.head.appendChild(
        style
    );


})();