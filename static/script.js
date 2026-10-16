/* ============================================================
   WANDERLUST
   FRONTEND CONTROLLER
   ============================================================

   FRONTEND ARCHITECTURE

       index.html
            |
            v
       script.js
            |
            v
         app.py
            |
            v
         main.py
            |
            +-----------------------------+
            |                             |
            v                             v
       MoodAgent
            |
            v
       TravelAgent (GPT-OSS 20B Cloud)
            |
            v
       ResearchAgent (GPT-OSS 120B Cloud + Tavily)
            |
            v
       TravelAgent (Tavily basic info + consistency check)
            |
            +--> Pexels images / MapTiler coordinates
            |
            v
          main.py
            |
            v
          app.py
                                         |
                                         v
                                    script.js


   IMPORTANT

   The frontend does NOT know about:

       - Groq
       - Gemini
       - NVIDIA
       - Ollama
       - Gemma
       - Qwen
       - LLM7
       - Tavily
       - Pexels
       - MapTiler
       - ResearchAgent internals
       - Ollama model internals

   The frontend only communicates with Flask.

   Current API:

       GET  /api/health

       POST /api/trip/start

       Request:
       {
           "user_input": "..."
       }

       Response:
       {
           "success": true,
           "data": {
               ...final StructureAgent result...
           }
       }

============================================================ */


/* ============================================================
   GLOBAL STATE
   ============================================================ */

let currentTrip = null;

let basicTripData = null;

let currentCandidates = [];

let selectedCandidate = null;

let tripStartInProgress = false;

let tripChatProcessing = false;

let chatStarted = false;


/* ============================================================
   LOCAL STORAGE
   ============================================================ */

const STORAGE_KEYS = {

    basicTrip:
        "wanderlust_basic_trip",

    lastTrip:
        "wanderlust_last_trip"

};


/* ============================================================
   API
   ============================================================ */

const API = {

    async request(
        endpoint,
        method = "GET",
        data = null
    ) {

        const options = {
            method: method,
            headers: {
                "Accept": "application/json"
            }
        };


        if (data !== null) {

            options.headers[
                "Content-Type"
            ] = "application/json";

            options.body =
                JSON.stringify(data);

        }


        let response;


        try {

            response =
                await fetch(
                    endpoint,
                    options
                );

        } catch (error) {

            throw new Error(
                "Unable to connect to the Flask server. Make sure app.py is running."
            );

        }


        let payload;


        try {

            payload =
                await response.json();

        } catch (error) {

            throw new Error(
                "The Flask server returned an invalid JSON response."
            );

        }


        if (
            !response.ok ||
            payload.success !== true
        ) {

            throw new Error(
                payload.error ||
                payload.message ||
                "The backend request failed."
            );

        }


        return payload.data;

    },


    health() {

        return this.request(
            "/api/health",
            "GET"
        );

    },


    startTrip(userInput) {

        return this.request(
            "/api/trip/start",
            "POST",
            {
                user_input:
                    String(userInput || "")
            }
        );

    }

};


/* ============================================================
   BASIC DOM HELPERS
   ============================================================ */

function value(id) {

    const element =
        document.getElementById(id);


    if (!element) {
        return "";
    }


    return String(
        element.value || ""
    ).trim();

}


/* ============================================================
   MESSAGE HELPERS
   ============================================================ */

function setMessage(
    id,
    message,
    visible = true
) {

    const element =
        document.getElementById(id);


    if (!element) {
        return;
    }


    element.textContent =
        String(message || "");


    element.style.display =
        visible
            ? "block"
            : "none";

}


/* ============================================================
   HTML ESCAPING
   ============================================================ */

function escapeHtml(text) {

    return String(
        text ?? ""
    )
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


/* ============================================================
   VALUE HELPERS
   ============================================================ */

function firstNonEmpty(...values) {

    for (
        const item
        of values
    ) {

        if (
            item === null ||
            item === undefined
        ) {
            continue;
        }


        if (
            typeof item === "string" &&
            item.trim()
        ) {

            return item.trim();

        }


        if (
            typeof item === "number" &&
            Number.isFinite(item)
        ) {

            return item;

        }

    }


    return "";

}


/* ============================================================
   MONEY
   ============================================================ */

function formatMoney(number) {

    const amount =
        Number(number);


    if (
        !Number.isFinite(amount)
    ) {

        return "Not available";

    }


    return amount.toLocaleString(
        "en-CA",
        {
            style: "currency",
            currency: "CAD"
        }
    );

}


/* ============================================================
   NUMBER
   ============================================================ */

function formatNumber(number) {

    const amount =
        Number(number);


    if (
        !Number.isFinite(amount)
    ) {

        return "—";

    }


    return amount.toLocaleString(
        "en-CA",
        {
            maximumFractionDigits: 4
        }
    );

}


/* ============================================================
   PAGE NAVIGATION
   ============================================================ */

function showPage(pageName) {

    document
        .querySelectorAll(".page")
        .forEach(page => {

            page.classList.remove(
                "active"
            );

        });


    const target =
        document.getElementById(
            "page-" + pageName
        );


    if (target) {

        target.classList.add(
            "active"
        );

    }


    document
        .querySelectorAll(".nav-button")
        .forEach(button => {

            button.classList.toggle(
                "active",
                button.dataset.page ===
                    pageName
            );

        });


    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });


    if (
        pageName === "planner"
    ) {

        updatePlannerAvailability();

    }


    if (
        pageName === "budget"
    ) {

        updateBudgetUI();

    }


    if (
        pageName === "search"
    ) {

        renderLocalSearchResults();

    }


    if (
        pageName === "random"
    ) {

        loadRandomDestination();

    }

}


/* ============================================================
   COUNTRY DETECTION
   ============================================================ */

function detectDepartureCountry(text) {

    const lower =
        String(text || "")
            .toLowerCase();


    const countries = [

        [
            "canada",
            "Canada"
        ],

        [
            "united states",
            "United States"
        ],

        [
            "usa",
            "United States"
        ],

        [
            "india",
            "India"
        ],

        [
            "japan",
            "Japan"
        ],

        [
            "france",
            "France"
        ],

        [
            "germany",
            "Germany"
        ],

        [
            "italy",
            "Italy"
        ],

        [
            "switzerland",
            "Switzerland"
        ],

        [
            "australia",
            "Australia"
        ],

        [
            "new zealand",
            "New Zealand"
        ],

        [
            "united kingdom",
            "United Kingdom"
        ]

    ];


    for (
        const [
            needle,
            country
        ]
        of countries
    ) {

        if (
            lower.includes(
                needle
            )
        ) {

            return country;

        }

    }


    const canadianProvinceCodes = [

        "ab",
        "bc",
        "mb",
        "nb",
        "nl",
        "ns",
        "nt",
        "nu",
        "on",
        "pe",
        "qc",
        "sk",
        "yt"

    ];


    const parts =
        lower
            .split(/[, ]+/)
            .map(
                item =>
                    item.trim()
            )
            .filter(Boolean);


    if (
        parts.some(
            item =>
                canadianProvinceCodes
                    .includes(item)
        )
    ) {

        return "Canada";

    }


    return "";

}


/* ============================================================
   TRIP SCOPE
   ============================================================ */

function getTripScope() {

    return document.querySelector(
        'input[name="trip_scope"]:checked'
    )?.value || "domestic";

}


/* ============================================================
   COUNTRY FIELD
   ============================================================ */

