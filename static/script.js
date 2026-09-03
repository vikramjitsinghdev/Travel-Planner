/* ============================================================
   WANDERLUST — FRONTEND CONTROLLER
   ============================================================ */

let currentTrip = null;
let basicTripData = null;
let currentTripId = null;

let tripStartInProgress = false;
let initialChatEventHandled = false;

const STORAGE_KEYS = {
    tripId: "wanderlust_trip_id",
    basicTrip: "wanderlust_basic_trip"
};


/* ============================================================
   API
   FRONTEND → app.py ONLY
   ============================================================ */

const API = {

    /* --------------------------------------------------------
       Generic request handler
       -------------------------------------------------------- */

    async request(
        endpoint,
        method = "GET",
        data = null
    ) {

        const options = {
            method: method,
            headers: {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        };


        if (data !== null) {

            options.body =
                JSON.stringify(data);
        }


        console.log(
            `WANDERLUST → ${method} ${endpoint}`,
            data
        );


        let response;

        try {

            response =
                await fetch(
                    endpoint,
                    options
                );

        } catch (error) {

            console.error(
                "NETWORK ERROR:",
                error
            );

            throw new Error(
                "Could not connect to the Flask backend."
            );
        }


        let payload = null;


        try {

            payload =
                await response.json();

        } catch {

            throw new Error(
                `Flask returned an invalid response (${response.status}).`
            );
        }


        console.log(
            `WANDERLUST ← ${response.status} ${endpoint}`,
            payload
        );


        if (!response.ok) {

            throw new Error(
                payload?.message ||
                payload?.error ||
                `Backend request failed (${response.status}).`
            );
        }


        /*
         * Most Wanderlust endpoints use:
         *
         * {
         *     status: "success",
         *     data: ...
         * }
         *
         * But we also tolerate a direct JSON response.
         */

        if (
            payload &&
            payload.status &&
            payload.status !== "success"
        ) {

            throw new Error(
                payload.message ||
                payload.error ||
                "Backend request failed."
            );
        }


        if (
            payload &&
            Object.prototype.hasOwnProperty.call(
                payload,
                "data"
            )
        ) {

            return payload.data;
        }


        return payload;
    },


    /* ========================================================
       HEALTH
       ======================================================== */

    health() {

        return this.request(
            "/api/health",
            "GET"
        );
    },


    /* ========================================================
       BASIC INFORMATION
       ======================================================== */

    saveBasicTrip(
        basicInformation
    ) {

        return this.request(
            "/api/trip/basic-info",
            "POST",
            {
                basic_information:
                    basicInformation
            }
        );
    },


    getBasicTrip(
        tripId
    ) {

        return this.request(
            `/api/trip/basic/${tripId}`,
            "GET"
        );
    },


    /* ========================================================
       DESTINATIONS
       ======================================================== */

    homeDestinations() {

        return this.request(
            "/api/destinations/home",
            "GET"
        );
    },


    randomDestinations(
        limit = 6
    ) {

        return this.request(
            `/api/destinations/random?limit=${limit}`,
            "GET"
        );
    },


    searchDestination(
        query
    ) {

        return this.request(
            "/api/destinations/search",
            "POST",
            {
                query:
                    String(query || "").trim()
            }
        );
    },


    /* ========================================================
       AI TRIP PLANNER
       ======================================================== */

    startTrip(
        tripData
    ) {

        return this.request(
            "/api/trip/start",
            "POST",
            tripData
        );
    },


    updateTrip(
        tripId,
        changeRequest
    ) {

        return this.request(
            "/api/trip/update",
            "POST",
            {
                trip_id:
                    Number(tripId),

                change_request:
                    String(
                        changeRequest || ""
                    ).trim()
            }
        );
    },


    selectTrip(
        tripId,
        selectedIndex
    ) {

        return this.request(
            "/api/trip/select",
            "POST",
            {
                trip_id:
                    Number(tripId),

                selected_index:
                    Number(selectedIndex)
            }
        );
    },


    confirmTrip(
        tripId
    ) {

        return this.request(
            "/api/trip/confirm",
            "POST",
            {
                trip_id:
                    Number(tripId)
            }
        );
    },


    cancelTrip(
        tripId
    ) {

        return this.request(
            "/api/trip/cancel",
            "POST",
            {
                trip_id:
                    Number(tripId)
            }
        );
    },


    deleteTrip(
        tripId
    ) {

        return this.request(
            "/api/trip/delete",
            "POST",
            {
                trip_id:
                    Number(tripId)
            }
        );
    }

};


/* ============================================================
   HELPERS
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


/* ------------------------------------------------------------
   HTML escaping
   ------------------------------------------------------------ */

function escapeHtml(text) {

    return String(text ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


/* ------------------------------------------------------------
   Money
   ------------------------------------------------------------ */

function formatMoney(number) {

    return Number(number || 0)
        .toLocaleString(
            "en-CA",
            {
                style: "currency",
                currency: "CAD"
            }
        );
}


/* ------------------------------------------------------------
   Message helper
   ------------------------------------------------------------ */

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
        message || "";


    element.style.display =
        visible && message
            ? "block"
            : "none";
}


/* ============================================================
   RESPONSE NORMALIZATION
   ============================================================ */

/*
 * Flask may return:
 *
 * [
 *     {...},
 *     {...}
 * ]
 *
 * OR:
 *
 * {
 *     destinations: [...]
 * }
 *
 * OR:
 *
 * {
 *     results: [...]
 * }
 *
 * OR:
 *
 * {
 *     data: [...]
 * }
 *
 * This helper prevents valid backend data
 * from being incorrectly displayed as empty.
 */

function normalizeDestinations(
    response
) {

    if (Array.isArray(response)) {

        return response;
    }


    if (!response) {

        return [];
    }


    if (
        Array.isArray(
            response.destinations
        )
    ) {

        return response.destinations;
    }


    if (
        Array.isArray(
            response.results
        )
    ) {

        return response.results;
    }


    if (
        Array.isArray(
            response.data
        )
    ) {

        return response.data;
    }


    if (
        response.destination
    ) {

        return [
            response.destination
        ];
    }


    if (
        response.result
    ) {

        if (
            Array.isArray(
                response.result
            )
        ) {

            return response.result;
        }


        return [
            response.result
        ];
    }


    /*
     * A single destination object.
     */

    if (
        typeof response === "object" &&
        (
            response.name ||
            response.destination_name
        )
    ) {

        return [
            response
        ];
    }


    return [];
}


/* ============================================================
   PAGE NAVIGATION
   ============================================================ */

function showPage(
    pageName
) {

    document
        .querySelectorAll(".page")
        .forEach(
            page => {

                page.classList.remove(
                    "active"
                );
            }
        );


    const target =
        document.getElementById(
            `page-${pageName}`
        );


    if (!target) {

        console.error(
            "Page does not exist:",
            pageName
        );

        return;
    }


    target.classList.add(
        "active"
    );


    document
        .querySelectorAll(".nav-button")
        .forEach(
            button => {

                button.classList.toggle(
                    "active",
                    button.dataset.page ===
                    pageName
                );
            }
        );


    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });


    /*
     * Page-specific loading.
     */

    if (pageName === "home") {

        loadHomeDestinations();
    }


    if (pageName === "random") {

        loadRandomDestinations();
    }


    if (pageName === "basic") {

        loadBasicInformation();
    }
}


