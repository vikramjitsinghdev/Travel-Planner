/* ============================================================
   WANDERLUST
   NEW FRONTEND CONTROLLER
   ============================================================

   NEW ARCHITECTURE

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
            +-------------------------+
            |                         |
            v                         v
       MoodAgent                TravelAgent
                                   |
                              Gemini selects
                              EXACTLY 3
                                   |
                         +---------+---------+
                         |                   |
                         v                   v
                  ResearchAgent          Pexels
                         |
              +----------+----------+
              |          |          |
              v          v          v
           Worker 1   Worker 2   Worker 3
              |          |          |
             D1         D2         D3
              |          |          |
              +----------+----------+
                         |
                    Gemma QC
                         |
                         v
                 Enriched results
                         |
                         v
                       main.py
                         |
                         v
                       app.py
                         |
                         v
                     script.js
                         |
                         v
                    index.html


   IMPORTANT:

   The frontend DOES NOT know about:
       - Worker 1 models
       - Worker 2 models
       - Worker 3 models
       - Gemma
       - ResearchAgent internals
       - Gemini internals

   It only receives the final three destination options.
*/


/* ============================================================
   GLOBAL STATE
   ============================================================ */

let currentTrip = null;

let basicTripData = null;

let currentTripId = null;

let tripStartInProgress = false;

let tripChatProcessing = false;

let chatStarted = false;


/* ============================================================
   LOCAL STORAGE
   ============================================================ */

const STORAGE_KEYS = {

    tripId:
        "wanderlust_trip_id",

    basicTrip:
        "wanderlust_basic_trip"

};


/* ============================================================
   API CONNECTOR
   ============================================================ */

const API = {

    async request(
        endpoint,
        method = "GET",
        data = null
    ) {

        const options = {

            method:
                method,

            headers: {}

        };


        if (data !== null) {

            options.headers[
                "Content-Type"
            ] = "application/json";

            options.body =
                JSON.stringify(
                    data
                );

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
                "Unable to connect to the Flask server."
            );

        }


        let payload;


        try {

            payload =
                await response.json();

        } catch (error) {

            throw new Error(
                "The Flask server returned an invalid response."
            );

        }


        if (
            !response.ok ||
            payload.status !== "success"
        ) {

            throw new Error(
                payload.message ||
                "The backend request failed."
            );

        }


        return payload.data;

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
       BASIC TRIP INFORMATION
    ======================================================== */

    saveBasicInformation(
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
       START NEW AI TRIP
    ======================================================== */

    startTrip(
        tripId,
        userInput
    ) {

        return this.request(

            "/api/trip/start",

            "POST",

            {

                trip_id:
                    tripId,

                user_input:
                    String(
                        userInput
                    )

            }

        );

    },


    /* ========================================================
       UPDATE TRIP
    ======================================================== */

    updateTrip(
        tripId,
        changeRequest
    ) {

        return this.request(

            "/api/trip/update",

            "POST",

            {

                trip_id:
                    tripId,

                change_request:
                    String(
                        changeRequest
                    )

            }

        );

    },


    /* ========================================================
       SELECT DESTINATION
    ======================================================== */

    selectTrip(
        tripId,
        selectedIndex
    ) {

        return this.request(

            "/api/trip/select",

            "POST",

            {

                trip_id:
                    tripId,

                selected_index:
                    selectedIndex

            }

        );

    },


    /* ========================================================
       STATUS
    ======================================================== */

    getTripStatus(
        tripId
    ) {

        return this.request(

            "/api/trip/status",

            "POST",

            {

                trip_id:
                    tripId

            }

        );

    },


    /* ========================================================
       CONFIRM
    ======================================================== */

    confirmTrip(
        tripId
    ) {

        return this.request(

            "/api/trip/confirm",

            "POST",

            {

                trip_id:
                    tripId

            }

        );

    },


    /* ========================================================
       CANCEL
    ======================================================== */

    cancelTrip(
        tripId
    ) {

        return this.request(

            "/api/trip/cancel",

            "POST",

            {

                trip_id:
                    tripId

            }

        );

    },


    /* ========================================================
       DELETE
    ======================================================== */

    deleteTrip(
        tripId
    ) {

        return this.request(

            "/api/trip/delete",

            "POST",

            {

                trip_id:
                    tripId

            }

        );

    },


    /* ========================================================
       RANDOM DESTINATIONS
    ======================================================== */

    randomDestinations(
        limit = 6
    ) {

        return this.request(

            `/api/destinations/random?limit=${limit}`,

            "GET"

        );

    },


    /* ========================================================
       DESTINATION SEARCH
    ======================================================== */

    searchDestination(
        query
    ) {

        return this.request(

            "/api/destinations/search",

            "POST",

            {

                query:
                    String(
                        query
                    )

            }

        );

    }

};


/* ============================================================
   BASIC DOM HELPERS
   ============================================================ */

function value(
    id
) {

    const element =
        document.getElementById(
            id
        );


    if (!element) {

        return "";

    }


    return String(
        element.value || ""
    ).trim();

}


/* ============================================================
   SET MESSAGE
   ============================================================ */

function setMessage(
    id,
    message,
    visible = true
) {

    const element =
        document.getElementById(
            id
        );


    if (!element) {

        return;

    }


    element.textContent =
        String(
            message || ""
        );


    element.style.display =
        visible
            ? "block"
            : "none";

}


/* ============================================================
   ESCAPE HTML
   ============================================================ */

function escapeHtml(
    text
) {

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
   FORMAT MONEY
   ============================================================ */

function formatMoney(
    number
) {

    const amount =
        Number(
            number || 0
        );


    if (
        !Number.isFinite(
            amount
        )
    ) {

        return "$0.00";

    }


    return amount.toLocaleString(
        "en-CA",
        {

            style:
                "currency",

            currency:
                "CAD"

        }
    );

}


/* ============================================================
   PAGE NAVIGATION
   ============================================================ */

function showPage(
    pageName
) {

    document
        .querySelectorAll(
            ".page"
        )
        .forEach(
            page => {

                page.classList.remove(
                    "active"
                );

            }
        );


    const target =
        document.getElementById(
            "page-" +
            pageName
        );


    if (target) {

        target.classList.add(
            "active"
        );

    }


    document
        .querySelectorAll(
            ".nav-button"
        )
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

        top:
            0,

        behavior:
            "smooth"

    });

}


