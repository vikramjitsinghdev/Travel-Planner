/* ============================================================
   WANDERLUST — FRONTEND CONTROLLER
   ============================================================ */

let currentTrip = null;
let basicTripData = null;
let currentTripId = null;

const STORAGE_KEYS = {
    tripId: "wanderlust_trip_id",
    basicTrip: "wanderlust_basic_trip"
};


/* ============================================================
   API
   ============================================================ */

const API = {

    async request(endpoint, method = "GET", data = null) {

        const options = {
            method: method,
            headers: {
                "Content-Type": "application/json"
            }
        };

        if (data !== null) {
            options.body = JSON.stringify(data);
        }

        const response = await fetch(endpoint, options);

        let payload;

        try {
            payload = await response.json();
        } catch {
            throw new Error(
                "Flask returned an invalid response."
            );
        }

        if (!response.ok || payload.status !== "success") {
            throw new Error(
                payload.message ||
                "Backend request failed."
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


    /* --------------------------------------------------------
       BASIC INFORMATION
    -------------------------------------------------------- */

    saveBasicTrip(basicInformation) {

        return this.request(
            "/api/trip/basic-info",
            "POST",
            {
                basic_information: basicInformation
            }
        );
    },


    getBasicTrip(tripId) {

        return this.request(
            `/api/trip/basic/${tripId}`,
            "GET"
        );
    },


    /* --------------------------------------------------------
       HOME
    -------------------------------------------------------- */

    homeDestinations() {

        return this.request(
            "/api/destinations/home",
            "GET"
        );
    },


    /* --------------------------------------------------------
       RANDOM DESTINATIONS
    -------------------------------------------------------- */

    randomDestinations(limit = 6) {

        return this.request(
            `/api/destinations/random?limit=${limit}`,
            "GET"
        );
    },


    /* --------------------------------------------------------
       DESTINATION
    -------------------------------------------------------- */

    destination(destinationId) {

        return this.request(
            `/api/destinations/${destinationId}`,
            "GET"
        );
    },


    /* --------------------------------------------------------
       SEARCH
    -------------------------------------------------------- */

    searchDestination(query) {

        return this.request(
            "/api/destinations/search",
            "POST",
            {
                query: String(query).trim()
            }
        );
    },


    /* --------------------------------------------------------
       AI PLANNER
    -------------------------------------------------------- */

    startTrip(tripData) {

        return this.request(
            "/api/trip/start",
            "POST",
            tripData
        );
    },


    updateTrip(tripId, changeRequest) {

        return this.request(
            "/api/trip/update",
            "POST",
            {
                trip_id: tripId,
                change_request: String(
                    changeRequest
                ).trim()
            }
        );
    },


    selectTrip(tripId, selectedIndex) {

        return this.request(
            "/api/trip/select",
            "POST",
            {
                trip_id: tripId,
                selected_index: selectedIndex
            }
        );
    },


    confirmTrip(tripId) {

        return this.request(
            "/api/trip/confirm",
            "POST",
            {
                trip_id: tripId
            }
        );
    },


    cancelTrip(tripId) {

        return this.request(
            "/api/trip/cancel",
            "POST",
            {
                trip_id: tripId
            }
        );
    },


    getTripStatus(tripId) {

        return this.request(
            "/api/trip/status",
            "POST",
            {
                trip_id: tripId
            }
        );
    },


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


function escapeHtml(text) {

    return String(text ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


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
        visible && message
            ? "block"
            : "none";
}


/* ============================================================
   PAGE NAVIGATION
   ============================================================ */

function showPage(pageName) {

    document
        .querySelectorAll(".page")
        .forEach(page => {
            page.classList.remove("active");
        });


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


    target.classList.add("active");


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

function detectDepartureCountry(text) {

    const lower =
        String(text || "").toLowerCase();


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

        if (lower.includes(keyword)) {
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


function getTripScope() {

    return document.querySelector(
        'input[name="trip_scope"]:checked'
    )?.value || "domestic";
}


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

        countryInput.value = detected;

        countryField.style.display = "none";


        if (countryHint) {

            countryHint.textContent =
                "Departure country detected automatically.";

        }

    } else {

        countryField.style.display = "flex";


        if (countryHint) {
            countryHint.textContent = "";
        }
    }
}


/* ============================================================
   BASIC INFORMATION
   ============================================================ */

function buildBasicTripData() {

    const other = value("other");


    return {

        departure_location:
            value("departure_location"),

        trip_scope:
            getTripScope(),

        country:
            value("country") || null,

        region:
            null,

        travelers:
            Number(value("travelers")),

        duration_days:
            Number(value("duration_days")),

        travel_dates:
            value("travel_dates"),

        maximum_total_travel_time:
            value("maximum_total_travel_time") ||
            "no preference",

        maximum_distance:
            value("maximum_distance") ||
            "no preference",

        transportation_preference:
            value("transportation_preference") ||
            "no preference",

        accommodation_preference:
            value("accommodation_preference") ||
            "no preference",

        safety_requirement:
            value("safety_requirement") ||
            "none",

        other:
            other ? [other] : [],

        budget:
            Number(value("budget"))
    };
}


function validateBasicTripData(data) {

    if (!data.departure_location) {

        return (
            "Please enter your departure location."
        );
    }


    if (
        !Number.isInteger(data.travelers) ||
        data.travelers < 1
    ) {

        return (
            "Number of travelers must be at least 1."
        );
    }


    if (
        !Number.isInteger(data.duration_days) ||
        data.duration_days < 1
    ) {

        return (
            "Trip duration must be at least 1 day."
        );
    }


    if (!data.travel_dates) {

        return (
            "Please enter your travel dates."
        );
    }


    if (
        !Number.isFinite(data.budget) ||
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
        validateBasicTripData(data);


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

        const result =
            await API.saveBasicTrip(data);


        if (
            !result ||
            !result.trip_id
        ) {

            throw new Error(
                "Flask did not return a trip ID."
            );
        }


        currentTripId =
            Number(result.trip_id);


        basicTripData =
            result.trip ||
            result.basic_information ||
            data;


        localStorage.setItem(
            STORAGE_KEYS.tripId,
            String(currentTripId)
        );


        localStorage.setItem(
            STORAGE_KEYS.basicTrip,
            JSON.stringify(basicTripData)
        );


        setMessage(
            "basicSaved",
            "Basic trip information saved."
        );


        /*
         * IMPORTANT:
         *
         * Basic Information
         *          ↓
         * Plan Trip
         */

        showPage("planner");


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
        localStorage.getItem(
            STORAGE_KEYS.tripId
        );


    if (!tripId) {

        const cached =
            localStorage.getItem(
                STORAGE_KEYS.basicTrip
            );


        if (cached) {

            try {

                basicTripData =
                    JSON.parse(cached);

            } catch {

                basicTripData = null;
            }
        }

    } else {

        try {

            const trip =
                await API.getBasicTrip(
                    tripId
                );


            basicTripData =
                trip;


            currentTripId =
                Number(trip.id);

        } catch (error) {

            console.warn(
                "Could not retrieve database trip:",
                error
            );
        }
    }


    if (basicTripData) {

        populateBasicForm(
            basicTripData
        );
    }
}


/* ============================================================
   POPULATE BASIC FORM
   ============================================================ */

function populateBasicForm(trip) {

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


    fields.forEach(id => {

        const element =
            document.getElementById(id);


        if (
            element &&
            trip[id] !== undefined &&
            trip[id] !== null
        ) {

            element.value =
                trip[id];
        }
    });


    const other =
        document.getElementById("other");


    if (
        other &&
        trip.other
    ) {

        other.value =
            Array.isArray(trip.other)
                ? trip.other.join(", ")
                : trip.other;
    }


    if (trip.trip_scope) {

        const radio =
            document.querySelector(
                `input[name="trip_scope"][value="${CSS.escape(trip.trip_scope)}"]`
            );


        if (radio) {
            radio.checked = true;
        }
    }


    updateCountryField();
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
     * Recover the SQLite trip ID.
     */

    if (!currentTripId) {

        currentTripId =
            Number(
                localStorage.getItem(
                    STORAGE_KEYS.tripId
                )
            );
    }


    /*
     * The user must have completed
     * Basic Information first.
     */

    if (
        !currentTripId ||
        !Number.isInteger(currentTripId)
    ) {

        setMessage(
            "plannerError",
            "Please complete Basic Information first."
        );

        showPage("basic");

        return;
    }


    /*
     * Plan Trip contains ONLY the user's
     * experience/preferences.
     */

    const preferences =
        value("user_preferences");


    if (!preferences) {

        setMessage(
            "plannerError",
            "Please describe what you want from your trip."
        );

        return;
    }


    /*
     * CRITICAL FIX:
     *
     * user_input is explicitly a STRING.
     *
     * Basic information is NOT sent again.
     *
     * main.py should use trip_id to retrieve:
     *
     * departure_location
     * country
     * travelers
     * duration_days
     * dates
     * budget
     * transportation
     * accommodation
     * etc.
     */

    const data = {

        trip_id:
            currentTripId,

        user_input:
            String(
                preferences
            ).trim()

    };


    console.log(
        "Sending planner request:",
        data
    );


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

        currentTrip =
            await API.startTrip(data);


        if (currentTrip?.trip_id) {

            currentTripId =
                Number(
                    currentTrip.trip_id
                );


            localStorage.setItem(
                STORAGE_KEYS.tripId,
                String(currentTripId)
            );
        }


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


        updateBudgetUI();


        if (results) {

            setTimeout(() => {

                results.scrollIntoView({
                    behavior: "smooth"
                });

            }, 100);
        }


    } catch (error) {

        console.error(
            "START TRIP ERROR:",
            error
        );


        setMessage(
            "plannerError",
            error.message ||
            "Unable to start travel planning."
        );


    } finally {

        setMessage(
            "plannerLoading",
            "",
            false
        );


        if (button) {

            button.disabled = false;

            button.textContent =
                "FIND TRIPS →";
        }
    }
}


/* ============================================================
   CANDIDATES
   ============================================================ */

function getCandidates(trip) {

    if (
        trip?.candidate_result?.candidates &&
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
            trip?.candidates
        )
    ) {

        return trip.candidates.map(
            candidate => {

                if (
                    typeof candidate ===
                    "string"
                ) {

                    return {
                        name: candidate,
                        country: "",
                        reason: ""
                    };
                }


                return candidate;
            }
        );
    }


    return [];
}


/* ============================================================
   RENDER AI RESULTS
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
        getCandidates(trip);


    grid.innerHTML = "";


    if (!candidates.length) {

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
                            candidate.name ||
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


            buttons[0].addEventListener(
                "click",
                () => selectTrip(index)
            );


            buttons[1].addEventListener(
                "click",
                () => showDestination(index)
            );


            grid.appendChild(card);
        }
    );
}


/* ============================================================
   SELECT TRIP
   ============================================================ */

async function selectTrip(index) {

    if (!currentTrip) {

        alert("No active trip.");

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
        panel.style.display = "block";
    }


    if (name) {

        name.textContent =
            selected.name ||
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


    try {

        currentTrip =
            await API.selectTrip(
                currentTrip.trip_id ||
                currentTripId,
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

function renderSelectedTrip(trip) {

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


    if (costs.length) {

        html += `

            <div style="margin-top:17px;">

                <h4>
                    Estimated Costs
                </h4>

                <div class="expense-list">

        `;


        costs.forEach(cost => {

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
        });


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

        button.disabled = true;

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


        alert(
            "Trip confirmed."
        );


    } catch (error) {

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
   UPDATE TRIP
   ============================================================ */

async function updateTrip(changeRequest) {

    if (
        !currentTrip?.trip_id
    ) {

        alert(
            "No active trip."
        );

        return;
    }


    if (
        !String(changeRequest).trim()
    ) {

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
                currentTrip.trip_id,
                changeRequest
            );


        renderTripResults(
            currentTrip
        );


        updateBudgetUI();


    } catch (error) {

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

    currentTrip = null;


    const results =
        document.getElementById(
            "resultsSection"
        );


    if (results) {

        results.style.display =
            "none";
    }


    clearSelection();


    showPage("planner");
}


/* ============================================================
   CANCEL
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


        clearSelection();

        updateBudgetUI();


        alert(
            "Trip cancelled."
        );


    } catch (error) {

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


        currentTrip = null;

        basicTripData = null;

        currentTripId = null;


        localStorage.removeItem(
            STORAGE_KEYS.tripId
        );


        localStorage.removeItem(
            STORAGE_KEYS.basicTrip
        );


        resetPlanner();

        showPage("home");


    } catch (error) {

        alert(
            error.message
        );
    }
}


/* ============================================================
   AI DESTINATION DETAILS
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
            "";
    }


    modal.classList.add(
        "open"
    );
}


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

        const destinations =
            await API.homeDestinations();


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


    container.innerHTML = "";


    if (
        !Array.isArray(destinations) ||
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

        const destinations =
            await API.randomDestinations(
                6
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


    container.innerHTML = "";


    if (
        !Array.isArray(destinations) ||
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

    showPage("search");


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

        result.innerHTML = "";
    }


    try {

        const destinations =
            await API.searchDestination(
                query
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
    destination
) {

    const result =
        document.getElementById(
            "destinationSearchResults"
        );


    if (!result) {
        return;
    }


    result.innerHTML = "";


    /*
     * Backend may return:
     *
     * 1 destination
     * OR
     * an array of destinations.
     */

    let destinations;


    if (Array.isArray(destination)) {

        destinations =
            destination;

    } else if (destination) {

        destinations = [
            destination
        ];

    } else {

        destinations = [];
    }


    if (!destinations.length) {

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
            searchDestination
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

                        showPage(
                            button.dataset.page
                        );
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
     * The HTML should NOT also contain
     * onclick="randomizeDestinations()".
     *
     * This gives the button one listener only.
     */

    button.addEventListener(
        "click",
        async event => {

            event.preventDefault();


            button.disabled = true;

            button.textContent =
                "LOADING...";


            try {

                await randomizeDestinations();

            } finally {

                button.disabled = false;

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
            formatMoney(total);
    }


    if (spentElement) {

        spentElement.textContent =
            formatMoney(spent);
    }


    if (remainingElement) {

        remainingElement.textContent =
            formatMoney(
                budget.remaining
            );
    }


    if (estimatedElement) {

        estimatedElement.textContent =
            formatMoney(estimated);
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

        initializeNavigation();

        initializeForms();

        initializeRandomPage();

        initializeSearch();

        initializeModal();


        /*
         * Recover previously saved trip ID.
         */

        const storedTripId =
            localStorage.getItem(
                STORAGE_KEYS.tripId
            );


        if (storedTripId) {

            const parsed =
                Number(storedTripId);


            if (
                Number.isInteger(parsed) &&
                parsed > 0
            ) {

                currentTripId =
                    parsed;
            }
        }


        /*
         * Recover saved basic information.
         */

        await loadBasicInformation();


        /*
         * Load home destinations.
         */

        await loadHomeDestinations();


        /*
         * Check Flask.
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

    }
);