function updateCountryField() {

    const scope =
        getTripScope();


    const countryField =
        document.getElementById(
            "countryField"
        );


    const countryInput =
        document.getElementById(
            "country"
        );


    const hint =
        document.getElementById(
            "countryHint"
        );


    if (
        !countryField ||
        !countryInput
    ) {

        return;

    }


    const detectedCountry =
        detectDepartureCountry(
            value(
                "departure_location"
            )
        );


    if (
        scope === "domestic" &&
        detectedCountry
    ) {

        countryInput.value =
            detectedCountry;


        countryField.style.display =
            "none";


        if (hint) {

            hint.textContent =
                "Departure country detected automatically.";

        }

    } else {

        countryField.style.display =
            "flex";


        if (hint) {

            hint.textContent =
                "";

        }

    }

}


/* ============================================================
   BUILD BASIC TRIP DATA
   ============================================================ */

function buildBasicTripData() {

    const travelers =
        Number(
            value("travelers")
        );


    const duration =
        Number(
            value("duration_days")
        );


    const budget =
        Number(
            value("budget")
        );


    return {

        departure_location:
            value(
                "departure_location"
            ),

        trip_scope:
            getTripScope(),

        country:
            value("country") ||
            null,

        region:
            null,

        travelers:
            Number.isFinite(
                travelers
            )
                ? travelers
                : null,

        duration_days:
            Number.isFinite(
                duration
            )
                ? duration
                : null,

        travel_dates:
            value(
                "travel_dates"
            ),

        maximum_total_travel_time:
            value(
                "maximum_total_travel_time"
            ),

        maximum_distance:
            value(
                "maximum_distance"
            ),

        transportation_preference:
            value(
                "transportation_preference"
            ),

        accommodation_preference:
            value(
                "accommodation_preference"
            ),

        safety_requirement:
            value(
                "safety_requirement"
            ),

        budget:
            Number.isFinite(
                budget
            )
                ? budget
                : null,

        currency:
            "CAD",

        other:
            value("other")

    };

}


/* ============================================================
   VALIDATE BASIC DATA
   ============================================================ */

function validateBasicTripData(data) {

    if (
        !data.departure_location
    ) {

        return (
            "Please enter your departure location."
        );

    }


    if (
        !Number.isFinite(
            data.travelers
        ) ||
        data.travelers < 1
    ) {

        return (
            "Please enter a valid number of travelers."
        );

    }


    if (
        !Number.isFinite(
            data.duration_days
        ) ||
        data.duration_days < 1
    ) {

        return (
            "Please enter a valid trip duration."
        );

    }


    if (
        !data.travel_dates
    ) {

        return (
            "Please enter your travel dates."
        );

    }


    if (
        !Number.isFinite(
            data.budget
        ) ||
        data.budget <= 0
    ) {

        return (
            "Please enter a valid travel budget."
        );

    }


    if (
        data.trip_scope ===
            "international" &&
        !data.country
    ) {

        return (
            "Please enter the country you want to travel to."
        );

    }


    return null;

}


/* ============================================================
   SAVE BASIC INFORMATION
   ============================================================ */

function saveBasicInformation() {

    const data =
        buildBasicTripData();


    const error =
        validateBasicTripData(
            data
        );


    if (error) {

        setMessage(
            "basicError",
            error,
            true
        );

        return null;

    }


    basicTripData =
        data;


    localStorage.setItem(
        STORAGE_KEYS.basicTrip,
        JSON.stringify(data)
    );


    setMessage(
        "basicError",
        "",
        false
    );


    setMessage(
        "basicSaved",
        "Trip information saved locally. You can now describe the experience you want.",
        true
    );


    updatePlannerAvailability();


    return data;

}


/* ============================================================
   LOAD BASIC INFORMATION
   ============================================================ */

function loadBasicInformation() {

    const stored =
        localStorage.getItem(
            STORAGE_KEYS.basicTrip
        );


    if (!stored) {
        return;
    }


    try {

        basicTripData =
            JSON.parse(
                stored
            );

    } catch (error) {

        basicTripData =
            null;

        return;

    }


    if (
        !basicTripData ||
        typeof basicTripData !==
            "object"
    ) {

        basicTripData =
            null;

        return;

    }


    const fields = [

        "departure_location",
        "country",
        "travelers",
        "duration_days",
        "travel_dates",
        "maximum_total_travel_time",
        "maximum_distance",
        "transportation_preference",
        "accommodation_preference",
        "safety_requirement",
        "budget",
        "other"

    ];


    fields.forEach(id => {

        const element =
            document.getElementById(
                id
            );


        if (!element) {
            return;
        }


        const storedValue =
            basicTripData[id];


        if (
            storedValue !== null &&
            storedValue !== undefined
        ) {

            element.value =
                storedValue;

        }

    });


    const scopeInput =
        document.querySelector(
            `input[name="trip_scope"][value="${basicTripData.trip_scope || "domestic"}"]`
        );


    if (scopeInput) {

        scopeInput.checked =
            true;

    }


    updateCountryField();

    updatePlannerAvailability();

}


/* ============================================================
   BUILD BACKEND REQUEST
   ============================================================

   The backend expects ONE natural-language user_input.

   We therefore combine the practical trip information with
   the user's experience request here.

============================================================ */

function buildPlannerRequest(
    preferenceText
) {

    const basic =
        basicTripData ||
        buildBasicTripData();


    const preference =
        String(
            preferenceText || ""
        ).trim();


    const lines = [

        "I want Wanderlust to plan a trip using these requirements:",

        "",

        "PRACTICAL TRIP INFORMATION",

        `Departure location: ${
            basic.departure_location ||
            "not specified"
        }`,

        `Trip scope: ${
            basic.trip_scope ||
            "not specified"
        }`,

        `Country: ${
            basic.country ||
            "not specified"
        }`,

        `Number of travelers: ${
            basic.travelers ??
            "not specified"
        }`,

        `Trip duration: ${
            basic.duration_days ??
            "not specified"
        } days`,

        `Travel dates: ${
            basic.travel_dates ||
            "not specified"
        }`,

        `Maximum total travel time: ${
            basic.maximum_total_travel_time ||
            "no preference"
        }`,

        `Maximum travel distance: ${
            basic.maximum_distance ||
            "no preference"
        }`,

        `Transportation preference: ${
            basic.transportation_preference ||
            "no preference"
        }`,

        `Accommodation preference: ${
            basic.accommodation_preference ||
            "no preference"
        }`,

        `Safety requirements: ${
            basic.safety_requirement ||
            "none"
        }`,

        `Total budget: ${
            basic.budget ??
            "not specified"
        } ${basic.currency || "CAD"}`,

        `Other requirements: ${
            basic.other ||
            "none"
        }`,

        "",

        "TRAVEL EXPERIENCE REQUEST",

        preference

    ];


    return lines.join("\n");

}


/* ============================================================
   PLANNER AVAILABILITY
   ============================================================ */

function updatePlannerAvailability() {

    const notice =
        document.getElementById(
            "plannerBasicNotice"
        );


    const panel =
        document.getElementById(
            "preferencePanel"
        );


    if (
        !notice ||
        !panel
    ) {

        return;

    }


    const data =
        basicTripData ||
        buildBasicTripData();


    const valid =
        !validateBasicTripData(
            data
        );


    notice.style.display =
        valid
            ? "none"
            : "block";


    panel.style.opacity =
        valid
            ? "1"
            : "0.72";

}


/* ============================================================
   START TRIP
   ============================================================ */