/* ============================================================
   COUNTRY DETECTION
   ============================================================ */

function detectDepartureCountry(
    text
) {

    const lower =
        String(text || "")
            .toLowerCase();


    const countries = [

        ["canada", "Canada"],
        ["united states", "United States"],
        ["usa", "United States"],
        ["india", "India"],
        ["japan", "Japan"],
        ["france", "France"],
        ["germany", "Germany"],
        ["italy", "Italy"],
        ["switzerland", "Switzerland"],
        ["australia", "Australia"],
        ["new zealand", "New Zealand"],
        ["united kingdom", "United Kingdom"],
        ["uk", "United Kingdom"]

    ];


    for (
        const [keyword, country]
        of countries
    ) {

        if (
            lower.includes(keyword)
        ) {

            return country;
        }
    }


    const canadianCodes = [

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
            .filter(Boolean);


    if (
        parts.some(
            part =>
                canadianCodes.includes(part)
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

    const countryInput =
        document.getElementById(
            "country"
        );


    const countryField =
        document.getElementById(
            "countryField"
        );


    const countryHint =
        document.getElementById(
            "countryHint"
        );


    if (
        !countryInput ||
        !countryField
    ) {

        return;
    }


    const detected =
        detectDepartureCountry(
            value("departure_location")
        );


    if (
        getTripScope() === "domestic" &&
        detected
    ) {

        countryInput.value =
            detected;


        countryField.style.display =
            "none";


        if (countryHint) {

            countryHint.textContent =
                "Departure country detected automatically.";
        }

    } else {

        countryField.style.display =
            "flex";


        if (countryHint) {

            countryHint.textContent =
                "";
        }
    }
}


/* ============================================================
   BASIC INFORMATION
   ============================================================ */

function buildBasicTripData() {

    const other =
        value("other");


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
            Number(
                value("travelers")
            ),

        duration_days:
            Number(
                value("duration_days")
            ),

        travel_dates:
            value("travel_dates"),

        maximum_total_travel_time:
            value(
                "maximum_total_travel_time"
            ) ||
            "no preference",

        maximum_distance:
            value(
                "maximum_distance"
            ) ||
            "no preference",

        transportation_preference:
            value(
                "transportation_preference"
            ) ||
            "no preference",

        accommodation_preference:
            value(
                "accommodation_preference"
            ) ||
            "no preference",

        safety_requirement:
            value(
                "safety_requirement"
            ) ||
            "none",

        other:
            other
                ? [other]
                : [],

        budget:
            Number(
                value("budget")
            )
    };
}


/* ============================================================
   BASIC INFORMATION VALIDATION
   ============================================================ */

function validateBasicTripData(
    data
) {

    if (
        !data.departure_location
    ) {

        return (
            "Please enter your departure location."
        );
    }


    if (
        !Number.isInteger(
            data.travelers
        ) ||
        data.travelers < 1
    ) {

        return (
            "Number of travelers must be at least 1."
        );
    }


    if (
        !Number.isInteger(
            data.duration_days
        ) ||
        data.duration_days < 1
    ) {

        return (
            "Trip duration must be at least 1 day."
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


    return null;
}


/* ============================================================
   SAVE BASIC INFORMATION
   ============================================================ */

async function saveBasicInformation() {

    const data =
        buildBasicTripData();


    const error =
        validateBasicTripData(
            data
        );


    if (error) {

        setMessage(
            "basicError",
            error
        );

        return false;
    }


    const button =
        document.getElementById(
            "continueToPlanningButton"
        );


    if (button) {

        button.disabled = true;

        button.textContent =
            "SAVING...";
    }


    setMessage(
        "basicError",
        "",
        false
    );


    setMessage(
        "basicSaved",
        "Saving your trip information..."
    );


    try {

        console.log(
            "Saving basic trip information:",
            data
        );


        const result =
            await API.saveBasicTrip(
                data
            );


        console.log(
            "Basic trip saved:",
            result
        );


        /*
         * Flask should return a trip ID.
         *
         * Accept several reasonable response
         * structures so frontend formatting
         * does not break the database connection.
         */

        const returnedTripId =
            result?.trip_id ??
            result?.id ??
            result?.trip?.trip_id ??
            result?.trip?.id ??
            result?.basic_information?.trip_id ??
            result?.basic_information?.id;


        if (
            !returnedTripId
        ) {

            throw new Error(
                "Flask saved the information but did not return a trip ID."
            );
        }


        currentTripId =
            Number(
                returnedTripId
            );


        if (
            !Number.isInteger(
                currentTripId
            ) ||
            currentTripId <= 0
        ) {

            throw new Error(
                "Flask returned an invalid trip ID."
            );
        }


        /*
         * Preserve returned information
         * when available.
         */

        basicTripData =
            result?.trip ||
            result?.basic_information ||
            data;


        /*
         * Persist locally as a backup.
         */

        localStorage.setItem(
            STORAGE_KEYS.tripId,
            String(currentTripId)
        );


        localStorage.setItem(
            STORAGE_KEYS.basicTrip,
            JSON.stringify(
                basicTripData
            )
        );


        setMessage(
            "basicSaved",
            "Basic trip information saved."
        );


        console.log(
            "Trip ID established:",
            currentTripId
        );


        /*
         * Move to planner scene.
         */

        showPage(
            "planner"
        );


        return true;

    } catch (error) {

        console.error(
            "BASIC INFORMATION ERROR:",
            error
        );


        setMessage(
            "basicError",
            error.message ||
            "Unable to save your trip."
        );


        return false;

    } finally {

        if (button) {

            button.disabled = false;

            button.textContent =
                "CONTINUE TO PLAN TRIP →";
        }
    }
}


/* ============================================================
   LOAD BASIC INFORMATION
   ============================================================ */

async function loadBasicInformation() {

    let tripId =
        currentTripId ||
        Number(
            localStorage.getItem(
                STORAGE_KEYS.tripId
            )
        );


    /*
     * If we don't have a database ID,
     * use the locally cached information.
     */

    if (
        !tripId ||
        !Number.isInteger(
            Number(tripId)
        )
    ) {

        const cached =
            localStorage.getItem(
                STORAGE_KEYS.basicTrip
            );


        if (cached) {

            try {

                basicTripData =
                    JSON.parse(
                        cached
                    );

            } catch {

                basicTripData =
                    null;
            }
        }


        if (basicTripData) {

            populateBasicForm(
                basicTripData
            );
        }


        return;
    }


    currentTripId =
        Number(tripId);


    try {

        const response =
            await API.getBasicTrip(
                currentTripId
            );


        console.log(
            "Loaded basic trip:",
            response
        );


        /*
         * Accommodate:
         *
         * { id: ... }
         *
         * { trip: {...} }
         *
         * { basic_information: {...} }
         */

        const trip =
            response?.trip ||
            response?.basic_information ||
            response;


        if (
            trip &&
            typeof trip === "object"
        ) {

            basicTripData =
                trip;


            currentTripId =
                Number(
                    trip.id ||
                    trip.trip_id ||
                    currentTripId
                );


            localStorage.setItem(
                STORAGE_KEYS.tripId,
                String(currentTripId)
            );


            localStorage.setItem(
                STORAGE_KEYS.basicTrip,
                JSON.stringify(
                    basicTripData
                )
            );


            populateBasicForm(
                basicTripData
            );
        }

    } catch (error) {

        console.warn(
            "Could not retrieve database trip:",
            error
        );


        /*
         * Database request failed, so use
         * the local copy if available.
         */

        const cached =
            localStorage.getItem(
                STORAGE_KEYS.basicTrip
            );


        if (cached) {

            try {

                basicTripData =
                    JSON.parse(
                        cached
                    );


                populateBasicForm(
                    basicTripData
                );

            } catch {

                basicTripData =
                    null;
            }
        }
    }
}


/* ============================================================
   POPULATE BASIC FORM
   ============================================================ */

function populateBasicForm(
    trip
) {

    if (
        !trip ||
        typeof trip !== "object"
    ) {

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
        "budget"

    ];


    fields.forEach(
        id => {

            const element =
                document.getElementById(
                    id
                );


            if (
                element &&
                trip[id] !== undefined &&
                trip[id] !== null
            ) {

                element.value =
                    trip[id];
            }
        }
    );


    const other =
        document.getElementById(
            "other"
        );


    if (
        other &&
        trip.other !== undefined &&
        trip.other !== null
    ) {

        other.value =
            Array.isArray(
                trip.other
            )
                ? trip.other.join(", ")
                : String(
                    trip.other
                );
    }


    if (
        trip.trip_scope
    ) {

        const radio =
            document.querySelector(
                `input[name="trip_scope"][value="${CSS.escape(trip.trip_scope)}"]`
            );


        if (radio) {

            radio.checked =
                true;
        }
    }


    updateCountryField();
}


/* ============================================================
   CHAT HELPERS
   ============================================================ */

function chatSetTyping(
    show
) {

    if (
        typeof window.wanderlustSetTyping ===
        "function"
    ) {

        window.wanderlustSetTyping(
            Boolean(show)
        );
    }
}


/* ------------------------------------------------------------
   Assistant message
   ------------------------------------------------------------ */

function chatAddAssistantMessage(
    text
) {

    if (
        typeof window.wanderlustAddAssistantMessage ===
        "function"
    ) {

        return window.wanderlustAddAssistantMessage(
            String(text || "")
        );
    }


    /*
     * Compatibility fallback.
     */

    const container =
        document.getElementById(
            "tripChatMessages"
        );


    if (!container) {

        console.warn(
            "Chat container not found."
        );

        return null;
    }


    const message =
        document.createElement(
            "div"
        );


    message.className =
        "chat-message assistant";


    message.textContent =
        String(text || "");


    container.appendChild(
        message
    );


    container.scrollTop =
        container.scrollHeight;


    return message;
}


/*
 * Compatibility alias.
 *
 * The previous version of the file used
 * chatAddAssistant() in one place and
 * chatAddAssistantMessage() elsewhere.
 *
 * Both now work.
 */

function chatAddAssistant(
    text
) {

    return chatAddAssistantMessage(
        text
    );
}


/* ============================================================
   CHAT → BACKEND
   ============================================================ */

function initializeTripChatBackend() {

    /*
     * Prevent duplicate initialization.
     */

    if (
        window.__wanderlustChatBackendInitialized
    ) {

        return;
    }


    window.__wanderlustChatBackendInitialized =
        true;


    document.addEventListener(
        "wanderlust:chat-message",
        async event => {

            const message =
                String(
                    event?.detail?.message ||
                    ""
                ).trim();


            if (!message) {

                return;
            }


            /*
             * The initial message is already
             * handled by startTrip().
             *
             * Do not send it twice.
             */

            if (
                tripStartInProgress
            ) {

                initialChatEventHandled =
                    true;


                console.log(
                    "Initial chat event ignored because /api/trip/start is already processing it."
                );


                return;
            }


            /*
             * After the first planning request,
             * chat messages become modifications.
             */

            const tripId =
                Number(
                    currentTripId ||
                    currentTrip?.trip_id ||
                    currentTrip?.id
                );


            if (
                !tripId ||
                !Number.isInteger(
                    tripId
                )
            ) {

                chatAddAssistantMessage(
                    "Please start a trip before asking me to modify it."
                );


                return;
            }


            await processChatUpdate(
                tripId,
                message
            );
        }
    );
}


/* ============================================================
   PROCESS CHAT UPDATE
   ============================================================ */

async function processChatUpdate(
    tripId,
    message
) {

    const clean =
        String(
            message || ""
        ).trim();


    if (!clean) {

        return;
    }


    chatSetTyping(
        true
    );


    console.log(
        "WANDERLUST CHAT → /api/trip/update",
        {
            trip_id:
                tripId,

            change_request:
                clean
        }
    );


    try {

        currentTrip =
            await API.updateTrip(
                tripId,
                clean
            );


        console.log(
            "WANDERLUST CHAT ← /api/trip/update",
            currentTrip
        );


        if (
            currentTrip?.trip_id ||
            currentTrip?.id
        ) {

            currentTripId =
                Number(
                    currentTrip.trip_id ||
                    currentTrip.id
                );


            localStorage.setItem(
                STORAGE_KEYS.tripId,
                String(currentTripId)
            );
        }


        chatSetTyping(
            false
        );


        const response =
            currentTrip?.travel_options ||
            currentTrip?.message ||
            currentTrip?.response;


        if (
            typeof response === "string" &&
            response.trim()
        ) {

            chatAddAssistantMessage(
                response.trim()
            );

        } else {

            chatAddAssistantMessage(
                "I've updated your travel recommendations based on that."
            );
        }


        renderTripResults(
            currentTrip
        );


        updateBudgetUI();

    } catch (error) {

        console.error(
            "CHAT UPDATE ERROR:",
            error
        );


        chatSetTyping(
            false
        );


        chatAddAssistantMessage(
            "I couldn't apply that change. " +
            (
                error.message ||
                "Unknown backend error."
            )
        );

    } finally {

        chatSetTyping(
            false
        );
    }
}


/* ============================================================
   START AI PLANNER
   ============================================================ */

async function startTrip() {

    setMessage(
        "plannerError",
        "",
        false
    );


    /*
     * Recover trip ID from memory if necessary.
     */

    if (
        !currentTripId
    ) {

        const stored =
            Number(
                localStorage.getItem(
                    STORAGE_KEYS.tripId
                )
            );


        if (
            Number.isInteger(stored) &&
            stored > 0
        ) {

            currentTripId =
                stored;
        }
    }


    /*
     * Basic Information must already
     * exist in SQLite.
     */

    if (
        !currentTripId ||
        !Number.isInteger(
            currentTripId
        )
    ) {

        setMessage(
            "plannerError",
            "Please complete Basic Information first."
        );


        showPage(
            "basic"
        );


        return;
    }


    /*
     * Natural-language user request.
     */

    const preferences =
        value(
            "user_preferences"
        );


    if (!preferences) {

        setMessage(
            "plannerError",
            "Please describe what you want from your trip."
        );


        return;
    }


    /*
     * Mark the initial request as being
     * handled by /api/trip/start.
     */

    tripStartInProgress =
        true;


    initialChatEventHandled =
        false;


    chatSetTyping(
        true
    );


    /*
     * app.py receives:
     *
     * {
     *     trip_id: 123,
     *     user_input: "..."
     * }
     *
     * main.py retrieves the basic
     * information from the database.
     */

    const data = {

        trip_id:
            Number(
                currentTripId
            ),

        user_input:
            String(
                preferences
            ).trim()

    };


    console.log(
        "WANDERLUST → /api/trip/start",
        data
    );


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


    try {

        currentTrip =
            await API.startTrip(
                data
            );


        console.log(
            "WANDERLUST ← /api/trip/start",
            currentTrip
        );


        /*
         * Recover the returned trip ID
         * if the backend sends one.
         */

        const returnedTripId =
            currentTrip?.trip_id ??
            currentTrip?.id;


        if (
            returnedTripId
        ) {

            currentTripId =
                Number(
                    returnedTripId
                );


            localStorage.setItem(
                STORAGE_KEYS.tripId,
                String(currentTripId)
            );
        }


        /*
         * Backend finished.
         */

        tripStartInProgress =
            false;


        chatSetTyping(
            false
        );


        /*
         * Display the AI's response.
         */

        const response =
            currentTrip?.travel_options ||
            currentTrip?.message ||
            currentTrip?.response;


        if (
            typeof response === "string" &&
            response.trim()
        ) {

            chatAddAssistantMessage(
                response.trim()
            );

        } else {

            chatAddAssistantMessage(
                "I've finished analyzing your trip preferences and found some destinations that match."
            );
        }


        /*
         * Preserve the existing
         * destination-card interface.
         */

        renderTripResults(
            currentTrip
        );


        updateBudgetUI();


        const results =
            document.getElementById(
                "resultsSection"
            );


        if (results) {

            results.style.display =
                "block";
        }

    } catch (error) {

        console.error(
            "START TRIP ERROR:",
            error
        );


        tripStartInProgress =
            false;


        chatSetTyping(
            false
        );


        chatAddAssistantMessage(
            "I couldn't finish planning your trip. " +
            (
                error.message ||
                "Unknown backend error."
            )
        );


        setMessage(
            "plannerError",
            error.message ||
            "Unable to start travel planning."
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
    }
}


/* ============================================================
   CANDIDATES
   ============================================================ */

function getCandidates(trip) {

    if (!trip) {
        return [];
    }

    /*
     * ========================================================
     * FINAL RECOMMENDATIONS
     * ========================================================
     *
     * The backend's final Gemini stage stores the three
     * selected travel options in:
     *
     *     trip.travel_options
     *
     * These are the destinations the user should see.
     */

    if (
        Array.isArray(
            trip.travel_options
        )
    ) {

        return trip.travel_options
            .filter(
                option =>
                    option &&
                    typeof option === "object"
            )
            .map(
                (option, index) => {

                    return {

                        name:
                            option.destination ||
                            option.destination_name ||
                            "Unknown destination",

                        country:
                            option.country ||
                            "",

                        reason:
                            option.why_it_fits ||
                            option.reason ||
                            option.match_reason ||
                            "",

                        rank:
                            option.rank ||
                            index + 1,

                        highlights:
                            Array.isArray(
                                option.highlights
                            )
                                ? option.highlights
                                : [],

                        limitations:
                            Array.isArray(
                                option.limitations
                            )
                                ? option.limitations
                                : [],

                        budget_summary:
                            option.budget_summary ||
                            "",

                        practicality_summary:
                            option.practicality_summary ||
                            "",

                        weather_summary:
                            option.weather_summary ||
                            "",

                        confidence:
                            option.confidence ||
                            ""

                    };

                }
            );
    }


    /*
     * ========================================================
     * FALLBACK FOR OLD RESPONSES
     * ========================================================
     *
     * Only use these if the backend did not return
     * travel_options.
     */

    if (
        trip.candidate_result &&
        Array.isArray(
            trip.candidate_result.candidates
        )
    ) {

        return trip
            .candidate_result
            .candidates;

    }


    if (
        Array.isArray(
            trip.candidates
        )
    ) {

        return trip.candidates.map(
            candidate => {

                if (
                    typeof candidate ===
                    "string"
                ) {

                    return {

                        name:
                            candidate,

                        country:
                            "",

                        reason:
                            ""

                    };

                }

                return candidate;

            }
        );

    }


    if (
        Array.isArray(
            trip.data?.candidates
        )
    ) {

        return trip.data.candidates;

    }


    return [];
}

/* ============================================================
   RENDER AI RESULTS
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


    grid.innerHTML =
        "";


    if (
        !candidates.length
    ) {

        grid.innerHTML = `

            <div class="panel">

                <strong>
                    No destinations were returned.
                </strong>

                <p>
                    Try changing your travel preferences
                    and search again.
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


            card.innerHTML = `

                <div class="result-card-body">

                    <span class="result-number">
                        ${index + 1}
                    </span>

                    <h3>
                        ${escapeHtml(
                            candidate.name ||
                            candidate.destination_name ||
                            "Unknown destination"
                        )}
                    </h3>

                    <div class="result-country">

                        ${escapeHtml(
                            candidate.country ||
                            ""
                        )}

                    </div>

                    <p class="result-reason">

                        ${escapeHtml(
                            candidate.reason ||
                            candidate.match_reason ||
                            "No additional explanation was provided."
                        )}

                    </p>

                    <div class="option-meta">

                        <div class="meta-box">

                            <small>
                                Trip
                            </small>

                            <strong>

                                ${escapeHtml(
                                    basicTripData?.trip_scope ||
                                    "—"
                                )}

                            </strong>

                        </div>

                        <div class="meta-box">

                            <small>
                                Travelers
                            </small>

                            <strong>

                                ${escapeHtml(
                                    basicTripData?.travelers ||
                                    "—"
                                )}

                            </strong>

                        </div>

                        <div class="meta-box">

                            <small>
                                Days
                            </small>

                            <strong>

                                ${escapeHtml(
                                    basicTripData?.duration_days ||
                                    "—"
                                )}

                            </strong>

                        </div>

                    </div>


                    <div
                        style="
                            margin-top:15px;
                            display:flex;
                            gap:8px;
                            flex-wrap:wrap;
                        "
                    >

                        <button
                            class="btn btn-blue"
                            type="button"
                        >

                            SELECT THIS TRIP

                        </button>


                        <button
                            class="btn btn-light"
                            type="button"
                        >

                            DETAILS

                        </button>

                    </div>

                </div>

            `;


            const buttons =
                card.querySelectorAll(
                    "button"
                );


            if (
                buttons[0]
            ) {

                buttons[0].addEventListener(
                    "click",
                    () => {

                        selectTrip(
                            index
                        );
                    }
                );
            }


            if (
                buttons[1]
            ) {

                buttons[1].addEventListener(
                    "click",
                    () => {

                        showDestination(
                            index
                        );
                    }
                );
            }


            grid.appendChild(
                card
            );
        }
    );
}


/* ============================================================
   SELECT TRIP
   ============================================================ */

async function selectTrip(
    index
) {

    if (!currentTrip) {

        alert(
            "No active trip."
        );


        return;
    }


    const candidates =
        getCandidates(
            currentTrip
        );


    if (
        index < 0 ||
        index >= candidates.length
    ) {

        alert(
            "Invalid destination."
        );


        return;
    }


    const selected =
        candidates[index];


    const panel =
        document.getElementById(
            "selectionPanel"
        );


    const name =
        document.getElementById(
            "selectedTripName"
        );


    const content =
        document.getElementById(
            "selectedTripContent"
        );


    if (panel) {

        panel.style.display =
            "block";
    }


    if (name) {

        name.textContent =
            selected.name ||
            selected.destination_name ||
            "Selected destination";
    }


    if (content) {

        content.innerHTML = `

            <div
                class="loading"
                style="display:block;"
            >

                Calculating detailed trip costs...

            </div>

        `;
    }


    const tripId =
        Number(
            currentTrip.trip_id ||
            currentTripId
        );


    if (
        !tripId ||
        !Number.isInteger(
            tripId
        )
    ) {

        if (content) {

            content.innerHTML = `

                <div
                    class="error"
                    style="display:block;"
                >

                    No active trip ID was found.

                </div>

            `;
        }


        return;
    }


    try {

        currentTrip =
            await API.selectTrip(
                tripId,
                index
            );


        renderSelectedTrip(
            currentTrip
        );


        updateBudgetUI();

    } catch (error) {

        console.error(
            "SELECT TRIP ERROR:",
            error
        );


        if (content) {

            content.innerHTML = `

                <div
                    class="error"
                    style="display:block;"
                >

                    ${escapeHtml(
                        error.message
                    )}

                </div>

            `;
        }
    }
}


/* ============================================================
   SELECTED TRIP
   ============================================================ */

function renderSelectedTrip(
    trip
) {

    const selected =
        trip?.selected_trip ||
        {};


    const budget =
        trip?.budget ||
        {};


    const costs =
        Array.isArray(
            selected.costs
        )
            ? selected.costs
            : [];


    let html = `

        <div class="option-meta">

            <div class="meta-box">

                <small>
                    Status
                </small>

                <strong>

                    ${escapeHtml(
                        trip?.status ||
                        "—"
                    )}

                </strong>

            </div>


            <div class="meta-box">

                <small>
                    Estimated Total
                </small>

                <strong>

                    ${formatMoney(
                        budget.estimated_total
                    )}

                </strong>

            </div>


            <div class="meta-box">

                <small>
                    Remaining
                </small>

                <strong>

                    ${formatMoney(
                        budget.estimated_remaining
                    )}

                </strong>

            </div>

        </div>

    `;


    if (
        costs.length
    ) {

        html += `

            <div style="margin-top:17px;">

                <h4>
                    Estimated Costs
                </h4>

                <div class="expense-list">

        `;


        costs.forEach(
            cost => {

                html += `

                    <div class="expense">

                        <div class="expense-main">

                            <strong>

                                ${escapeHtml(
                                    cost.description ||
                                    cost.category ||
                                    "Travel cost"
                                )}

                            </strong>

                            <span>

                                ${escapeHtml(
                                    cost.category ||
                                    "other"
                                )}

                            </span>

                        </div>

                        <strong>

                            ${formatMoney(
                                cost.amount
                            )}

                        </strong>

                    </div>

                `;
            }
        );


        html += `

                </div>

            </div>

        `;
    }


    if (
        budget.estimates_affordable ===
        false
    ) {

        html += `

            <div
                class="error"
                style="display:block;"
            >

                This trip exceeds the available budget.

            </div>

        `;

    } else {

        html += `

            <div
                class="success"
                style="display:block;"
            >

                This trip currently fits within the budget.

            </div>

        `;
    }


    const content =
        document.getElementById(
            "selectedTripContent"
        );


    if (content) {

        content.innerHTML =
            html;
    }
}


/* ============================================================
   CONFIRM TRIP
   ============================================================ */

async function confirmTrip() {

    if (!currentTrip) {

        alert(
            "No active trip."
        );


        return;
    }


    if (
        currentTrip.status !==
        "awaiting_confirmation"
    ) {

        alert(
            "Select a destination first."
        );


        return;
    }


    const button =
        document.getElementById(
            "confirmTripButton"
        );


    if (button) {

        button.disabled =
            true;


        button.textContent =
            "CONFIRMING...";
    }


    try {

        currentTrip =
            await API.confirmTrip(
                currentTrip.trip_id ||
                currentTripId
            );


        renderSelectedTrip(
            currentTrip
        );


        updateBudgetUI();


        alert(
            "Trip confirmed."
        );

    } catch (error) {

        console.error(
            "CONFIRM TRIP ERROR:",
            error
        );


        alert(
            error.message
        );

    } finally {

        if (button) {

            button.disabled =
                false;


            button.textContent =
                "CONFIRM TRIP";
        }
    }
}


/* ============================================================
   UPDATE TRIP
   ============================================================ */

async function updateTrip(
    changeRequest
) {

    if (
        !currentTrip?.trip_id &&
        !currentTripId
    ) {

        alert(
            "No active trip."
        );


        return;
    }


    const clean =
        String(
            changeRequest || ""
        ).trim();


    if (!clean) {

        alert(
            "Please enter the changes."
        );


        return;
    }


    try {

        setMessage(
            "plannerLoading",
            "Updating your travel options..."
        );


        currentTrip =
            await API.updateTrip(
                currentTrip.trip_id ||
                currentTripId,
                clean
            );


        renderTripResults(
            currentTrip
        );


        updateBudgetUI();

    } catch (error) {

        console.error(
            "UPDATE TRIP ERROR:",
            error
        );


        setMessage(
            "plannerError",
            error.message
        );

    } finally {

        setMessage(
            "plannerLoading",
            "",
            false
        );
    }
}


/* ============================================================
   CLEAR SELECTION
   ============================================================ */

function clearSelection() {

    const panel =
        document.getElementById(
            "selectionPanel"
        );


    if (panel) {

        panel.style.display =
            "none";
    }
}


/* ============================================================
   RESET PLANNER
   ============================================================ */

function resetPlanner() {

    currentTrip =
        null;


    const results =
        document.getElementById(
            "resultsSection"
        );


    if (results) {

        results.style.display =
            "none";
    }


    clearSelection();


    showPage(
        "planner"
    );
}


/* ============================================================
   CANCEL
   ============================================================ */

async function cancelCurrentTrip() {

    const tripId =
        Number(
            currentTrip?.trip_id ||
            currentTripId
        );


    if (
        !tripId ||
        !Number.isInteger(
            tripId
        )
    ) {

        return;
    }


    if (
        !confirm(
            "Cancel this planning session?"
        )
    ) {

        return;
    }


    try {

        currentTrip =
            await API.cancelTrip(
                tripId
            );


        clearSelection();


        updateBudgetUI();


        alert(
            "Trip cancelled."
        );

    } catch (error) {

        console.error(
            "CANCEL TRIP ERROR:",
            error
        );


        alert(
            error.message
        );
    }
}


/* ============================================================
   DELETE
   ============================================================ */

async function deleteCurrentTrip() {

    if (!currentTripId) {

        return;
    }


    if (
        !confirm(
            "Delete this trip session permanently?"
        )
    ) {

        return;
    }


    try {

        await API.deleteTrip(
            currentTripId
        );


        currentTrip =
            null;


        basicTripData =
            null;


        currentTripId =
            null;


        localStorage.removeItem(
            STORAGE_KEYS.tripId
        );


        localStorage.removeItem(
            STORAGE_KEYS.basicTrip
        );


        resetPlanner();


        showPage(
            "home"
        );

    } catch (error) {

        console.error(
            "DELETE TRIP ERROR:",
            error
        );


        alert(
            error.message
        );
    }
}


/* ============================================================
   AI DESTINATION DETAILS
   ============================================================ */

function showDestination(
    index
) {

    if (!currentTrip) {

        return;
    }


    const candidates =
        getCandidates(
            currentTrip
        );


    const candidate =
        candidates[index];


    if (!candidate) {

        return;
    }


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


    if (title) {

        title.textContent =
            candidate.name ||
            candidate.destination_name ||
            "";
    }


    if (country) {

        country.textContent =
            candidate.country ||
            "";
    }


    if (reason) {

        reason.textContent =
            candidate.reason ||
            candidate.match_reason ||
            "";
    }


    modal.classList.add(
        "open"
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


    if (modal) {

        modal.classList.remove(
            "open"
        );
    }
}


/* ============================================================
   HOME DESTINATIONS
   ============================================================ */

async function loadHomeDestinations() {

    const container =
        document.getElementById(
            "homeDestinations"
        );


    if (!container) {

        return;
    }


    try {

        const response =
            await API.homeDestinations();


        const destinations =
            normalizeDestinations(
                response
            );


        renderHomeDestinations(
            destinations
        );

    } catch (error) {

        console.error(
            "HOME ERROR:",
            error
        );


        container.innerHTML = `

            <div class="panel">

                Unable to load destinations.

                <p>

                    ${escapeHtml(
                        error.message
                    )}

                </p>

            </div>

        `;
    }
}


/* ============================================================
   RENDER HOME
   ============================================================ */

function renderHomeDestinations(
    destinations
) {

    const container =
        document.getElementById(
            "homeDestinations"
        );


    if (!container) {

        return;
    }


    container.innerHTML =
        "";


    if (
        !Array.isArray(
            destinations
        ) ||
        !destinations.length
    ) {

        container.innerHTML = `

            <div class="panel">

                No destinations available.

            </div>

        `;


        return;
    }


    destinations.forEach(
        destination => {

            const card =
                document.createElement(
                    "article"
                );


            card.className =
                "destination-card";


            card.innerHTML = `

                <img
                    src="${escapeHtml(
                        destination.image_url ||
                        ""
                    )}"
                    alt="${escapeHtml(
                        destination.name ||
                        "Destination"
                    )}"
                    loading="lazy"
                >


                <div class="destination-overlay">

                    <h3>

                        ${escapeHtml(
                            destination.name ||
                            ""
                        )}

                    </h3>


                    <p>

                        ${escapeHtml(
                            destination.description ||
                            destination.country ||
                            ""
                        )}

                    </p>

                </div>

            `;


            card.addEventListener(
                "click",
                () => {

                    openDestination(
                        destination
                    );
                }
            );


            container.appendChild(
                card
            );
        }
    );
}


/* ============================================================
   RANDOM DESTINATIONS
   ============================================================ */

async function loadRandomDestinations() {

    const container =
        document.getElementById(
            "randomDestinations"
        );


    if (!container) {

        return;
    }


    container.innerHTML = `

        <div
            class="loading"
            style="display:block;"
        >

            Loading destinations...

        </div>

    `;


    try {

        const response =
            await API.randomDestinations(
                6
            );


        console.log(
            "Random destination response:",
            response
        );


        const destinations =
            normalizeDestinations(
                response
            );


        renderRandomDestinations(
            destinations
        );

    } catch (error) {

        console.error(
            "RANDOM ERROR:",
            error
        );


        container.innerHTML = `

            <div
                class="error"
                style="display:block;"
            >

                Unable to load random destinations.

                <br>

                ${escapeHtml(
                    error.message
                )}

            </div>

        `;
    }
}


/* ============================================================
   RENDER RANDOM
   ============================================================ */

function renderRandomDestinations(
    destinations
) {

    const container =
        document.getElementById(
            "randomDestinations"
        );


    if (!container) {

        return;
    }


    container.innerHTML =
        "";


    if (
        !Array.isArray(
            destinations
        ) ||
        !destinations.length
    ) {

        container.innerHTML = `

            <div class="panel">

                No random destinations are available.

            </div>

        `;


        return;
    }


    destinations.forEach(
        destination => {

            const card =
                document.createElement(
                    "article"
                );


            card.className =
                "random-card";


            card.innerHTML = `

                <img
                    class="random-card-image"
                    src="${escapeHtml(
                        destination.image_url ||
                        ""
                    )}"
                    alt="${escapeHtml(
                        destination.name ||
                        "Destination"
                    )}"
                    loading="lazy"
                >


                <div class="random-card-content">

                    <h3>

                        ${escapeHtml(
                            destination.name ||
                            ""
                        )}

                    </h3>


                    <div class="random-card-country">

                        ${escapeHtml(
                            destination.country ||
                            ""
                        )}

                    </div>


                    <p class="random-card-description">

                        ${escapeHtml(
                            destination.description ||
                            ""
                        )}

                    </p>


                    <button
                        class="btn btn-blue random-card-button"
                        type="button"
                    >

                        EXPLORE

                    </button>

                </div>

            `;


            const button =
                card.querySelector(
                    "button"
                );


            if (button) {

                button.addEventListener(
                    "click",
                    event => {

                        event.stopPropagation();


                        openDestination(
                            destination
                        );
                    }
                );
            }


            card.addEventListener(
                "click",
                () => {

                    openDestination(
                        destination
                    );
                }
            );


            container.appendChild(
                card
            );
        }
    );
}


/* ============================================================
   RANDOMIZE
   ============================================================ */

async function randomizeDestinations() {

    await loadRandomDestinations();
}


/* ============================================================
   OPEN DESTINATION
   ============================================================ */

function openDestination(
    destination
) {

    showPage(
        "search"
    );


    const details =
        document.getElementById(
            "destinationDetails"
        );


    const content =
        document.getElementById(
            "destinationDetailsContent"
        );


    if (
        !details ||
        !content
    ) {

        return;
    }


    details.style.display =
        "block";


    content.innerHTML = `

        <img
            class="destination-detail-image"
            src="${escapeHtml(
                destination.image_url ||
                ""
            )}"
            alt="${escapeHtml(
                destination.name ||
                "Destination"
            )}"
            loading="lazy"
        >


        <h2>

            ${escapeHtml(
                destination.name ||
                ""
            )}

        </h2>


        <p>

            ${escapeHtml(
                destination.country ||
                ""
            )}

        </p>


        <p>

            ${escapeHtml(
                destination.description ||
                "No description available."
            )}

        </p>


        <div class="destination-detail-grid">

            <div class="destination-detail-meta">

                <small>
                    Region
                </small>

                <strong>

                    ${escapeHtml(
                        destination.region ||
                        "—"
                    )}

                </strong>

            </div>


            <div class="destination-detail-meta">

                <small>
                    Latitude
                </small>

                <strong>

                    ${escapeHtml(
                        destination.latitude ??
                        "—"
                    )}

                </strong>

            </div>


            <div class="destination-detail-meta">

                <small>
                    Longitude
                </small>

                <strong>

                    ${escapeHtml(
                        destination.longitude ??
                        "—"
                    )}

                </strong>

            </div>

        </div>

    `;
}


/* ============================================================
   SEARCH DESTINATION
   ============================================================ */

async function searchDestination() {

    const input =
        document.getElementById(
            "destinationSearchInput"
        );


    const result =
        document.getElementById(
            "destinationSearchResults"
        );


    const loading =
        document.getElementById(
            "destinationSearchLoading"
        );


    if (!input) {

        return;
    }


    const query =
        String(
            input.value || ""
        ).trim();


    if (!query) {

        setMessage(
            "searchError",
            "Please enter a destination."
        );


        return;
    }


    setMessage(
        "searchError",
        "",
        false
    );


    if (loading) {

        loading.style.display =
            "block";


        loading.textContent =
            "Searching destination...";
    }


    if (result) {

        result.innerHTML =
            "";
    }


    try {

        const response =
            await API.searchDestination(
                query
            );


        console.log(
            "Search response:",
            response
        );


        const destinations =
            normalizeDestinations(
                response
            );


        renderSearchDestination(
            destinations
        );

    } catch (error) {

        console.error(
            "SEARCH ERROR:",
            error
        );


        setMessage(
            "searchError",
            error.message ||
            "Unable to search destination."
        );

    } finally {

        if (loading) {

            loading.style.display =
                "none";
        }
    }
}


/* ============================================================
   RENDER SEARCH RESULTS
   ============================================================ */

function renderSearchDestination(
    destinations
) {

    const result =
        document.getElementById(
            "destinationSearchResults"
        );


    if (!result) {

        return;
    }


    result.innerHTML =
        "";


    if (
        !Array.isArray(
            destinations
        ) ||
        !destinations.length
    ) {

        result.innerHTML = `

            <div class="panel">

                No destination found.

            </div>

        `;


        return;
    }


    destinations.forEach(
        item => {

            const card =
                document.createElement(
                    "article"
                );


            card.className =
                "search-result-card";


            card.innerHTML = `

                <img
                    src="${escapeHtml(
                        item.image_url ||
                        ""
                    )}"
                    alt="${escapeHtml(
                        item.name ||
                        "Destination"
                    )}"
                    loading="lazy"
                >


                <div class="search-result-body">

                    <h3>

                        ${escapeHtml(
                            item.name ||
                            ""
                        )}

                    </h3>


                    <p>

                        ${escapeHtml(
                            item.country ||
                            ""
                        )}

                    </p>


                    <p>

                        ${escapeHtml(
                            item.description ||
                            "No description available."
                        )}

                    </p>


                    <button
                        class="btn btn-blue"
                        type="button"
                    >

                        VIEW DESTINATION

                    </button>

                </div>

            `;


            const button =
                card.querySelector(
                    "button"
                );


            if (button) {

                button.addEventListener(
                    "click",
                    () => {

                        openDestination(
                            item
                        );
                    }
                );
            }


            result.appendChild(
                card
            );
        }
    );
}


/* ============================================================
   SEARCH INITIALIZATION
   ============================================================ */

function initializeSearch() {

    const input =
        document.getElementById(
            "destinationSearchInput"
        );


    const button =
        document.getElementById(
            "destinationSearchButton"
        );


    if (button) {

        button.addEventListener(
            "click",
            event => {

                event.preventDefault();

                searchDestination();
            }
        );
    }


    if (input) {

        input.addEventListener(
            "keydown",
            event => {

                if (
                    event.key ===
                    "Enter"
                ) {

                    event.preventDefault();

                    searchDestination();
                }
            }
        );
    }
}


/* ============================================================
   NAVIGATION INITIALIZATION
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
                    event => {

                        event.preventDefault();


                        const page =
                            button.dataset.page;


                        if (page) {

                            showPage(
                                page
                            );
                        }
                    }
                );
            }
        );
}


/* ============================================================
   FORM INITIALIZATION
   ============================================================ */

function initializeForms() {

    const departure =
        document.getElementById(
            "departure_location"
        );


    if (departure) {

        departure.addEventListener(
            "input",
            updateCountryField
        );
    }


    document
        .querySelectorAll(
            'input[name="trip_scope"]'
        )
        .forEach(
            radio => {

                radio.addEventListener(
                    "change",
                    updateCountryField
                );
            }
        );


    const basicForm =
        document.getElementById(
            "basicTripForm"
        );


    if (basicForm) {

        basicForm.addEventListener(
            "submit",
            async event => {

                event.preventDefault();


                await saveBasicInformation();
            }
        );
    }


    const plannerForm =
    document.getElementById(
        "tripForm"
    );

if (plannerForm) {

    plannerForm.addEventListener(
        "submit",
        event => {

            event.preventDefault();

            startTrip();

        }
    );

}


const startButton =
    document.getElementById(
        "startTripButton"
    );

if (startButton) {

    startButton.addEventListener(
        "click",
        event => {

            /*
             * The inline HTML chat controller
             * handles opening the visual chat scene.
             *
             * This handler handles the actual
             * backend request.
             */

            event.preventDefault();

            startTrip();

        }
    );

}
}


/* ============================================================
   RANDOM INITIALIZATION
   ============================================================ */

function initializeRandomPage() {

    const button =
        document.getElementById(
            "randomizeButton"
        );


    if (!button) {

        return;
    }


    /*
     * We intentionally attach the listener
     * only here.
     *
     * Do not also use:
     *
     * onclick="randomizeDestinations()"
     */

    button.addEventListener(
        "click",
        async event => {

            event.preventDefault();


            button.disabled =
                true;


            button.textContent =
                "LOADING...";


            try {

                await randomizeDestinations();

            } finally {

                button.disabled =
                    false;


                button.textContent =
                    "↻ RANDOMIZE";
            }
        }
    );
}


/* ============================================================
   MODAL INITIALIZATION
   ============================================================ */

function initializeModal() {

    const modal =
        document.getElementById(
            "destinationModal"
        );


    if (!modal) {

        return;
    }


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
}


/* ============================================================
   BUDGET UI
   ============================================================ */

function updateBudgetUI() {

    const budget =
        currentTrip?.budget;


    const empty =
        document.getElementById(
            "budgetEmpty"
        );


    const content =
        document.getElementById(
            "budgetContent"
        );


    if (!budget) {

        if (empty) {

            empty.style.display =
                "block";
        }


        if (content) {

            content.style.display =
                "none";
        }


        return;
    }


    if (empty) {

        empty.style.display =
            "none";
    }


    if (content) {

        content.style.display =
            "block";
    }


    const total =
        Number(
            budget.total_budget ||
            0
        );


    const spent =
        Number(
            budget.spent ||
            0
        );


    const estimated =
        Number(
            budget.estimated_total ||
            0
        );


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


    if (totalElement) {

        totalElement.textContent =
            formatMoney(
                total
            );
    }


    if (spentElement) {

        spentElement.textContent =
            formatMoney(
                spent
            );
    }


    if (remainingElement) {

        remainingElement.textContent =
            formatMoney(
                budget.remaining
            );
    }


    if (estimatedElement) {

        estimatedElement.textContent =
            formatMoney(
                estimated
            );
    }


    const progress =
        document.getElementById(
            "budgetProgress"
        );


    if (progress) {

        const used =
            spent +
            estimated;


        const percentage =
            total > 0
                ? Math.min(
                    100,
                    (
                        used /
                        total
                    ) * 100
                )
                : 0;


        progress.style.width =
            `${percentage}%`;
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


        /*
         * Initialize UI systems first.
         */

        initializeNavigation();

        initializeForms();

        initializeRandomPage();

        initializeSearch();

        initializeModal();

        initializeTripChatBackend();


        /*
         * Recover saved trip ID.
         */

        const storedTripId =
            Number(
                localStorage.getItem(
                    STORAGE_KEYS.tripId
                )
            );


        if (
            Number.isInteger(
                storedTripId
            ) &&
            storedTripId > 0
        ) {

            currentTripId =
                storedTripId;


            console.log(
                "Recovered trip ID:",
                currentTripId
            );
        }


        /*
         * Recover cached basic information
         * before asking Flask.
         */

        const cachedBasicTrip =
            localStorage.getItem(
                STORAGE_KEYS.basicTrip
            );


        if (cachedBasicTrip) {

            try {

                basicTripData =
                    JSON.parse(
                        cachedBasicTrip
                    );

            } catch {

                basicTripData =
                    null;
            }
        }


        /*
         * Check Flask first.
         */

        try {

            await API.health();


            console.log(
                "Wanderlust Flask backend connected."
            );

        } catch (error) {

            console.warn(
                "Flask backend health check failed:",
                error
            );
        }


        /*
         * Load basic trip from SQLite
         * when a trip ID exists.
         */

        if (
            currentTripId
        ) {

            await loadBasicInformation();
        }


        /*
         * Home destinations.
         */

        await loadHomeDestinations();


        console.log(
            "Wanderlust frontend initialized."
        );
    }
);