/* ============================================================
   COUNTRY DETECTION
   ============================================================ */

function detectDepartureCountry(
    text
) {

    const lower =
        String(
            text || ""
        )
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
            .split(
                /[, ]+/
            )
            .map(
                item =>
                    item.trim()
            )
            .filter(
                Boolean
            );


    if (
        parts.some(
            item =>
                canadianProvinceCodes
                    .includes(
                        item
                    )
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

    return {

        departure_location:
            value(
                "departure_location"
            ),

        trip_scope:
            getTripScope(),

        country:
            value(
                "country"
            ) || null,

        region:
            null,

        travelers:
            Number(
                value(
                    "travelers"
                )
            ),

        duration_days:
            Number(
                value(
                    "duration_days"
                )
            ),

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
            Number(
                value(
                    "budget"
                )
            ),

        currency:
            "CAD"

    };

}


/* ============================================================
   BASIC FORM VALIDATION
   ============================================================ */

function validateBasicTripData(
    data
) {

    if (
        !data.departure_location
    ) {

        return "Please enter your departure location.";

    }


    if (
        !Number.isFinite(
            data.travelers
        ) ||
        data.travelers < 1
    ) {

        return "Please enter a valid number of travelers.";

    }


    if (
        !Number.isFinite(
            data.duration_days
        ) ||
        data.duration_days < 1
    ) {

        return "Please enter a valid trip duration.";

    }


    if (
        !data.travel_dates
    ) {

        return "Please enter your travel dates.";

    }


    if (
        !Number.isFinite(
            data.budget
        ) ||
        data.budget <= 0
    ) {

        return "Please enter a valid travel budget.";

    }


    return null;

}


/* ============================================================
   SAVE BASIC INFORMATION
   ============================================================ */

async function saveBasicInformation() {

    const data =
        buildBasicTripData();


    const validationError =
        validateBasicTripData(
            data
        );


    if (validationError) {

        setMessage(
            "basicError",
            validationError
        );

        return null;

    }


    try {

        setMessage(
            "basicError",
            "",
            false
        );


        const result =
            await API.saveBasicInformation(
                data
            );


        if (
            !result ||
            !result.trip_id
        ) {

            throw new Error(
                "The backend did not return a trip ID."
            );

        }


        basicTripData =
            data;


        currentTripId =
            Number(
                result.trip_id
            );


        localStorage.setItem(

            STORAGE_KEYS.tripId,

            String(
                currentTripId
            )

        );


        localStorage.setItem(

            STORAGE_KEYS.basicTrip,

            JSON.stringify(
                basicTripData
            )

        );


        return result;

    } catch (error) {

        console.error(
            "SAVE BASIC INFORMATION ERROR:",
            error
        );


        setMessage(
            "basicError",
            error.message ||
            "Unable to save basic trip information."
        );


        return null;

    }

}


/* ============================================================
   LOAD BASIC INFORMATION
   ============================================================ */

async function loadBasicInformation() {

    if (
        !currentTripId
    ) {

        return null;

    }


    try {

        const result =
            await API.getBasicTrip(
                currentTripId
            );


        if (
            result &&
            result.basic_information
        ) {

            basicTripData =
                result.basic_information;

        } else {

            basicTripData =
                result;

        }


        if (basicTripData) {

            localStorage.setItem(

                STORAGE_KEYS.basicTrip,

                JSON.stringify(
                    basicTripData
                )

            );

        }


        return result;

    } catch (error) {

        console.warn(
            "Unable to load saved basic trip:",
            error
        );


        return null;

    }

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


    const userInput =
        value(
            "user_preferences"
        );


    if (!userInput) {

        setMessage(
            "plannerError",
            "Please describe what you want from your trip."
        );

        return;

    }


    const button =
        document.getElementById(
            "startTripButton"
        );


    tripStartInProgress =
        true;


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
        "Wanderlust is finding 3 destinations that match your request..."
    );


    chatSetTyping(
        true
    );


    try {

        /* ----------------------------------------------------
           Make sure basic information exists.
        ---------------------------------------------------- */

        if (!currentTripId) {

            const saved =
                await saveBasicInformation();


            if (!saved) {

                throw new Error(
                    "Please complete the basic trip information first."
                );

            }

        }


        /* ----------------------------------------------------
           Backend pipeline:

               app.py
                 ↓
               main.py
                 ↓
               MoodAgent
                 ↓
               TravelAgent
                 ↓
               Gemini → EXACTLY 3
                 ↓
               ResearchAgent
                 ↓
               Worker 1/2/3
                 ↓
               Gemma verification
                 ↓
               Pexels
        ---------------------------------------------------- */

        currentTrip =
            await API.startTrip(

                currentTripId,

                userInput

            );


        if (
            !currentTrip
        ) {

            throw new Error(
                "The backend returned no trip data."
            );

        }


        /* ----------------------------------------------------
           Render the three final enriched options.
        ---------------------------------------------------- */

        renderTripResults(
            currentTrip
        );


        updateBudgetUI();


        /* ----------------------------------------------------
           Chat response.
        ---------------------------------------------------- */

        chatSetTyping(
            false
        );


        renderChatRecommendations(
            currentTrip
        );


        /* ----------------------------------------------------
           Show results.
        ---------------------------------------------------- */

        const resultsSection =
            document.getElementById(
                "resultsSection"
            );


        if (resultsSection) {

            resultsSection.style.display =
                "block";

        }


        scrollToResultsIfNeeded();

    } catch (error) {

        console.error(
            "START TRIP ERROR:",
            error
        );


        chatSetTyping(
            false
        );


        chatAddAssistant(

            "I couldn't complete the trip search.\n\n" +
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


        setMessage(
            "plannerLoading",
            "",
            false
        );

    }

}


/* ============================================================
   GET THREE DESTINATIONS
   ============================================================ */

function getCandidates(
    trip
) {

    if (
        trip &&
        Array.isArray(
            trip.travel_options
        )
    ) {

        return trip.travel_options;

    }


    if (
        trip &&
        Array.isArray(
            trip.destinations
        )
    ) {

        return trip.destinations;

    }


    if (
        trip &&
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
        trip &&
        Array.isArray(
            trip.candidates
        )
    ) {

        return trip.candidates;

    }


    return [];

}


/* ============================================================
   CHAT HELPERS
   ============================================================ */

function chatAddAssistant(
    text
) {

    if (
        typeof window
            .wanderlustAddAssistantMessage
        ===
        "function"
    ) {

        return window
            .wanderlustAddAssistantMessage(
                text
            );

    }


    return null;

}


function chatSetTyping(
    show
) {

    if (
        typeof window
            .wanderlustSetTyping
        ===
        "function"
    ) {

        window
            .wanderlustSetTyping(
                Boolean(
                    show
                )
            );

    }

}


/* ============================================================
   CHAT CANDIDATE FORMAT
   ============================================================ */

function formatChatCandidate(
    candidate,
    index
) {

    const name =
        candidate?.name ||
        candidate?.destination ||
        "Unknown destination";


    const country =
        candidate?.country ||
        "";


    const reason =
        candidate?.reason ||
        "This destination matches your travel request.";


    return (

        `${index + 1}. ${name}` +

        (
            country
                ? `, ${country}`
                : ""
        ) +

        `\n${reason}`

    );

}


/* ============================================================
   CHAT RECOMMENDATIONS
   ============================================================ */

function renderChatRecommendations(
    trip
) {

    const candidates =
        getCandidates(
            trip
        );


    if (
        candidates.length !== 3
    ) {

        return;

    }


    chatAddAssistant(

        "I've finished finding the destinations that best match your request:\n\n" +

        candidates
            .map(
                formatChatCandidate
            )
            .join(
                "\n\n"
            ) +

        "\n\nYou can select one of the three options below, or tell me what you'd like to change."

    );

}


/* ============================================================
   RESULTS
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
        candidates.length !== 3
    ) {

        grid.innerHTML = `

            <div class="panel">

                <strong>
                    Unable to display the recommendations.
                </strong>

                <p>
                    The travel system did not return
                    exactly three destinations.
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
                candidate?.name ||
                candidate?.destination ||
                "Unknown destination";


            const country =
                candidate?.country ||
                "";


            const reason =
                candidate?.reason ||
                "No additional explanation was provided.";


            const description =
                candidate?.description ||
                "";


            const image =
                candidate?.image?.image_url ||
                "";


            const photographer =
                candidate?.image?.photographer ||
                "";


            card.innerHTML = `

                ${
                    image
                        ? `
                            <div
                                class="result-card-image"
                                style="
                                    width:100%;
                                    height:210px;
                                    overflow:hidden;
                                    border-radius:14px 14px 0 0;
                                    background:#e2e8f0;
                                "
                            >

                                <img
                                    src="${escapeHtml(image)}"
                                    alt="${escapeHtml(name)}"
                                    style="
                                        width:100%;
                                        height:100%;
                                        object-fit:cover;
                                        display:block;
                                    "
                                    loading="lazy"
                                >

                            </div>
                        `
                        : ""
                }


                <div class="result-card-body">

                    <span class="result-number">
                        ${index + 1}
                    </span>


                    <h3>
                        ${escapeHtml(
                            name
                        )}
                    </h3>


                    ${
                        country
                            ? `
                                <div class="result-country">
                                    ${escapeHtml(
                                        country
                                    )}
                                </div>
                            `
                            : ""
                    }


                    ${
                        description
                            ? `
                                <p
                                    style="
                                        line-height:1.6;
                                        margin:12px 0;
                                    "
                                >
                                    ${escapeHtml(
                                        description
                                    )}
                                </p>
                            `
                            : ""
                    }


                    <p class="result-reason">

                        ${escapeHtml(
                            reason
                        )}

                    </p>


                    ${
                        photographer
                            ? `
                                <div
                                    style="
                                        font-size:11px;
                                        color:var(--muted);
                                        margin-top:8px;
                                    "
                                >
                                    Photo by
                                    ${escapeHtml(
                                        photographer
                                    )}
                                    on Pexels
                                </div>
                            `
                            : ""
                    }


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
                            data-action="select"
                        >
                            SELECT THIS TRIP
                        </button>


                        <button
                            class="btn btn-light"
                            type="button"
                            data-action="details"
                        >
                            DETAILS
                        </button>

                    </div>

                </div>

            `;


            const selectButton =
                card.querySelector(
                    '[data-action="select"]'
                );


            const detailsButton =
                card.querySelector(
                    '[data-action="details"]'
                );


            if (selectButton) {

                selectButton.addEventListener(
                    "click",
                    () =>
                        selectTrip(
                            index
                        )
                );

            }


            if (detailsButton) {

                detailsButton.addEventListener(
                    "click",
                    () =>
                        showDestination(
                            index
                        )
                );

            }


            grid.appendChild(
                card
            );

        }
    );

}


/* ============================================================
   SHOW DESTINATION DETAILS
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


    if (
        index < 0 ||
        index >= candidates.length
    ) {

        return;

    }


    const candidate =
        candidates[index];


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


    const map =
        document.getElementById(
            "modalMap"
        );


    const name =
        candidate?.name ||
        candidate?.destination ||
        "Destination";


    if (title) {

        title.textContent =
            name;

    }


    if (country) {

        country.textContent =
            candidate?.country ||
            "";

    }


    if (reason) {

        reason.textContent =
            candidate?.description ||
            candidate?.reason ||
            "";

    }


    if (map) {

        const research =
            candidate?.research ||
            {};


        const strengths =
            Array.isArray(
                research.strengths
            )
                ? research.strengths
                : [];


        const limitations =
            Array.isArray(
                research.limitations
            )
                ? research.limitations
                : [];


        const evidence =
            Array.isArray(
                research.evidence
            )
                ? research.evidence
                : [];


        let html =
            "";


        if (
            strengths.length
        ) {

            html += `

                <div class="map-item">

                    <strong>
                        Strengths
                    </strong>

                    <ul>
                        ${
                            strengths
                                .map(
                                    item =>
                                        `<li>${escapeHtml(item)}</li>`
                                )
                                .join("")
                        }
                    </ul>

                </div>

            `;

        }


        if (
            limitations.length
        ) {

            html += `

                <div class="map-item">

                    <strong>
                        Limitations
                    </strong>

                    <ul>
                        ${
                            limitations
                                .map(
                                    item =>
                                        `<li>${escapeHtml(item)}</li>`
                                )
                                .join("")
                        }
                    </ul>

                </div>

            `;

        }


        if (
            evidence.length
        ) {

            html += `

                <div class="map-item">

                    <strong>
                        Research evidence
                    </strong>

                    <ul>
                        ${
                            evidence
                                .slice(
                                    0,
                                    5
                                )
                                .map(
                                    item =>
                                        `<li>${escapeHtml(
                                            typeof item === "string"
                                                ? item
                                                : JSON.stringify(item)
                                        )}</li>`
                                )
                                .join("")
                        }
                    </ul>

                </div>

            `;

        }


        if (!html) {

            html = `

                <div class="map-item">

                    Detailed research is available
                    in the destination recommendation.

                </div>

            `;

        }


        map.innerHTML =
            html;

    }


    modal.classList.add(
        "open"
    );

}


/* ============================================================
   CLOSE DESTINATION MODAL
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
   SELECT DESTINATION
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
            "Invalid destination selection."
        );

        return;

    }


    const selected =
        candidates[index];


    const selectedName =
        selected?.name ||
        selected?.destination ||
        "Selected destination";


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
            selectedName;

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


    try {

        currentTrip =
            await API.selectTrip(

                currentTrip.trip_id,

                index

            );


        renderSelectedTrip(
            currentTrip
        );


        updateBudgetUI();


        if (panel) {

            panel.scrollIntoView({

                behavior:
                    "smooth",

                block:
                    "start"

            });

        }

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
   RENDER SELECTED TRIP
   ============================================================ */

function renderSelectedTrip(
    trip
) {

    const selected =
        trip?.selected_trip ||
        {};


    const details =
        selected?.details ||
        selected;


    const costs =
        Array.isArray(
            details?.costs
        )
            ? details.costs
            : [];


    const budget =
        trip?.budget ||
        {};


    let html = `

        <div class="option-meta">

            <div class="meta-box">

                <small>
                    Status
                </small>

                <strong>
                    ${escapeHtml(
                        trip?.status ||
                        "selected"
                    )}
                </strong>

            </div>


            <div class="meta-box">

                <small>
                    Estimated Total
                </small>

                <strong>
                    ${formatMoney(
                        details?.total_estimated_cost ??
                        budget?.estimated_total
                    )}
                </strong>

            </div>


            <div class="meta-box">

                <small>
                    Estimated Remaining
                </small>

                <strong>
                    ${formatMoney(
                        budget?.estimated_remaining
                    )}
                </strong>

            </div>

        </div>

    `;


    if (
        costs.length
    ) {

        html += `

            <div
                style="
                    margin-top:17px;
                "
            >

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
        Array.isArray(
            details?.unknown_costs
        ) &&
        details.unknown_costs.length
    ) {

        html += `

            <div
                style="
                    margin-top:15px;
                "
            >

                <h4>
                    Costs requiring verification
                </h4>

                <ul>

                    ${
                        details.unknown_costs
                            .map(
                                item =>
                                    `<li>${escapeHtml(item)}</li>`
                            )
                            .join("")
                    }

                </ul>

            </div>

        `;

    }


    if (
        details?.within_budget === false
        ||
        budget?.estimates_affordable === false
    ) {

        html += `

            <div
                class="error"
                style="display:block;"
            >

                This trip currently exceeds
                the available budget.

            </div>

        `;

    } else {

        html += `

            <div
                class="success"
                style="display:block;"
            >

                This trip currently fits
                within the available budget.

            </div>

        `;

    }


    const notes =
        Array.isArray(
            details?.notes
        )
            ? details.notes
            : [];


    if (
        notes.length
    ) {

        html += `

            <div
                style="
                    margin-top:15px;
                "
            >

                <h4>
                    Notes
                </h4>

                <ul>

                    ${
                        notes
                            .map(
                                note =>
                                    `<li>${escapeHtml(note)}</li>`
                            )
                            .join("")
                    }

                </ul>

            </div>

        `;

    }


    if (
        trip?.map_data &&
        Array.isArray(
            trip.map_data
        ) &&
        trip.map_data.length
    ) {

        html += `

            <div
                style="
                    margin-top:15px;
                "
            >

                <h4>
                    Location
                </h4>

                <p
                    style="
                        color:var(--muted);
                        font-size:13px;
                    "
                >

                    Geographic information
                    is available for this destination.

                </p>

            </div>

        `;

    }


    if (
        document.getElementById(
            "selectedTripContent"
        )
    ) {

        document.getElementById(
            "selectedTripContent"
        ).innerHTML =
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
        "selected"
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
                currentTrip.trip_id
            );


        renderSelectedTrip(
            currentTrip
        );


        updateBudgetUI();


        chatAddAssistant(

            `Your trip to ${
                escapeHtml(
                    currentTrip.selected_destination ||
                    "the selected destination"
                )
            } has been confirmed.`

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
        !currentTrip?.trip_id
    ) {

        chatAddAssistant(
            "There is no active trip to update."
        );

        return;

    }


    const clean =
        String(
            changeRequest || ""
        ).trim();


    if (!clean) {

        return;

    }


    if (
        tripChatProcessing
    ) {

        return;

    }


    tripChatProcessing =
        true;


    chatSetTyping(
        true
    );


    try {

        currentTrip =
            await API.updateTrip(

                currentTrip.trip_id,

                clean

            );


        renderTripResults(
            currentTrip
        );


        updateBudgetUI();


        chatSetTyping(
            false
        );


        chatAddAssistant(

            "I've updated your trip options based on your request. " +
            "The three new destinations are shown below."

        );


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
            "UPDATE TRIP ERROR:",
            error
        );


        chatSetTyping(
            false
        );


        chatAddAssistant(

            "I couldn't update the trip:\n\n" +
            (
                error.message ||
                "Unknown error."
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
                budget.total_budget
            );

    }


    if (spentElement) {

        spentElement.textContent =
            formatMoney(
                budget.spent
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
                budget.estimated_total
            );

    }


    const progress =
        document.getElementById(
            "budgetProgress"
        );


    if (progress) {

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
                    ) *
                    100
                )

                : 0;


        progress.style.width =
            `${percentage}%`;

    }


    const summary =
        document.getElementById(
            "budgetSummary"
        );


    if (summary) {

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
                    ) *
                    100
                )

                : 0;


        summary.textContent =
            `${percentage.toFixed(1)}% of the budget would be used if the current estimate were committed.`;

    }

}


/* ============================================================
   RANDOM DESTINATIONS
   ============================================================ */

async function loadRandomDestination() {

    const container =
        document.getElementById(
            "randomDestination"
        );


    if (!container) {

        return;

    }


    container.innerHTML = `

        <div
            class="loading"
            style="display:block;"
        >

            Loading a destination...

        </div>

    `;


    try {

        const result =
            await API.randomDestinations(
                1
            );


        const destinations =
            result?.destinations ||
            [];


        if (!destinations.length) {

            throw new Error(
                "No destination was returned."
            );

        }


        const destination =
            destinations[0];


        container.innerHTML = `

            <article class="destination-card">

                ${
                    destination.image_url
                        ? `
                            <img
                                src="${escapeHtml(
                                    destination.image_url
                                )}"
                                alt="${escapeHtml(
                                    destination.name ||
                                    "Destination"
                                )}"
                                style="
                                    width:100%;
                                    height:260px;
                                    object-fit:cover;
                                    border-radius:14px;
                                "
                            >
                        `
                        : ""
                }


                <h2>

                    ${escapeHtml(
                        destination.name ||
                        "Destination"
                    )}

                </h2>


                <div class="result-country">

                    ${escapeHtml(
                        destination.country ||
                        ""
                    )}

                </div>


                ${
                    destination.description
                        ? `
                            <p>
                                ${escapeHtml(
                                    destination.description
                                )}
                            </p>
                        `
                        : ""
                }

            </article>

        `;

    } catch (error) {

        container.innerHTML = `

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

        const result =
            await API.request(
                "/api/destinations/home",
                "GET"
            );


        const destinations =
            Array.isArray(
                result
            )
                ? result
                : (
                    result?.destinations ||
                    []
                );


        container.innerHTML =
            "";


        destinations.forEach(
            destination => {

                const card =
                    document.createElement(
                        "article"
                    );


                card.className =
                    "destination-card";


                card.innerHTML = `

                    ${
                        destination.image_url
                            ? `
                                <img
                                    src="${escapeHtml(
                                        destination.image_url
                                    )}"
                                    alt="${escapeHtml(
                                        destination.name ||
                                        "Destination"
                                    )}"
                                    style="
                                        width:100%;
                                        height:180px;
                                        object-fit:cover;
                                        border-radius:12px;
                                    "
                                >
                            `
                            : ""
                    }


                    <h3>

                        ${escapeHtml(
                            destination.name ||
                            "Destination"
                        )}

                    </h3>


                    <div class="result-country">

                        ${escapeHtml(
                            destination.country ||
                            ""
                        )}

                    </div>

                `;


                container.appendChild(
                    card
                );

            }
        );

    } catch (error) {

        console.warn(
            "HOME DESTINATIONS ERROR:",
            error
        );

    }

}