async function startTrip() {

    if (
        tripStartInProgress
    ) {

        return;

    }


    const preference =
        value(
            "user_preferences"
        );


    if (!preference) {

        setMessage(
            "plannerError",
            "Please describe what you want from your trip.",
            true
        );

        return;

    }


    let basic =
        basicTripData;


    if (!basic) {

        basic =
            saveBasicInformation();

    }


    if (!basic) {

        setMessage(
            "plannerError",
            "Please complete the basic trip information first.",
            true
        );

        return;

    }


    tripStartInProgress =
        true;


    const button =
        document.getElementById(
            "startTripButton"
        );


    if (button) {

        button.disabled =
            true;

        button.textContent =
            "PLANNING...";

    }


    setMessage(
        "plannerError",
        "",
        false
    );


    setMessage(
        "plannerLoading",
        "Wanderlust is understanding your preferences, researching destinations, comparing sources, and preparing your three options...",
        true
    );


    openTripChat();


    chatSetTyping(
        true
    );


    addUserChatMessage(
        preference
    );


    try {

        const requestText =
            buildPlannerRequest(
                preference
            );


        currentTrip =
            await API.startTrip(
                requestText
            );


        if (
            !currentTrip ||
            typeof currentTrip !==
                "object"
        ) {

            throw new Error(
                "The backend returned no usable trip result."
            );

        }


        currentCandidates =
            getCandidates(
                currentTrip
            );


        if (
            currentCandidates.length !==
                3
        ) {

            throw new Error(
                "The backend did not return exactly three destination options."
            );

        }


        selectedCandidate =
            null;


        localStorage.setItem(
            STORAGE_KEYS.lastTrip,
            JSON.stringify(
                currentTrip
            )
        );


        renderTripResults(
            currentTrip
        );


        renderChatRecommendations(
            currentTrip
        );


        updateBudgetUI();


        const resultsSection =
            document.getElementById(
                "resultsSection"
            );


        if (resultsSection) {

            resultsSection.style.display =
                "block";

        }


        chatSetTyping(
            false
        );


        scrollToResultsIfNeeded();

    } catch (error) {

        console.error(
            "START TRIP ERROR:",
            error
        );


        chatSetTyping(
            false
        );


        addAssistantChatMessage(
            "I couldn't complete the trip search.\n\n" +
            (
                error.message ||
                "Unknown backend error."
            )
        );


        setMessage(
            "plannerError",
            error.message ||
                "Unable to start travel planning.",
            true
        );

    } finally {

        tripStartInProgress =
            false;


        chatSetTyping(
            false
        );


        if (button) {

            button.disabled =
                false;

            button.textContent =
                "FIND TRIPS →";

        }


        setMessage(
            "plannerLoading",
            "",
            false
        );

    }

}


/* ============================================================
   DESTINATION DETECTION
   ============================================================ */

function looksLikeDestination(item) {

    if (
        !item ||
        typeof item !== "object" ||
        Array.isArray(item)
    ) {

        return false;

    }


    return Boolean(

        item.destination ||

        item.name ||

        item.city ||

        item.title

    );

}


/* ============================================================
   FIND DESTINATION ARRAY
   ============================================================ */

function findDestinationArray(
    valueToInspect,
    depth = 0
) {

    if (
        depth > 8 ||
        valueToInspect === null ||
        valueToInspect === undefined
    ) {

        return null;

    }


    if (
        Array.isArray(
            valueToInspect
        )
    ) {

        if (
            valueToInspect.length === 3 &&
            valueToInspect.every(
                looksLikeDestination
            )
        ) {

            return valueToInspect;

        }


        for (
            const item
            of valueToInspect
        ) {

            const found =
                findDestinationArray(
                    item,
                    depth + 1
                );


            if (found) {

                return found;

            }

        }


        return null;

    }


    if (
        typeof valueToInspect !==
            "object"
    ) {

        return null;

    }


    const priorityKeys = [

        "destinations",

        "travel_options",

        "recommendations",

        "candidates",

        "options",

        "results",

        "travel_result",

        "research_result",

        "final_result",

        "structured_result",

        "data"

    ];


    for (
        const key
        of priorityKeys
    ) {

        if (
            !(key in valueToInspect)
        ) {

            continue;

        }


        const found =
            findDestinationArray(
                valueToInspect[key],
                depth + 1
            );


        if (found) {

            return found;

        }

    }


    for (
        const [
            key,
            child
        ]
        of Object.entries(
            valueToInspect
        )
    ) {

        if (
            priorityKeys.includes(
                key
            )
        ) {

            continue;

        }


        const found =
            findDestinationArray(
                child,
                depth + 1
            );


        if (found) {

            return found;

        }

    }


    return null;

}


/* ============================================================
   GET CANDIDATES
   ============================================================ */

function getCandidates(
    trip
) {

    const found =
        findDestinationArray(
            trip
        );


    return Array.isArray(found)
        ? found.slice(0, 3)
        : [];

}


/* ============================================================
   DESTINATION NAME
   ============================================================ */

function getDestinationName(
    candidate
) {

    return firstNonEmpty(

        candidate?.destination,

        candidate?.name,

        candidate?.city,

        candidate?.title,

        "Unknown destination"

    );

}


/* ============================================================
   COUNTRY
   ============================================================ */

function getDestinationCountry(
    candidate
) {

    return firstNonEmpty(

        candidate?.country,

        candidate?.destination_country,

        candidate?.location?.country,

        ""

    );

}


/* ============================================================
   BASIC INFORMATION
   ============================================================ */

function getBasicInfo(
    candidate
) {

    return firstNonEmpty(

        candidate?.basic_info,

        candidate?.description,

        candidate?.summary,

        candidate?.basic_information,

        candidate?.overview,

        candidate?.reason,

        "No destination description was provided."

    );

}


/* ============================================================
   ATTRACTIONS
   ============================================================ */

function getAttractions(
    candidate
) {

    const possible =

        candidate?.major_attractions ||

        candidate?.attractions ||

        candidate?.points_of_interest;


    if (
        Array.isArray(
            possible
        )
    ) {

        return possible
            .filter(Boolean)
            .slice(0, 6);

    }


    return [];

}


/* ============================================================
   IMAGES
   ============================================================ */

function getImages(
    candidate
) {

    const output = [];

    const seen =
        new Set();


    function addImage(
        valueToAdd
    ) {

        if (
            typeof valueToAdd !==
                "string"
        ) {

            return;

        }


        const url =
            valueToAdd.trim();


        if (
            !url ||
            seen.has(url)
        ) {

            return;

        }


        seen.add(url);

        output.push(url);

    }


    const imageFields = [

        candidate?.images,

        candidate?.image_urls,

        candidate?.photos

    ];


    imageFields.forEach(
        field => {

            if (
                Array.isArray(field)
            ) {

                field.forEach(
                    item => {

                        if (
                            typeof item ===
                                "string"
                        ) {

                            addImage(
                                item
                            );

                        } else if (
                            item &&
                            typeof item ===
                                "object"
                        ) {

                            addImage(
                                item.url
                            );

                            addImage(
                                item.image_url
                            );

                            addImage(
                                item.src
                            );

                        }

                    }
                );

            }

        }
    );


    addImage(
        candidate?.image_url
    );


    addImage(
        candidate?.image?.url
    );


    addImage(
        candidate?.image?.image_url
    );


    addImage(
        candidate?.image?.src
    );


    return output.slice(
        0,
        6
    );

}


/* ============================================================
   COORDINATES
   ============================================================ */

