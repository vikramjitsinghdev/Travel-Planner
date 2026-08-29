/* ============================================================
   WANDERLUST
   FLASK FRONTEND CONTROLLER
   ============================================================

   Architecture:

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
       +----+----+----+----+
       |    |    |    |    |
      Mood Travel Research Map Budget


   Flask API endpoints:

       GET  /api/health

       POST /api/trip/start
       POST /api/trip/update
       POST /api/trip/select
       POST /api/trip/confirm
       POST /api/trip/cancel
       POST /api/trip/status
       POST /api/trip/delete
*/


/* ============================================================
   GLOBAL TRIP STATE
   ============================================================ */

let currentTrip = null;


/* ============================================================
   API CONNECTOR
   ============================================================ */

const API = {

    async request(
        endpoint,
        method = "POST",
        data = null
    ) {

        const options = {
            method: method,
            headers: {}
        };


        /*
         * Only attach JSON headers/body when
         * data is actually being sent.
         */

        if (data !== null) {

            options.headers[
                "Content-Type"
            ] = "application/json";

            options.body = JSON.stringify(
                data
            );
        }


        let response;

        try {

            response = await fetch(
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

            payload = await response.json();

        } catch {

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


    /* --------------------------------------------------------
       HEALTH
    -------------------------------------------------------- */

    health() {

        return this.request(
            "/api/health",
            "GET"
        );
    },


    /* --------------------------------------------------------
       START TRIP
    -------------------------------------------------------- */

    startTrip(tripData) {

        return this.request(
            "/api/trip/start",
            "POST",
            tripData
        );
    },


    /* --------------------------------------------------------
       UPDATE TRIP
    -------------------------------------------------------- */

    updateTrip(
        tripId,
        changeRequest
    ) {

        return this.request(
            "/api/trip/update",
            "POST",
            {
                trip_id: tripId,
                change_request: changeRequest
            }
        );
    },


    /* --------------------------------------------------------
       SELECT TRIP
    -------------------------------------------------------- */

    selectTrip(
        tripId,
        selectedIndex
    ) {

        return this.request(
            "/api/trip/select",
            "POST",
            {
                trip_id: tripId,
                selected_index: selectedIndex
            }
        );
    },


    /* --------------------------------------------------------
       CONFIRM TRIP
    -------------------------------------------------------- */

    confirmTrip(tripId) {

        return this.request(
            "/api/trip/confirm",
            "POST",
            {
                trip_id: tripId
            }
        );
    },


    /* --------------------------------------------------------
       CANCEL TRIP
    -------------------------------------------------------- */

    cancelTrip(tripId) {

        return this.request(
            "/api/trip/cancel",
            "POST",
            {
                trip_id: tripId
            }
        );
    },


    /* --------------------------------------------------------
       GET TRIP STATUS
    -------------------------------------------------------- */

    getTripStatus(tripId) {

        return this.request(
            "/api/trip/status",
            "POST",
            {
                trip_id: tripId
            }
        );
    },


    /* --------------------------------------------------------
       DELETE TRIP
    -------------------------------------------------------- */

    deleteTrip(tripId) {

        return this.request(
            "/api/trip/delete",
            "POST",
            {
                trip_id: tripId
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

    element.textContent = message;

    element.style.display =
        visible ? "block" : "none";
}


function escapeHtml(text) {

    return String(
        text ?? ""
    )
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


function formatMoney(number) {

    const amount =
        Number(number || 0);

    return amount.toLocaleString(
        "en-CA",
        {
            style: "currency",
            currency: "CAD"
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
                button.dataset.page === pageName
            );

        });


    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });
}


function initializeNavigation() {

    document
        .querySelectorAll(".nav-button")
        .forEach(button => {

            button.addEventListener(
                "click",
                () => {

                    showPage(
                        button.dataset.page
                    );

                }
            );

        });

}


/* ============================================================
   DOMESTIC COUNTRY DETECTION
   ============================================================ */

function detectDepartureCountry(text) {

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
        const [needle, country]
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


    /*
     * Canadian province/territory
     * abbreviations.
     */

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


function updateCountryField() {

    const scope =
        document.querySelector(
            'input[name="trip_scope"]:checked'
        )?.value;


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


    /*
     * Domestic trip + country detected:
     *
     * Automatically use departure country.
     *
     * Example:
     *
     * Saint John, NB, Canada
     *
     * becomes:
     *
     * country = Canada
     */

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

            hint.textContent = "";

        }

    }

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
   BUILD TRIP DATA
   ============================================================ */

function buildTripData() {

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
            ),

        user_preferences:
            value(
                "user_preferences"
            )

    };

}


/* ============================================================
   VALIDATE TRIP DATA
   ============================================================ */

function validateTripData(data) {

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


    /*
     * Most important check:
     *
     * user_preferences MUST be a string.
     */

    if (
        typeof data.user_preferences !==
        "string"
    ) {

        return (
            "Trip preferences must be entered as text."
        );

    }


    if (
        !data.user_preferences.trim()
    ) {

        return (
            "Please describe what you want from the trip."
        );

    }


    /*
     * Domestic trips need a country.
     *
     * Normally this is automatically detected.
     */

    if (
        data.trip_scope === "domestic" &&
        !data.country
    ) {

        return (
            "For domestic travel, the country must be known. Enter it in your departure location or country field."
        );

    }


    return null;

}


/* ============================================================
   START TRIP
   ============================================================ */

async function startTrip() {

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


    const data =
        buildTripData();


    const validationError =
        validateTripData(
            data
        );


    if (validationError) {

        setMessage(
            "plannerError",
            validationError
        );

        return;

    }


    const button =
        document.getElementById(
            "startTripButton"
        );


    if (button) {

        button.disabled = true;

        button.textContent =
            "PLANNING...";

    }


    setMessage(
        "plannerLoading",
        "AI systems are processing your trip..."
    );


    try {

        /*
         * IMPORTANT:
         *
         * This is now the only place where
         * the frontend starts the backend workflow.
         */

        currentTrip =
            await API.startTrip(
                data
            );


        renderTripResults(
            currentTrip
        );


        const resultsSection =
            document.getElementById(
                "resultsSection"
            );


        if (resultsSection) {

            resultsSection.style.display =
                "block";

        }


        updateBudgetUI();


        setMessage(
            "plannerLoading",
            "",
            false
        );


        setTimeout(
            () => {

                if (resultsSection) {

                    resultsSection.scrollIntoView({
                        behavior: "smooth"
                    });

                }

            },
            100
        );


    } catch (error) {

        console.error(
            "START TRIP ERROR:",
            error
        );


        setMessage(
            "plannerError",
            error.message ||
            "Unable to start the travel planning process."
        );


        setMessage(
            "plannerLoading",
            "",
            false
        );


    } finally {

        if (button) {

            button.disabled = false;

            button.textContent =
                "FIND TRIPS →";

        }

    }

}


/* ============================================================
   GET CANDIDATES
   ============================================================ */

function getCandidates(trip) {

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

        return trip.candidates.map(
            name => ({

                name: name,

                country: "",

                reason: ""

            })
        );

    }


    return [];

}


/* ============================================================
   RENDER CANDIDATE RESULTS
   ============================================================ */

function renderTripResults(trip) {

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


    grid.innerHTML = "";


    if (
        !candidates.length
    ) {

        grid.innerHTML = `
            <div class="panel">
                <strong>
                    No destinations were returned.
                </strong>

                <p style="color:var(--muted);">
                    Try modifying your trip requirements
                    and search again.
                </p>
            </div>
        `;

        return;

    }


    candidates.forEach(
        (candidate, index) => {

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
                            candidate.name
                        )}
                    </h3>


                    <div class="result-country">

                        ${escapeHtml(
                            candidate.country || ""
                        )}

                    </div>


                    <p class="result-reason">

                        ${escapeHtml(
                            candidate.reason ||
                            "No reason provided."
                        )}

                    </p>


                    <div class="option-meta">

                        <div class="meta-box">

                            <small>
                                Trip
                            </small>

                            <strong>

                                ${escapeHtml(
                                    trip
                                        ?.trip_information
                                        ?.trip_scope ||
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
                                    trip
                                        ?.trip_information
                                        ?.travelers ||
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
                                    trip
                                        ?.trip_information
                                        ?.duration_days ||
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
                            onclick="selectTrip(${index})"
                        >
                            SELECT THIS TRIP
                        </button>


                        <button
                            class="btn btn-light"
                            onclick="showDestination(${index})"
                        >
                            DETAILS
                        </button>

                    </div>

                </div>
            `;


            grid.appendChild(
                card
            );

        }
    );


    /*
     * Display AI comparison if main.py
     * returned one.
     */

    if (
        trip &&
        trip.travel_options
    ) {

        const panel =
            document.createElement(
                "div"
            );


        panel.className =
            "panel final-panel";


        panel.style.gridColumn =
            "1 / -1";


        panel.innerHTML = `

            <h3 style="margin-top:0;">
                AI Comparison
            </h3>

            <pre>
${escapeHtml(
    formatAIResponse(
        trip.travel_options
    )
)}
            </pre>

        `;


        grid.appendChild(
            panel
        );

    }

}


/* ============================================================
   FORMAT AI RESPONSE
   ============================================================ */

function formatAIResponse(
    response
) {

    if (
        typeof response ===
        "string"
    ) {

        return response;

    }


    try {

        return JSON.stringify(
            response,
            null,
            2
        );

    } catch {

        return String(
            response
        );

    }

}


/* ============================================================
   SELECT DESTINATION
   ============================================================ */

async function selectTrip(index) {

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


    const selectionPanel =
        document.getElementById(
            "selectionPanel"
        );


    const selectedName =
        candidates[index].name;


    if (selectionPanel) {

        selectionPanel.style.display =
            "block";

    }


    document.getElementById(
        "selectedTripName"
    ).textContent =
        selectedName;


    document.getElementById(
        "selectedTripContent"
    ).innerHTML = `

        <div
            class="loading"
            style="display:block;"
        >
            Calculating detailed trip costs...
        </div>

    `;


    try {

        /*
         * Backend:
         *
         * main.select_trip()
         *
         * will research/calculate the
         * detailed costs for the selected
         * destination.
         */

        currentTrip =
            await API.selectTrip(
                currentTrip.trip_id,
                index
            );


        renderSelectedTrip(
            currentTrip
        );


        updateBudgetUI();


        /*
         * Scroll to the detailed
         * selection panel.
         */

        if (selectionPanel) {

            selectionPanel.scrollIntoView({
                behavior: "smooth"
            });

        }


    } catch (error) {

        console.error(
            "SELECT TRIP ERROR:",
            error
        );


        document.getElementById(
            "selectedTripContent"
        ).innerHTML = `

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
   RENDER SELECTED TRIP
   ============================================================ */

function renderSelectedTrip(
    trip
) {

    const selectedTrip =
        trip.selected_trip ||
        {};


    const costs =
        Array.isArray(
            selectedTrip.costs
        )
            ? selectedTrip.costs
            : [];


    const budget =
        trip.budget ||
        {};


    let html = "";


    html += `

        <div class="option-meta">

            <div class="meta-box">

                <small>
                    Status
                </small>

                <strong>
                    ${escapeHtml(
                        trip.status ||
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
                    Estimated Remaining
                </small>

                <strong>
                    ${formatMoney(
                        budget.estimated_remaining
                    )}
                </strong>

            </div>

        </div>

    `;


    /*
     * Detailed costs.
     */

    if (costs.length) {

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

    } else {

        html += `

            <div
                class="panel"
                style="
                    margin-top:17px;
                    background:#f8fafc;
                "
            >

                <strong>
                    No detailed cost items were returned.
                </strong>

                <p
                    style="
                        font-size:12px;
                        color:var(--muted);
                    "
                >
                    The backend should return
                    selected_trip.costs for detailed
                    budget processing.
                </p>

            </div>

        `;

    }


    /*
     * Budget affordability.
     */

    if (
        budget.estimates_affordable ===
        false
    ) {

        html += `

            <div
                class="error"
                style="display:block;"
            >

                This estimated trip exceeds
                the available budget.

                Confirmation will be rejected
                by the backend.

            </div>

        `;

    } else {

        html += `

            <div
                class="success"
                style="display:block;"
            >

                This estimated trip currently
                fits within the available budget.

            </div>

        `;

    }


    document.getElementById(
        "selectedTripContent"
    ).innerHTML =
        html;

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
            "A destination must be selected before the trip can be confirmed."
        );

        return;

    }


    const button =
        document.getElementById(
            "confirmTripButton"
        );


    if (button) {

        button.disabled = true;

        button.textContent =
            "CONFIRMING...";

    }


    try {

        /*
         * This is the point where
         * temporary estimated costs
         * become committed budget
         * expenses.
         */

        currentTrip =
            await API.confirmTrip(
                currentTrip.trip_id
            );


        renderSelectedTrip(
            currentTrip
        );


        updateBudgetUI();


        alert(
            "Trip confirmed. The temporary estimates have been committed to the budget."
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

            button.disabled = false;

            button.textContent =
                "CONFIRM TRIP";

        }

    }

}


/* ============================================================
   DESTINATION DETAILS
   ============================================================ */

function showDestination(index) {

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


    document.getElementById(
        "modalTitle"
    ).textContent =
        candidate.name;


    document.getElementById(
        "modalCountry"
    ).textContent =
        candidate.country ||
        "";


    document.getElementById(
        "modalReason"
    ).textContent =
        candidate.reason ||
        "No additional candidate description was returned.";


    const mapList =
        document.getElementById(
            "modalMap"
        );


    /*
     * Match the candidate with
     * MapTiler information.
     */

    const matchingMap =
        Array.isArray(
            currentTrip.map_data
        )
            ? currentTrip.map_data.find(
                item => {

                    return String(
                        item.destination ||
                        ""
                    )
                        .toLowerCase()
                        .includes(
                            String(
                                candidate.name ||
                                ""
                            )
                                .toLowerCase()
                        );

                }
            )
            : null;


    if (
        matchingMap
    ) {

        const coords =
            matchingMap.coordinates ||
            {};


        mapList.innerHTML = `

            <div class="map-item">

                <strong>
                    MapTiler location
                </strong>

                <div class="coordinates">

                    Latitude:
                    ${escapeHtml(
                        coords.latitude
                    )}

                    <br>

                    Longitude:
                    ${escapeHtml(
                        coords.longitude
                    )}

                </div>

            </div>

        `;

    } else {

        mapList.innerHTML = `

            <div class="map-item">

                Geographic information was not
                returned for this candidate.

            </div>

        `;

    }


    document.getElementById(
        "destinationModal"
    ).classList.add(
        "open"
    );

}


function closeModal() {

    document.getElementById(
        "destinationModal"
    ).classList.remove(
        "open"
    );

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


    if (!currentTrip) {

        return;

    }


    /*
     * This only resets the frontend
     * selection display.
     *
     * It does NOT commit anything
     * to the budget.
     */

    currentTrip.selected_trip =
        null;


    currentTrip.selected_destination =
        null;


    currentTrip.status =
        "awaiting_selection";


    updateBudgetUI();

}


/* ============================================================
   RESET PLANNER
   ============================================================ */

function resetPlanner() {

    const results =
        document.getElementById(
            "resultsSection"
        );


    if (results) {

        results.style.display =
            "none";

    }


    const selection =
        document.getElementById(
            "selectionPanel"
        );


    if (selection) {

        selection.style.display =
            "none";

    }


    currentTrip =
        null;


    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });

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

        alert(
            "There is no active trip to update."
        );

        return;

    }


    if (
        typeof changeRequest !==
        "string" ||
        !changeRequest.trim()
    ) {

        alert(
            "Please enter the changes you want to make."
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
                currentTrip.trip_id,
                changeRequest.trim()
            );


        renderTripResults(
            currentTrip
        );


        updateBudgetUI();


        setMessage(
            "plannerLoading",
            "",
            false
        );


    } catch (error) {

        console.error(
            "UPDATE TRIP ERROR:",
            error
        );


        setMessage(
            "plannerError",
            error.message
        );


        setMessage(
            "plannerLoading",
            "",
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


    document.getElementById(
        "budgetTotal"
    ).textContent =
        formatMoney(
            budget.total_budget
        );


    document.getElementById(
        "budgetSpent"
    ).textContent =
        formatMoney(
            budget.spent
        );


    document.getElementById(
        "budgetRemaining"
    ).textContent =
        formatMoney(
            budget.remaining
        );


    document.getElementById(
        "budgetEstimated"
    ).textContent =
        formatMoney(
            budget.estimated_total
        );


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
                (used / total) * 100,
                100
            )
            : 0;


    document.getElementById(
        "budgetProgress"
    ).style.width =
        percentage + "%";


    document.getElementById(
        "budgetSummary"
    ).textContent =
        `${percentage.toFixed(1)}% of the budget would be used if the current estimate were committed.`;


    const list =
        document.getElementById(
            "budgetExpenses"
        );


    list.innerHTML = "";


    const estimatedCosts =
        Array.isArray(
            budget.estimated_costs
        )
            ? budget.estimated_costs
            : [];


    const expenses =
        Array.isArray(
            budget.expenses
        )
            ? budget.expenses
            : [];


    if (
        !estimatedCosts.length &&
        !expenses.length
    ) {

        list.innerHTML = `

            <div
                style="
                    color:var(--muted);
                    font-size:13px;
                "
            >

                No costs have been recorded yet.

            </div>

        `;

        return;

    }


    /*
     * Temporary estimates.
     */

    estimatedCosts.forEach(
        item => {

            list.insertAdjacentHTML(
                "beforeend",
                `

                <div class="expense">

                    <div class="expense-main">

                        <strong>

                            Estimated:
                            ${escapeHtml(
                                item.description ||
                                "Travel cost"
                            )}

                        </strong>

                        <span>

                            ${escapeHtml(
                                item.category ||
                                "other"
                            )}

                        </span>

                    </div>


                    <strong>

                        ${formatMoney(
                            item.amount
                        )}

                    </strong>

                </div>

                `
            );

        }
    );


    /*
     * Committed expenses.
     */

    expenses.forEach(
        item => {

            list.insertAdjacentHTML(
                "beforeend",
                `

                <div class="expense">

                    <div class="expense-main">

                        <strong>

                            Confirmed:
                            ${escapeHtml(
                                item.description ||
                                "Expense"
                            )}

                        </strong>

                        <span>

                            ${escapeHtml(
                                item.category ||
                                "other"
                            )}

                        </span>

                    </div>


                    <strong>

                        ${formatMoney(
                            item.amount
                        )}

                    </strong>

                </div>

                `
            );

        }
    );

}