/* ============================================================
   SEARCH
   ============================================================ */

function initializeSearch() {

    const searchBox =
        document.getElementById(
            "searchBox"
        );


    if (!searchBox) {

        return;

    }


    searchBox.addEventListener(
        "input",
        event => {

            const query =
                String(
                    event.target.value ||
                    ""
                )
                    .toLowerCase()
                    .trim();


            document
                .querySelectorAll(
                    ".destination-card"
                )
                .forEach(
                    card => {

                        card.style.display =

                            !query ||
                            card.textContent
                                .toLowerCase()
                                .includes(
                                    query
                                )

                                ? ""
                                : "none";

                    }
                );

        }
    );

}


/* ============================================================
   TRIP CHAT BACKEND
   ============================================================ */

function initializeTripChatBackend() {

    const chatForm =
        document.getElementById(
            "tripChatForm"
        );


    const chatInput =
        document.getElementById(
            "tripChatInput"
        );


    if (
        !chatForm ||
        !chatInput
    ) {

        return;

    }


    document.addEventListener(

        "wanderlust:chat-message",

        event => {

            const message =
                event?.detail?.message;


            if (
                !message
            ) {

                return;

            }


            const clean =
                String(
                    message
                ).trim();


            if (!clean) {

                return;

            }


            /*
             * The initial user message is already being
             * handled by /api/trip/start.
             */

            if (
                tripStartInProgress
            ) {

                return;

            }


            /*
             * After the initial search, every new chat
             * message becomes an update request.
             */

            updateTrip(
                clean
            );

        }

    );

}