function getCoordinates(
    candidate
) {

    const sources = [

        candidate?.map_coordinates,

        candidate?.coordinates,

        candidate?.location?.coordinates,

        candidate?.map?.coordinates

    ];


    for (
        const source
        of sources
    ) {

        if (!source) {
            continue;
        }


        if (
            typeof source ===
                "object" &&
            !Array.isArray(source)
        ) {

            const latitude =
                Number(
                    firstNonEmpty(
                        source.latitude,
                        source.lat
                    )
                );


            const longitude =
                Number(
                    firstNonEmpty(
                        source.longitude,
                        source.lon,
                        source.lng
                    )
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

                    latitude:
                        latitude,

                    longitude:
                        longitude

                };

            }

        }


        if (
            Array.isArray(source) &&
            source.length >= 2
        ) {

            const first =
                Number(
                    source[0]
                );


            const second =
                Number(
                    source[1]
                );


            if (
                Number.isFinite(
                    first
                ) &&
                Number.isFinite(
                    second
                )
            ) {

                return {

                    latitude:
                        first,

                    longitude:
                        second

                };

            }

        }

    }


    return null;

}


/* ============================================================
   RESEARCH OBJECT
   ============================================================ */

function getResearchObject(
    candidate
) {

    return (

        candidate?.verified_result ||

        candidate?.worker_result ||

        candidate?.research_result ||

        candidate?.research ||

        candidate

    );

}


/* ============================================================
   COST
   ============================================================ */

function getCost(
    candidate,
    fieldName
) {

    const objects = [

        candidate,

        candidate?.verified_result,

        candidate?.worker_result,

        candidate?.research_result,

        candidate?.research,

        getResearchObject(
            candidate
        )

    ];


    for (
        const object
        of objects
    ) {

        if (
            !object ||
            typeof object !==
                "object"
        ) {

            continue;

        }


        const number =
            Number(
                object[fieldName]
            );


        if (
            Number.isFinite(
                number
            ) &&
            number >= 0
        ) {

            return number;

        }

    }


    return null;

}


/* ============================================================
   ESTIMATED COST
   ============================================================

   Worker cost fields mean:

       traveling_cost
           one-time travel cost

       residence_cost
           accommodation cost for trip

       average_food_cost
           food cost per day

       daily_average_travel_cost
           local transportation per day

============================================================ */

function getEstimatedWorkerCost(
    candidate
) {

    const duration =
        Number(
            basicTripData?.duration_days ||
            candidate?.duration_days ||
            0
        );


    const traveling =
        getCost(
            candidate,
            "traveling_cost"
        );


    const residence =
        getCost(
            candidate,
            "residence_cost"
        );


    const food =
        getCost(
            candidate,
            "average_food_cost"
        );


    const localTravel =
        getCost(
            candidate,
            "daily_average_travel_cost"
        );


    if (
        traveling === null &&
        residence === null &&
        food === null &&
        localTravel === null
    ) {

        return null;

    }


    return (

        (traveling || 0) +

        (residence || 0) +

        (
            (food || 0) *
            duration
        ) +

        (
            (localTravel || 0) *
            duration
        )

    );

}


/* ============================================================
   CHAT
   ============================================================ */

function getChatMessagesElement() {

    return document.getElementById(
        "tripChatMessages"
    );

}


/* ============================================================
   ADD CHAT MESSAGE
   ============================================================ */

function addChatMessage(
    text,
    type = "assistant"
) {

    const container =
        getChatMessagesElement();


    if (!container) {
        return;
    }


    const row =
        document.createElement(
            "div"
        );


    row.className =
        `trip-chat-row ${type}`;


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
        "trip-chat-bubble";


    bubble.textContent =
        String(
            text || ""
        );


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

}


/* ============================================================
   CHAT USER
   ============================================================ */

function addUserChatMessage(
    text
) {

    addChatMessage(
        text,
        "user"
    );

}


/* ============================================================
   CHAT ASSISTANT
   ============================================================ */

function addAssistantChatMessage(
    text
) {

    addChatMessage(
        text,
        "assistant"
    );

}


/* ============================================================
   CHAT TYPING
   ============================================================ */

function chatSetTyping(
    show
) {

    const typing =
        document.getElementById(
            "tripChatTyping"
        );


    if (!typing) {
        return;
    }


    typing.classList.toggle(
        "show",
        Boolean(show)
    );


    typing.setAttribute(
        "aria-hidden",
        show
            ? "false"
            : "true"
    );

}


/* ============================================================
   OPEN CHAT
   ============================================================ */

function openTripChat() {

    const scene =
        document.getElementById(
            "tripChatScene"
        );


    if (!scene) {
        return;
    }


    scene.classList.add(
        "open"
    );


    const plannerPage = document.getElementById("page-planner");

    plannerPage?.classList.add("planner-chat-active");


    if (!chatStarted) {

        chatStarted =
            true;


        addAssistantChatMessage(
            "Tell me the experience you want and Wanderlust will research three destination options for you."
        );

    }

}


/* ============================================================
   RENDER CHAT RECOMMENDATIONS
   ============================================================ */

function renderChatRecommendations(
    trip
) {

    const candidates =
        getCandidates(
            trip
        );


    if (
        candidates.length !==
            3
    ) {

        return;

    }


    const lines = [

        "I've finished researching your three destination options:",

        ""

    ];


    candidates.forEach(
        (
            candidate,
            index
        ) => {

            const name =
                getDestinationName(
                    candidate
                );


            const country =
                getDestinationCountry(
                    candidate
                );


            lines.push(
                `${index + 1}. ${name}${
                    country
                        ? `, ${country}`
                        : ""
                }`
            );

        }
    );


    lines.push(
        "",
        "Choose one of the three options below to inspect it in more detail."
    );


    addAssistantChatMessage(
        lines.join("\n")
    );

}


/* ============================================================
   RENDER RESULTS
   ============================================================ */

function renderTripResults(
    trip
) {

    const grid =
        document.getElementById(
            "resultGrid"
        );


    if (!grid) {
        return;
    }


    const candidates =
        getCandidates(
            trip
        );


    currentCandidates =
        candidates;


    grid.innerHTML =
        "";


    if (
        candidates.length !==
            3
    ) {

        grid.innerHTML = `

            <div
                class="panel"
                style="grid-column:1/-1;"
            >

                <strong>
                    Unable to display the recommendations.
                </strong>

                <p>
                    The backend did not return exactly three destinations.
                </p>

            </div>

        `;


        return;

    }


    candidates.forEach(
        (
            candidate,
            index
        ) => {

            const card =
                document.createElement(
                    "article"
                );


            card.className =
                "result-card";


            const name =
                getDestinationName(
                    candidate
                );


            const country =
                getDestinationCountry(
                    candidate
                );


            const description =
                getBasicInfo(
                    candidate
                );


            const images =
                getImages(
                    candidate
                );


            const attractions =
                getAttractions(
                    candidate
                );


            const coordinates =
                getCoordinates(
                    candidate
                );


            const estimatedCost =
                getEstimatedWorkerCost(
                    candidate
                );


            const image =
                images[0] ||
                "";


            card.innerHTML = `

                ${
                    image
                        ? `
                            <img
                                class="result-image"
                                src="${escapeHtml(image)}"
                                alt="${escapeHtml(name)}"
                                loading="lazy"
                                onerror="this.style.display='none';"
                            >
                          `
                        : ""
                }

                <div
                    class="result-card-body"
                >

                    <span
                        class="result-number"
                    >
                        ${index + 1}
                    </span>


                    <h3>
                        ${escapeHtml(name)}
                    </h3>


                    ${
                        country
                            ? `
                                <div
                                    class="result-country"
                                >
                                    ${escapeHtml(country)}
                                </div>
                              `
                            : ""
                    }


                    <p
                        class="result-description"
                    >
                        ${escapeHtml(description)}
                    </p>


                    ${
                        attractions.length
                            ? `
                                <div
                                    class="detail-box"
                                    style="margin-top:12px;"
                                >

                                    <h4>
                                        Major attractions
                                    </h4>

                                    <p>
                                        ${
                                            attractions
                                                .map(
                                                    item =>
                                                        `• ${escapeHtml(item)}`
                                                )
                                                .join(
                                                    "<br>"
                                                )
                                        }
                                    </p>

                                </div>
                              `
                            : ""
                    }


                    <div
                        class="option-meta"
                    >

                        <div
                            class="meta-box"
                        >

                            <small>
                                Research estimate
                            </small>

                            <strong>
                                ${
                                    estimatedCost !==
                                    null
                                        ? escapeHtml(
                                            formatMoney(
                                                estimatedCost
                                            )
                                          )
                                        : "Not available"
                                }
                            </strong>

                        </div>


                        <div
                            class="meta-box"
                        >

                            <small>
                                Travelers
                            </small>

                            <strong>
                                ${
                                    basicTripData?.travelers ||
                                    "—"
                                }
                            </strong>

                        </div>


                        <div
                            class="meta-box"
                        >

                            <small>
                                Map
                            </small>

                            <strong>
                                ${
                                    coordinates
                                        ? "Available"
                                        : "Not available"
                                }
                            </strong>

                        </div>

                    </div>


                    <div
                        class="form-actions"
                    >

                        <button
                            class="btn btn-light details-button"
                            type="button"
                        >
                            VIEW DETAILS
                        </button>


                        <button
                            class="btn btn-primary select-button"
                            type="button"
                        >
                            SELECT TRIP
                        </button>

                    </div>

                </div>

            `;


            const detailsButton =
                card.querySelector(
                    ".details-button"
                );


            const selectButton =
                card.querySelector(
                    ".select-button"
                );


            detailsButton?.addEventListener(
                "click",
                () => {

                    showDestination(
                        candidate
                    );

                }
            );


            selectButton?.addEventListener(
                "click",
                () => {

                    selectTrip(
                        index
                    );

                }
            );


            grid.appendChild(
                card
            );

        }
    );


    renderHomeDestinations(
        candidates
    );

}