/* ============================================================
   GET CURRENT TRIP STATUS
   ============================================================ */

async function refreshStatus() {

    if (
        !currentTrip?.trip_id
    ) {

        showPage(
            "planner"
        );

        return;

    }


    try {

        currentTrip =
            await API.getTripStatus(
                currentTrip.trip_id
            );


        updateBudgetUI();


        if (
            currentTrip.status ===
            "awaiting_selection"
        ) {

            renderTripResults(
                currentTrip
            );

        }


        if (
            currentTrip.status ===
            "awaiting_confirmation"
        ) {

            renderSelectedTrip(
                currentTrip
            );

        }


    } catch (error) {

        console.error(
            "STATUS ERROR:",
            error
        );


        alert(
            error.message
        );

    }

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
            "Cancel this planning session and discard temporary estimates?"
        )
    ) {

        return;

    }


    try {

        currentTrip =
            await API.cancelTrip(
                currentTrip.trip_id
            );


        updateBudgetUI();


        /*
         * Hide selected-trip panel because
         * temporary estimates have been
         * discarded.
         */

        const selectionPanel =
            document.getElementById(
                "selectionPanel"
            );


        if (selectionPanel) {

            selectionPanel.style.display =
                "none";

        }


        alert(
            "Trip cancelled. Temporary estimates were discarded."
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


        updateBudgetUI();


        resetPlanner();


        showPage(
            "home"
        );


        alert(
            "Trip session deleted."
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
                event.target.value
                    .toLowerCase()
                    .trim();


            document
                .querySelectorAll(
                    ".destination-card"
                )
                .forEach(card => {

                    card.style.display =
                        !query ||
                        card.textContent
                            .toLowerCase()
                            .includes(query)
                            ? ""
                            : "none";

                });

        }
    );

}


/* ============================================================
   INITIALIZE DOM EVENTS
   ============================================================ */

function initializeTripForm() {

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
        .forEach(input => {

            input.addEventListener(
                "change",
                updateCountryField
            );

        });


    const form =
        document.getElementById(
            "tripForm"
        );


    if (form) {

        form.addEventListener(
            "submit",
            event => {

                event.preventDefault();

                startTrip();

            }
        );

    }

}


/* ============================================================
   MODAL EVENTS
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
                event.target.id ===
                "destinationModal"
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
    () => {

        initializeNavigation();

        initializeTripForm();

        initializeSearch();

        initializeModal();

        updateCountryField();

        updateBudgetUI();

    }
);