/* ============================================================
   CHAT CLOSE
   ============================================================ */

window.wanderlustCloseTripChat =
function () {

    const scene =
        document.getElementById(
            "tripChatScene"
        );


    const panel =
        document.getElementById(
            "preferencePanel"
        );


    const messages =
        document.getElementById(
            "tripChatMessages"
        );


    if (scene) {

        scene.classList.remove(
            "open"
        );

    }


    if (panel) {

        panel.style.display =
            "";

    }


    if (messages) {

        messages.innerHTML =
            "";

    }


    chatStarted =
        false;


    tripChatProcessing =
        false;

};


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


    if (!currentTrip) {

        return;

    }


    currentTrip.selected_trip =
        null;


    currentTrip.selected_destination =
        null;


    currentTrip.status =
        "awaiting_selection";

}


/* ============================================================
   CANCEL CURRENT TRIP
   ============================================================ */

async function cancelCurrentTrip() {

    if (
        !currentTrip?.trip_id
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
                currentTrip.trip_id
            );


        const panel =
            document.getElementById(
                "selectionPanel"
            );


        if (panel) {

            panel.style.display =
                "none";

        }


        updateBudgetUI();


        chatAddAssistant(
            "The current trip planning session has been cancelled."
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
   DELETE CURRENT TRIP
   ============================================================ */

async function deleteCurrentTrip() {

    if (
        !currentTrip?.trip_id
    ) {

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
            currentTrip.trip_id
        );


        currentTrip =
            null;


        currentTripId =
            null;


        basicTripData =
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
   RESET PLANNER
   ============================================================ */

function resetPlanner() {

    const results =
        document.getElementById(
            "resultsSection"
        );


    const selection =
        document.getElementById(
            "selectionPanel"
        );


    if (results) {

        results.style.display =
            "none";

    }


    if (selection) {

        selection.style.display =
            "none";

    }


    currentTrip =
        null;


    tripStartInProgress =
        false;


    tripChatProcessing =
        false;


    window.scrollTo({

        top:
            0,

        behavior:
            "smooth"

    });

}


/* ============================================================
   STATUS
   ============================================================ */

async function refreshStatus() {

    if (
        !currentTripId
    ) {

        return;

    }


    try {

        currentTrip =
            await API.getTripStatus(
                currentTripId
            );


        updateBudgetUI();


        if (
            currentTrip.status ===
            "awaiting_selection"
        ) {

            renderTripResults(
                currentTrip
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


        if (
            currentTrip.status ===
            "selected"
        ) {

            renderSelectedTrip(
                currentTrip
            );

        }

    } catch (error) {

        console.warn(
            "STATUS ERROR:",
            error
        );

    }

}


/* ============================================================
   FORM INITIALIZATION
   ============================================================ */

function initializeForms() {

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


    const tripForm =
        document.getElementById(
            "tripForm"
        );


    if (tripForm) {

        tripForm.addEventListener(
            "submit",
            event => {

                event.preventDefault();

                startTrip();

            }
        );

    }


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
   INITIALIZATION
   ============================================================ */

document.addEventListener(
    "DOMContentLoaded",
    async () => {

        console.log(
            "Wanderlust frontend initializing..."
        );


        /* ----------------------------------------------------
           Initialize UI.
        ---------------------------------------------------- */

        initializeNavigation();

        initializeForms();

        initializeSearch();

        initializeModal();

        initializeTripChatBackend();


        /* ----------------------------------------------------
           Recover trip ID.
        ---------------------------------------------------- */

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

        }


        /* ----------------------------------------------------
           Recover cached basic information.
        ---------------------------------------------------- */

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


        /* ----------------------------------------------------
           Flask health.
        ---------------------------------------------------- */

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


        /* ----------------------------------------------------
           Load saved basic trip.
        ---------------------------------------------------- */

        if (
            currentTripId
        ) {

            await loadBasicInformation();

        }


        /* ----------------------------------------------------
           Home page.
        ---------------------------------------------------- */

        await loadHomeDestinations();


        console.log(
            "Wanderlust frontend initialized."
        );

    }
);