/* ============================================================
   HOME DESTINATIONS
   ============================================================ */

function renderHomeDestinations(
    candidates
) {

    const container =
        document.getElementById(
            "homeDestinations"
        );


    if (!container) {
        return;
    }


    if (
        !Array.isArray(candidates) ||
        candidates.length === 0
    ) {

        container.innerHTML = `

            <div
                class="panel"
                style="grid-column:1/-1;"
            >

                <strong>
                    No destinations yet.
                </strong>

                <p>
                    Start planning a trip to generate destination recommendations.
                </p>

            </div>

        `;


        return;

    }


    const selected =
        candidates.slice(
            0,
            3
        );


    container.innerHTML =
        selected
            .map(
                (
                    candidate,
                    index
                ) => {

                    const name =
                        getDestinationName(
                            candidate
                        );


                    const country =
                        getDestinationCountry(
                            candidate
                        );


                    const image =
                        getImages(
                            candidate
                        )[0] ||
                        "";


                    return `

                        <article
                            class="destination-card ${
                                index === 0
                                    ? "large"
                                    : ""
                            }"
                            style="
                                background-image:
                                linear-gradient(
                                    rgba(15,23,42,.15),
                                    rgba(15,23,42,.55)
                                ),
                                url('${escapeHtml(image)}');
                                background-size:cover;
                                background-position:center;
                                cursor:pointer;
                            "
                            data-home-index="${index}"
                        >

                            <div
                                style="
                                    height:100%;
                                    display:flex;
                                    flex-direction:column;
                                    justify-content:flex-end;
                                    padding:20px;
                                    color:white;
                                "
                            >

                                <strong
                                    style="font-size:20px;"
                                >
                                    ${escapeHtml(name)}
                                </strong>

                                <span
                                    style="
                                        margin-top:4px;
                                        font-size:12px;
                                    "
                                >
                                    ${escapeHtml(country)}
                                </span>

                            </div>

                        </article>

                    `;

                }
            )
            .join("");


    container
        .querySelectorAll(
            ".destination-card"
        )
        .forEach(
            (
                card,
                index
            ) => {

                card.addEventListener(
                    "click",
                    () => {

                        showDestination(
                            selected[index]
                        );

                    }
                );

            }
        );

}


/* ============================================================
   DESTINATION MODAL
   ============================================================ */

function showDestination(
    candidate
) {

    const modal =
        document.getElementById(
            "destinationModal"
        );


    if (!modal) {
        return;
    }


    const title =
        document.getElementById(
            "modalTitle"
        );


    const country =
        document.getElementById(
            "modalCountry"
        );


    const reason =
        document.getElementById(
            "modalReason"
        );


    const description =
        document.getElementById(
            "modalDescription"
        );


    const map =
        document.getElementById(
            "modalMap"
        );


    const name =
        getDestinationName(
            candidate
        );


    const countryName =
        getDestinationCountry(
            candidate
        );


    const info =
        getBasicInfo(
            candidate
        );


    const attractions =
        getAttractions(
            candidate
        );


    const coordinates =
        getCoordinates(
            candidate
        );


    const images =
        getImages(
            candidate
        );


    const estimatedCost =
        getEstimatedWorkerCost(
            candidate
        );


    if (title) {

        title.textContent =
            name;

    }


    if (country) {

        country.textContent =
            countryName;

    }


    if (reason) {

        reason.textContent =
            "";

    }


    if (description) {

        description.innerHTML = `

            <p>
                ${escapeHtml(info)}
            </p>


            ${
                estimatedCost !== null
                    ? `
                        <h3>
                            Research cost estimate
                        </h3>

                        <p>
                            ${escapeHtml(
                                formatMoney(
                                    estimatedCost
                                )
                            )}
                        </p>
                      `
                    : ""
            }


            ${
                attractions.length
                    ? `
                        <h3>
                            Major attractions
                        </h3>

                        <ul>

                            ${
                                attractions
                                    .map(
                                        item =>
                                            `<li>${escapeHtml(item)}</li>`
                                    )
                                    .join("")
                            }

                        </ul>
                      `
                    : ""
            }


            ${
                images.length > 1
                    ? `
                        <div
                            style="
                                margin-top:18px;
                            "
                        >

                            <strong>
                                Destination images
                            </strong>

                            <div
                                style="
                                    display:grid;
                                    grid-template-columns:repeat(2,1fr);
                                    gap:10px;
                                    margin-top:10px;
                                "
                            >

                                ${
                                    images
                                        .slice(
                                            1,
                                            5
                                        )
                                        .map(
                                            image => `

                                                <img
                                                    src="${escapeHtml(image)}"
                                                    alt="${escapeHtml(name)}"
                                                    style="
                                                        width:100%;
                                                        height:150px;
                                                        object-fit:cover;
                                                        border-radius:10px;
                                                    "
                                                    loading="lazy"
                                                >

                                            `
                                        )
                                        .join("")
                                }

                            </div>

                        </div>
                      `
                    : ""
            }

        `;

    }


    if (map) {

        if (coordinates) {

            map.innerHTML = `

                <div
                    class="map-item"
                >

                    <strong>
                        Map coordinates
                    </strong>

                    <br>

                    Latitude:
                    ${escapeHtml(
                        formatNumber(
                            coordinates.latitude
                        )
                    )}

                    <br>

                    Longitude:
                    ${escapeHtml(
                        formatNumber(
                            coordinates.longitude
                        )
                    )}

                </div>

            `;

        } else {

            map.innerHTML = `

                <div
                    class="map-item"
                >

                    Map coordinates were not included in the final result.

                </div>

            `;

        }

    }


    modal.classList.add(
        "open"
    );


    modal.setAttribute(
        "aria-hidden",
        "false"
    );

}


/* ============================================================
   CLOSE MODAL
   ============================================================ */

function closeModal() {

    const modal =
        document.getElementById(
            "destinationModal"
        );


    if (!modal) {
        return;
    }


    modal.classList.remove(
        "open"
    );


    modal.setAttribute(
        "aria-hidden",
        "true"
    );

}


/* ============================================================
   SELECT DESTINATION
   ============================================================ */

function selectTrip(
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


    renderSelectedTrip(
        candidate,
        index
    );


    updateBudgetUI();


    const panel =
        document.getElementById(
            "selectionPanel"
        );


    if (panel) {

        panel.style.display =
            "block";


        panel.scrollIntoView({
            behavior:
                "smooth",
            block:
                "start"
        });

    }

}


/* ============================================================
   SELECTED TRIP
   ============================================================ */

function renderSelectedTrip(
    candidate,
    index = 0
) {

    const nameElement =
        document.getElementById(
            "selectedTripName"
        );


    const content =
        document.getElementById(
            "selectedTripContent"
        );


    const name =
        getDestinationName(
            candidate
        );


    const country =
        getDestinationCountry(
            candidate
        );


    if (nameElement) {

        nameElement.textContent =

            `${index + 1}. ${name}` +

            (
                country
                    ? `, ${country}`
                    : ""
            );

    }


    if (!content) {
        return;
    }


    const cost =
        getEstimatedWorkerCost(
            candidate
        );


    const coordinates =
        getCoordinates(
            candidate
        );


    const attractions =
        getAttractions(
            candidate
        );


    content.innerHTML = `

        <div
            class="destination-detail-grid"
        >

            <div
                class="detail-box"
            >

                <h4>
                    Destination information
                </h4>

                <p>
                    ${escapeHtml(
                        getBasicInfo(
                            candidate
                        )
                    )}
                </p>

            </div>


            <div
                class="detail-box"
            >

                <h4>
                    Research estimate
                </h4>

                <p>

                    ${
                        cost !== null
                            ? escapeHtml(
                                formatMoney(
                                    cost
                                )
                              )
                            : "Cost details were not included in the final response."
                    }

                </p>

            </div>

        </div>


        ${
            attractions.length
                ? `

                    <div
                        class="map-list"
                    >

                        <div
                            class="map-item"
                        >

                            <strong>
                                Major attractions
                            </strong>

                            <br><br>

                            ${
                                attractions
                                    .map(
                                        item =>
                                            `• ${escapeHtml(item)}`
                                    )
                                    .join(
                                        "<br>"
                                    )
                            }

                        </div>

                    </div>

                  `
                : ""
        }


        ${
            coordinates
                ? `

                    <div
                        class="map-list"
                    >

                        <div
                            class="map-item"
                        >

                            <strong>
                                Coordinates
                            </strong>

                            <br>

                            Latitude:
                            ${escapeHtml(
                                formatNumber(
                                    coordinates.latitude
                                )
                            )}

                            <br>

                            Longitude:
                            ${escapeHtml(
                                formatNumber(
                                    coordinates.longitude
                                )
                            )}

                        </div>

                    </div>

                  `
                : ""
        }

    `;

}


/* ============================================================
   CLEAR SELECTION
   ============================================================ */

function clearSelection() {

    selectedCandidate =
        null;


    const panel =
        document.getElementById(
            "selectionPanel"
        );


    if (panel) {

        panel.style.display =
            "none";

    }


    updateBudgetUI();

}


/* ============================================================
   CONFIRM TRIP
   ============================================================

   IMPORTANT:

   The current backend does not expose a booking endpoint.

   Therefore "Confirm Trip" only confirms the user's frontend
   selection. It does NOT book anything.

============================================================ */

function confirmTrip() {

    if (!selectedCandidate) {

        alert(
            "Please select a destination first."
        );

        return;

    }


    const name =
        getDestinationName(
            selectedCandidate
        );


    addAssistantChatMessage(

        `You selected ${name}. Your current Wanderlust backend does not perform bookings, so this selection is only saved in the current planning session.`

    );


    const button =
        document.getElementById(
            "confirmTripButton"
        );


    if (button) {

        button.textContent =
            "TRIP SELECTED ✓";


        button.disabled =
            true;

    }

}


/* ============================================================
   BUDGET PAGE
   ============================================================ */

function updateBudgetUI() {

    const empty =
        document.getElementById(
            "budgetEmpty"
        );


    const content =
        document.getElementById(
            "budgetContent"
        );


    if (
        !empty ||
        !content
    ) {

        return;

    }


    if (
        !basicTripData &&
        !currentTrip
    ) {

        empty.style.display =
            "block";


        content.style.display =
            "none";


        return;

    }


    empty.style.display =
        "none";


    content.style.display =
        "block";


    const totalBudget =
        Number(
            basicTripData?.budget
        );


    const estimated =
        selectedCandidate
            ? getEstimatedWorkerCost(
                selectedCandidate
              )
            : null;


    const totalElement =
        document.getElementById(
            "budgetTotal"
        );


    const spentElement =
        document.getElementById(
            "budgetSpent"
        );


    const remainingElement =
        document.getElementById(
            "budgetRemaining"
        );


    const estimatedElement =
        document.getElementById(
            "budgetEstimated"
        );


    const progress =
        document.getElementById(
            "budgetProgress"
        );


    const summary =
        document.getElementById(
            "budgetSummary"
        );


    const notes =
        document.getElementById(
            "budgetNotes"
        );


    if (totalElement) {

        totalElement.textContent =

            Number.isFinite(
                totalBudget
            )
                ? formatMoney(
                    totalBudget
                  )
                : "Not available";

    }


    if (spentElement) {

        spentElement.textContent =
            formatMoney(0);

    }


    if (estimatedElement) {

        estimatedElement.textContent =

            estimated !== null
                ? formatMoney(
                    estimated
                  )
                : "Select a destination";

    }


    if (remainingElement) {

        if (
            Number.isFinite(
                totalBudget
            ) &&
            estimated !== null
        ) {

            remainingElement.textContent =
                formatMoney(
                    totalBudget -
                    estimated
                );

        } else {

            remainingElement.textContent =
                "—";

        }

    }


    if (progress) {

        if (
            Number.isFinite(
                totalBudget
            ) &&
            totalBudget > 0 &&
            estimated !== null
        ) {

            const percentage =
                (
                    estimated /
                    totalBudget
                ) * 100;


            progress.style.width =

                `${Math.min(
                    100,
                    Math.max(
                        0,
                        percentage
                    )
                )}%`;

        } else {

            progress.style.width =
                "0%";

        }

    }


    if (summary) {

        if (
            estimated !== null &&
            Number.isFinite(
                totalBudget
            ) &&
            totalBudget > 0
        ) {

            const percentage =
                (
                    estimated /
                    totalBudget
                ) * 100;


            summary.textContent =

                `${percentage.toFixed(1)}% of your budget is represented by the current research estimate.`;

        } else {

            summary.textContent =

                "Select a destination to view the available research cost estimate.";

        }

    }


    if (notes) {

        notes.textContent =

            "These are research estimates only. Prices can change and no booking or payment has been made.";

    }

}


/* ============================================================
   RANDOM EXPOSURE
   ============================================================ */

function loadRandomDestination() {

    const container =
        document.getElementById(
            "randomDestinations"
        );


    if (!container) {
        return;
    }


    if (
        currentCandidates.length ===
            0
    ) {

        container.innerHTML = `

            <div
                class="panel"
                style="grid-column:1/-1;"
            >

                <strong>
                    No researched destinations yet.
                </strong>

                <p
                    style="
                        color:var(--muted);
                        font-size:13px;
                    "
                >
                    Start a trip first to generate destinations.
                </p>

                <button
                    class="btn btn-primary"
                    type="button"
                    onclick="showPage('basic')"
                >
                    START PLANNING
                </button>

            </div>

        `;


        return;

    }


    const shuffled =
        [
            ...currentCandidates
        ]
            .sort(
                () =>
                    Math.random() -
                    0.5
            );


    container.innerHTML =

        shuffled
            .map(
                (
                    candidate,
                    index
                ) => {

                    const name =
                        getDestinationName(
                            candidate
                        );


                    const country =
                        getDestinationCountry(
                            candidate
                        );


                    const image =
                        getImages(
                            candidate
                        )[0] ||
                        "";


                    return `

                        <article
                            class="random-card"
                            data-random-index="${index}"
                        >

                            ${
                                image
                                    ? `

                                        <img
                                            class="random-card-image"
                                            src="${escapeHtml(image)}"
                                            alt="${escapeHtml(name)}"
                                            loading="lazy"
                                        >

                                      `
                                    : ""
                            }


                            <div
                                class="random-card-content"
                            >

                                <h3>
                                    ${escapeHtml(name)}
                                </h3>


                                <div
                                    class="random-card-country"
                                >
                                    ${escapeHtml(country)}
                                </div>


                                <p
                                    class="random-card-description"
                                >
                                    ${escapeHtml(
                                        getBasicInfo(
                                            candidate
                                        )
                                    )}
                                </p>


                                <button
                                    class="btn btn-light random-card-button"
                                    type="button"
                                >
                                    VIEW DETAILS
                                </button>

                            </div>

                        </article>

                    `;

                }
            )
            .join("");


    container
        .querySelectorAll(
            ".random-card"
        )
        .forEach(
            (
                card,
                index
            ) => {

                card.addEventListener(
                    "click",
                    () => {

                        showDestination(
                            shuffled[index]
                        );

                    }
                );

            }
        );

}


/* ============================================================
   LOCAL SEARCH
   ============================================================ */

function renderLocalSearchResults(
    query = ""
) {

    const container =
        document.getElementById(
            "searchResults"
        );


    if (!container) {
        return;
    }


    const cleanQuery =
        String(
            query || ""
        )
            .trim()
            .toLowerCase();


    const matches =
        currentCandidates.filter(
            candidate => {

                if (!cleanQuery) {
                    return true;
                }


                const haystack = [

                    getDestinationName(
                        candidate
                    ),

                    getDestinationCountry(
                        candidate
                    ),

                    getBasicInfo(
                        candidate
                    ),

                    ...getAttractions(
                        candidate
                    )

                ]
                    .join(" ")
                    .toLowerCase();


                return haystack.includes(
                    cleanQuery
                );

            }
        );


    if (
        matches.length === 0
    ) {

        container.innerHTML = `

            <div
                class="panel"
                style="grid-column:1/-1;"
            >

                <strong>
                    No matching destinations found.
                </strong>

                <p
                    style="
                        color:var(--muted);
                        font-size:13px;
                    "
                >
                    Search the destinations returned by your current planning session.
                </p>

            </div>

        `;


        return;

    }


    container.innerHTML =

        matches
            .map(
                (
                    candidate
                ) => {

                    const name =
                        getDestinationName(
                            candidate
                        );


                    const country =
                        getDestinationCountry(
                            candidate
                        );


                    const image =
                        getImages(
                            candidate
                        )[0] ||
                        "";


                    return `

                        <article
                            class="search-result-card"
                        >

                            ${
                                image
                                    ? `

                                        <img
                                            src="${escapeHtml(image)}"
                                            alt="${escapeHtml(name)}"
                                            loading="lazy"
                                        >

                                      `
                                    : ""
                            }


                            <div
                                class="search-result-body"
                            >

                                <h3>
                                    ${escapeHtml(name)}
                                </h3>


                                <div
                                    class="result-country"
                                >
                                    ${escapeHtml(country)}
                                </div>


                                <p>
                                    ${escapeHtml(
                                        getBasicInfo(
                                            candidate
                                        )
                                    )}
                                </p>


                                <button
                                    class="btn btn-light"
                                    type="button"
                                >
                                    VIEW DETAILS
                                </button>

                            </div>

                        </article>

                    `;

                }
            )
            .join("");


    container
        .querySelectorAll(
            ".search-result-card"
        )
        .forEach(
            (
                card,
                index
            ) => {

                const button =
                    card.querySelector(
                        "button"
                    );


                button?.addEventListener(
                    "click",
                    () => {

                        showDestination(
                            matches[index]
                        );

                    }
                );

            }
        );

}


/* ============================================================
   SEARCH INITIALIZATION
   ============================================================ */

function initializeSearch() {

    const button =
        document.getElementById(
            "destinationSearchButton"
        );


    const input =
        document.getElementById(
            "destinationSearchInput"
        );


    const loading =
        document.getElementById(
            "destinationSearchLoading"
        );


    const error =
        document.getElementById(
            "destinationSearchError"
        );


    function performSearch() {

        const query =
            input?.value || "";


        if (loading) {

            loading.style.display =
                "block";

        }


        if (error) {

            error.style.display =
                "none";

        }


        try {

            renderLocalSearchResults(
                query
            );

        } catch (searchError) {

            console.error(
                searchError
            );


            setMessage(
                "destinationSearchError",
                "Unable to search the current destinations.",
                true
            );

        } finally {

            if (loading) {

                loading.style.display =
                    "none";

            }

        }

    }


    button?.addEventListener(
        "click",
        performSearch
    );


    input?.addEventListener(
        "keydown",
        event => {

            if (
                event.key ===
                    "Enter"
            ) {

                event.preventDefault();

                performSearch();

            }

        }
    );

}


/* ============================================================
   HEADER SEARCH
   ============================================================ */

function initializeHeaderSearch() {

    const search =
        document.querySelector(
            ".header .search"
        );


    if (!search) {
        return;
    }


    search.addEventListener(
        "input",
        event => {

            const query =
                String(
                    event.target.value ||
                    ""
                ).trim();


            if (query) {

                showPage(
                    "search"
                );

            }


            const destinationSearch =
                document.getElementById(
                    "destinationSearchInput"
                );


            if (
                destinationSearch
            ) {

                destinationSearch.value =
                    query;

            }


            renderLocalSearchResults(
                query
            );

        }
    );

}


/* ============================================================
   CHAT EDIT REQUEST
   ============================================================

   Current backend has no /api/trip/update endpoint.

   Therefore an edit request starts another complete planning
   request using the same practical trip information.

============================================================ */

async function submitChatChange(
    message
) {

    const clean =
        String(
            message || ""
        ).trim();


    if (
        !clean ||
        tripChatProcessing ||
        tripStartInProgress
    ) {

        return;

    }


    tripChatProcessing =
        true;


    chatSetTyping(
        true
    );


    addUserChatMessage(
        clean
    );


    try {

        const requestText =
            buildPlannerRequest(
                clean
            );


        currentTrip =
            await API.startTrip(
                requestText
            );


        currentCandidates =
            getCandidates(
                currentTrip
            );


        if (
            currentCandidates.length !==
                3
        ) {

            throw new Error(
                "The backend did not return exactly three destination options."
            );

        }


        selectedCandidate =
            null;


        localStorage.setItem(
            STORAGE_KEYS.lastTrip,
            JSON.stringify(
                currentTrip
            )
        );


        renderTripResults(
            currentTrip
        );


        renderChatRecommendations(
            currentTrip
        );


        updateBudgetUI();


        const resultsSection =
            document.getElementById(
                "resultsSection"
            );


        if (resultsSection) {

            resultsSection.style.display =
                "block";

        }

    } catch (error) {

        console.error(
            "CHAT CHANGE ERROR:",
            error
        );


        addAssistantChatMessage(

            "I couldn't rebuild the recommendations.\n\n" +
            (
                error.message ||
                "Unknown backend error."
            )

        );

    } finally {

        tripChatProcessing =
            false;


        chatSetTyping(
            false
        );

    }

}


/* ============================================================
   CHAT INITIALIZATION
   ============================================================ */

function initializeTripChat() {

    const chatForm =
        document.getElementById(
            "tripChatForm"
        );


    const chatInput =
        document.getElementById(
            "tripChatInput"
        );


    const backButton =
        document.getElementById(
            "tripChatBackButton"
        );


    const attachButton =
        document.getElementById(
            "tripChatAttachButton"
        );


    const emojiButton =
        document.getElementById(
            "tripChatEmojiButton"
        );


    chatForm?.addEventListener(
        "submit",
        async event => {

            event.preventDefault();


            const message =
                chatInput?.value ||
                "";


            if (chatInput) {

                chatInput.value =
                    "";

            }


            await submitChatChange(
                message
            );

        }
    );


    backButton?.addEventListener(
        "click",
        () => {

            const panel =
                document.getElementById(
                    "preferencePanel"
                );


            if (panel) {

                panel.style.display =
                    "block";

            }


            const scene =
                document.getElementById(
                    "tripChatScene"
                );


            if (scene) {

                scene.classList.remove(
                    "open"
                );

            }


            document.getElementById("page-planner")?.classList.remove("planner-chat-active");


            showPage(
                "planner"
            );

        }
    );


    attachButton?.addEventListener(
        "click",
        () => {

            alert(
                "File attachments are not part of the current Wanderlust backend."
            );

        }
    );


    emojiButton?.addEventListener(
        "click",
        () => {

            if (chatInput) {

                chatInput.value +=
                    " ✈️ ";

                chatInput.focus();

            }

        }
    );

}


/* ============================================================
   CLOSE CHAT
   ============================================================ */

window.wanderlustCloseTripChat =
    function () {

        const scene =
            document.getElementById(
                "tripChatScene"
            );


        if (scene) {

            scene.classList.remove(
                "open"
            );

        }

    };


/* ============================================================
   RESET PLANNER
   ============================================================ */

function resetPlanner() {

    currentTrip =
        null;


    currentCandidates =
        [];


    selectedCandidate =
        null;


    tripStartInProgress =
        false;


    tripChatProcessing =
        false;


    const results =
        document.getElementById(
            "resultsSection"
        );


    const selection =
        document.getElementById(
            "selectionPanel"
        );


    const scene =
        document.getElementById(
            "tripChatScene"
        );


    const messages =
        document.getElementById(
            "tripChatMessages"
        );


    const tripForm =
        document.getElementById(
            "tripForm"
        );


    if (results) {

        results.style.display =
            "none";

    }


    if (selection) {

        selection.style.display =
            "none";

    }


    if (scene) {

        scene.classList.remove(
            "open"
        );

    }


    document.getElementById("page-planner")?.classList.remove("planner-chat-active");


    if (messages) {

        messages.innerHTML =
            "";

    }


    if (tripForm) {

        tripForm.reset();

    }


    chatStarted =
        false;


    const confirmButton =
        document.getElementById(
            "confirmTripButton"
        );


    if (confirmButton) {

        confirmButton.disabled =
            false;


        confirmButton.textContent =
            "CONFIRM TRIP";

    }


    setMessage(
        "plannerError",
        "",
        false
    );


    setMessage(
        "plannerLoading",
        "",
        false
    );


    updateBudgetUI();


    renderHomeDestinations(
        []
    );


    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });

}


/* ============================================================
   SCROLL TO RESULTS
   ============================================================ */

function scrollToResultsIfNeeded() {

    const workspace = document.getElementById("tripChatScene");

    if (!workspace) {
        return;
    }

    setTimeout(() => {
        workspace.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });
    }, 100);

}


/* ============================================================
   RANDOM PAGE
   ============================================================ */

function initializeRandomPage() {

    const button =
        document.getElementById(
            "randomizeButton"
        );


    button?.addEventListener(
        "click",
        loadRandomDestination
    );

}


/* ============================================================
   NAVIGATION
   ============================================================ */

function initializeNavigation() {

    document
        .querySelectorAll(
            ".nav-button"
        )
        .forEach(
            button => {

                button.addEventListener(
                    "click",
                    () => {

                        showPage(
                            button.dataset.page
                        );

                    }
                );

            }
        );

}


/* ============================================================
   MODAL
   ============================================================ */

function initializeModal() {

    const modal =
        document.getElementById(
            "destinationModal"
        );


    const closeButton =
        document.getElementById(
            "modalCloseButton"
        );


    if (!modal) {
        return;
    }


    closeButton?.addEventListener(
        "click",
        closeModal
    );


    modal.addEventListener(
        "click",
        event => {

            if (
                event.target ===
                    modal
            ) {

                closeModal();

            }

        }
    );


    document.addEventListener(
        "keydown",
        event => {

            if (
                event.key ===
                    "Escape"
            ) {

                closeModal();

            }

        }
    );

}


/* ============================================================
   FORM INITIALIZATION
   ============================================================ */

function initializeForms() {

    const basicForm =
        document.getElementById(
            "basicTripForm"
        );


    basicForm?.addEventListener(
        "submit",
        event => {

            event.preventDefault();


            const saved =
                saveBasicInformation();


            if (saved) {

                showPage(
                    "planner"
                );

            }

        }
    );


    const tripForm =
        document.getElementById(
            "tripForm"
        );


    tripForm?.addEventListener(
        "submit",
        event => {

            event.preventDefault();

            startTrip();

        }
    );


    const departure =
        document.getElementById(
            "departure_location"
        );


    departure?.addEventListener(
        "input",
        updateCountryField
    );


    document
        .querySelectorAll(
            'input[name="trip_scope"]'
        )
        .forEach(
            input => {

                input.addEventListener(
                    "change",
                    updateCountryField
                );

            }
        );


    updateCountryField();

}


/* ============================================================
   LOAD LAST TRIP
   ============================================================ */

function loadLastTrip() {

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


        if (
            !parsed ||
            typeof parsed !==
                "object"
        ) {

            return;

        }


        const candidates =
            getCandidates(
                parsed
            );


        if (
            candidates.length ===
                3
        ) {

            currentTrip =
                parsed;


            currentCandidates =
                candidates;


            renderTripResults(
                parsed
            );


            const results =
                document.getElementById(
                    "resultsSection"
                );


            if (results) {

                results.style.display =
                    "block";

            }

        }

    } catch (error) {

        console.warn(
            "Unable to restore previous trip result:",
            error
        );

    }

}


/* ============================================================
   INITIALIZATION
   ============================================================ */

document.addEventListener(
    "DOMContentLoaded",
    async () => {

        console.log(
            "Wanderlust frontend initializing..."
        );


        initializeNavigation();


        initializeForms();


        initializeSearch();


        initializeHeaderSearch();


        initializeTripChat();


        initializeRandomPage();


        initializeModal();


        loadBasicInformation();


        loadLastTrip();


        if (
            currentCandidates.length ===
                3
        ) {

            renderHomeDestinations(
                currentCandidates
            );


            updateBudgetUI();

        }


        try {

            await API.health();


            console.log(
                "Wanderlust Flask backend connected."
            );

        } catch (error) {

            console.warn(
                "Flask backend health check failed:",
                error.message
            );

        }


        console.log(
            "Wanderlust frontend initialized."
        );

    }
);