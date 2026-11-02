let events = [];

let currentRole = "admin";

// =========================================
// SORTING
// =========================================

let currentSort = {
    field: null,
    ascending: true
};

// =========================================
// AUTO REMEDIATION POPUP
// =========================================

let lastAutoLogTime =
    localStorage.getItem("lastAutoLogTime") || "";


// =========================================
// LOAD INCIDENT DATA
// =========================================

// =========================================
// LOAD INCIDENT DATA
// =========================================

function loadDashboard() {

    fetch("action_executor.json?_=" + new Date().getTime())

        .then(response => {

            if (!response.ok) {
                throw new Error("No dashboard data");
            }

            return response.json();
        })

        .then(data => {

            

            const newEvents = data.map(item => {

                const primaryEvent =
                    item.supporting_events?.find(
                        e => e.role === "primary"
                    );

                const topAction =
                    item.remediation_script ||
                    item.suggested_actions?.[0]?.action ||
                    "Investigate incident manually";

                return {

                    eventId:
                        primaryEvent?.event_id || "-",

                    timestamp:
                        item.created_at
                            ? new Date(item.created_at).toLocaleString()
                            : "-",
                    rawTimestamp:
                        item.created_at || "-",

                    source:
                        item.root_cause?.category ||
                        "System Event",

                    severity:
                        item.severity ||
                        item.impact_summary?.severity ||
                        "Unknown",

                    message:
                        item.original_message ||
                        item.llm_explanation ||
                        item.message ||
                        item.root_cause?.reason_code ||
                        "No RCA message",

                    solution:
                        topAction,

                    confidence:
                        item.confidence_score || 0,

                    status:
                        item.status || "Pending",

                    approvedAt:
                        item.approved_time || "-",

                    remediationPath:
                        "#",

                    rawData:
                        item
                };

            });
            if (currentSort.field === null) {

              newEvents.sort((a, b) =>
                new Date(b.rawTimestamp) - new Date(a.rawTimestamp)
              );

            }

            if (JSON.stringify(newEvents) !== JSON.stringify(events)) {

              events = newEvents;

              updateSummaryCards();

              render();

      }
            checkAutoRemediation();

        })

        .catch(error => {

            console.log("Waiting for pipeline...");

            events = [];

            render();

        });

}

loadDashboard();


// =========================================
// RENDER TABLE
// =========================================

function render() {

  const table =
    document.getElementById("eventTable");

  // =========================================
// APPLY SORTING
// =========================================

let displayEvents = [...events];

if (currentSort.field === "timestamp") {

    displayEvents.sort((a, b) => {

        const t1 = new Date(a.rawTimestamp).getTime();
        const t2 = new Date(b.rawTimestamp).getTime();

        return currentSort.ascending
            ? t1 - t2
            : t2 - t1;

    });

}

if (currentSort.field === "confidence") {

    displayEvents.sort((a, b) =>

        currentSort.ascending
            ? a.confidence - b.confidence
            : b.confidence - a.confidence

    );

}

if (currentSort.field === "eventId") {

    displayEvents.sort((a, b) => {

        const id1 = Number(a.eventId);
        const id2 = Number(b.eventId);

        return currentSort.ascending
            ? id1 - id2
            : id2 - id1;

    });

}

if (currentSort.field === "approvedTime") {

    displayEvents.sort((a, b) => {

        const t1 = a.approvedAt === "-" ? 0 : new Date(a.approvedAt).getTime();
        const t2 = b.approvedAt === "-" ? 0 : new Date(b.approvedAt).getTime();

        return currentSort.ascending
            ? t1 - t2
            : t2 - t1;

    });

}

  table.innerHTML = "";


  // =========================================
  // FILTERS
  // =========================================

  const severityFilter =

    document
      .getElementById("severityFilter")
      .value;


  const statusFilter =

    document
      .getElementById("statusFilter")
      .value;


  const searchText =

    document
      .getElementById("searchInput")
      .value
      .toLowerCase();


  // =========================================
  // ROLE
  // =========================================

  currentRole =

    document
      .getElementById("roleSelector")
      .value;


  // =========================================
  // LOOP INCIDENTS
  // =========================================

  displayEvents.forEach((event, index) => {


    // =========================================
    // FILTER LOGIC
    // =========================================

    const severityMatch =

      severityFilter === "all" ||

      event.severity
        .toLowerCase() ===
        severityFilter.toLowerCase();


    const statusMatch =

      statusFilter === "all" ||

      event.status
        .toLowerCase() ===
        statusFilter.toLowerCase();


    const searchMatch =

      searchText === "" ||

      event.message
        .toLowerCase()
        .includes(searchText) ||

      event.source
        .toLowerCase()
        .includes(searchText);


    if (
      !severityMatch ||
      !statusMatch ||
      !searchMatch
    ) {
      return;
    }


    // =========================================
    // STATUS COLORS
    // =========================================

    let statusClass =
      "status-pending";


    if (
      event.status === "Approved"
    ) {

      statusClass =
        "status-approved";
    }


    if (event.status === "Rejected") {

      statusClass =
        "status-rejected";
    }

    if (event.status === "Auto Remediated") {
      statusClass = "status-auto-remediated";
    }


    // =========================================
    // REMEDIATION LINK
    // =========================================

    const remediationLink =

  event.rawData?.remediation_script

  ? `
      <a
        href="RemediationScripts/${event.rawData.remediation_script}"
        target="_blank">

        View Steps

      </a>
    `

  : "No Script";


    // =========================================
    // CREATE ROW
    // =========================================

    const card = document.createElement("div");
    card.className = "incident-card";
    // Row background based on status

    const severity = event.severity.toLowerCase();

    if (event.status === "Pending") {
    card.classList.add("row-pending");
}
else if (event.status === "Approved") {
    card.classList.add("row-approved");
}
else if (event.status === "Rejected") {
    card.classList.add("row-rejected");
}
else if (event.status === "Auto Remediated") {
    card.classList.add("row-auto-remediated");
}

    card.innerHTML = `
<div class="incident-row">

    <div class="col id">${index + 1}</div>

    <div class="col event">
        ${event.eventId}
    </div>

    <div class="col time">
        ${event.timestamp}
    </div>

    <div class="col source">
        ${event.source}
    </div>

    <div class="col severity">
        <span class="severity-${event.severity.toLowerCase()}">
            ${event.severity}
        </span>
    </div>

    <div class="col message">
        ${event.message}
    </div>

    <div class="col solution">
        ${event.solution}
    </div>

    <div class="col status">
        <span class="${statusClass}">
            ${event.status}
        </span>
    </div>

    <div class="col confidence">
        ${(event.confidence*100).toFixed(0)}%
    </div>

    <div class="col approved-time">
        ${event.approvedAt}
    </div>

    <div class="col remediation">
        ${remediationLink}
    </div>

    <div class="col actions"></div>

</div>
`;


    // =========================================
    // ACTION BUTTONS
    // =========================================

    const actionCell =
    card.querySelector(".actions");
    const hasRemediation = !!event.rawData?.remediation_script;
    const isLowConfidence = Number(event.confidence || 0) < 0.5;
    const approvalDisabled =
    (isLowConfidence || !hasRemediation) ? "disabled" : "";
    const approvalTitle = isLowConfidence
      ? 'title="Approval requires a confidence score of 50% or higher"'
      : "";


    // =========================================
    // ADMIN
    // =========================================

    if (currentRole === "admin") {


      actionCell.classList.add("action-cell");


      actionCell.innerHTML = `

        <button
          class="btn btn-approve"
          onclick="approve('${event.rawData.incident_id}')"
          ${approvalDisabled}
          ${approvalTitle}>

          Approve

        </button>

        <button
    class="btn btn-reject"
    onclick="reject('${event.rawData.incident_id}')"
    ${!hasRemediation ? "disabled" : ""}>
    Reject
</button>
      `;
    }


    // =========================================
    // NORMAL USER
    // =========================================

    else {


      actionCell.innerHTML = `

        <button
          class="btn btn-approve"
          disabled>

          Approve

        </button>

        <button
          class="btn btn-reject"
          disabled>

          Reject

        </button>
      `;
    }


    

    card.tabIndex = 0;
    card.setAttribute("role", "button");
    card.setAttribute("aria-label", `Open incident ${event.rawData.incident_id || event.eventId}`);
    card.addEventListener("click", () => renderIncidentDrawerDetails(event));
    card.addEventListener("keydown", (keyboardEvent) => {
      if (keyboardEvent.key === "Enter" || keyboardEvent.key === " ") {
        keyboardEvent.preventDefault();
        renderIncidentDrawerDetails(event);
      }
    });
    actionCell.addEventListener("click", (mouseEvent) => mouseEvent.stopPropagation());

    table.appendChild(card);
  });
}


// =========================================
// APPROVE
// =========================================

function approve(incidentId) {

    const event = events.find(
        e => e.rawData.incident_id === incidentId
    );

    if (!event) return;

    if (Number(event.confidence || 0) < 0.5) {
        console.warn("Approval blocked: incident confidence is below 50%.");
        return;
    }

    console.log("Approving:", event);

    const now = new Date();


  

  const scriptName = event.rawData?.remediation_script;

  

if (scriptName) {

  fetch(
    "http://localhost:5000/run-remediation",
    {

      method: "POST",

      headers: {
        "Content-Type":
          "application/json"
      },

      body: JSON.stringify({

        script:
          scriptName
      })
    }
  )

  .then(response => response.json())

  .then(data => {

    

    if (data.status === "success") {

    fetch("http://localhost:5000/cleanup-result")

    .then(r => r.json())

    .then(result => {

        showAutoPopup({

            event_id: event.eventId,

            script: data.script,

            result: data.verification,

            timestamp: data.time,

            files_deleted: result.files_deleted,

            recovered_gb: result.recovered_gb,

            cleanup_time: result.completed_at

        });

    });

} else {

    console.error("Backend Response:", data);

    alert(
`Remediation Failed

Verification:
${data.verification || "FAILED"}

Reason:
${data.details || data.message || "Unknown Error"}`
    );

}

})

  .catch(error => {

    console.error("Dashboard Error:", error);

    events = [];

    render();

});
}


 event.approvedAt =
  now.toLocaleString();
  event.status = "Approved";

  // =========================================
  // SEND FEEDBACK
  // =========================================

  fetch(
    "http://localhost:5000/feedback",
    {

      method: "POST",

      headers: {
        "Content-Type":
          "application/json"
      },

      body: JSON.stringify({

        alertId:
          event.eventId,

        solution:
          event.rawData.remediation_script,

        feedback:
          "success"
      })
    }
  )

  .then(response => response.json())

  .then(data => {

    console.log(
      "Feedback saved:",
      data
    );
  })

  .catch(error => {

    console.error(
      "Feedback API error:",
      error
    );
  });


  render();
}


// =========================================
// REJECT
// =========================================

function reject(incidentId)  {

  const event = events.find(
        e => e.rawData.incident_id === incidentId
    );

    if (!event) return;

    event.status = "Rejected";


  fetch(
    "http://localhost:5000/feedback",
    {

      method: "POST",

      headers: {
        "Content-Type":
          "application/json"
      },

      body: JSON.stringify({

        alertId:
          event.eventId,

        solution:
          event.solution,

        feedback:
          "failure"
      })
    }
  )

  .then(response => response.json())

  .then(data => {

    console.log(
      "Feedback saved:",
      data
    );
  })

  .catch(error => {

    console.error(
      "Feedback API error:",
      error
    );
  });


  render();
}


// =========================================
// FILTER LISTENERS
// =========================================

document
  .getElementById("severityFilter")
  .addEventListener(
    "change",
    render
  );


document
  .getElementById("statusFilter")
  .addEventListener(
    "change",
    render
  );


document
  .getElementById("searchInput")
  .addEventListener(
    "input",
    render
  );


document
  .getElementById("roleSelector")
  .addEventListener(
    "change",
    render
  );
  function viewSteps(item) {

  const actions = item.suggested_actions
    ?.map(a => "• " + a.action)
    .join("\n");


  alert(

`RCA Explanation:
${item.llm_explanation || item.original_message}

Root Cause:
${item.root_cause?.category}

Severity:
${item.severity}

Confidence:
${Math.round(item.confidence_score * 100)}%

Suggested Actions:
${actions || "Investigate incident manually"}

Remediation Script:
${item.remediation_script || "None"}`
  );
}
// =========================================
// CHECK AUTO REMEDIATION LOG
// =========================================

// Override the legacy alert-based helper with the detail drawer while retaining
// its public function name for any existing callers.
function viewSteps(item) {
  const matchingEvent = events.find(event => event.rawData === item) || {
    eventId: item.supporting_events?.find(event => event.role === "primary")?.event_id || "-",
    timestamp: item.created_at ? new Date(item.created_at).toLocaleString() : "-",
    source: item.root_cause?.category || "System Event",
    severity: item.severity || "Unknown",
    message: item.original_message || item.llm_explanation || "No RCA message",
    solution: item.remediation_script || item.suggested_actions?.[0]?.action || "Investigate incident manually",
    confidence: item.confidence_score || 0,
    status: item.status || "Pending",
    approvedAt: item.approved_time || "-",
    rawData: item
  };
  renderIncidentDrawerDetails(matchingEvent);
}

function setDrawerValue(id, value, isHtml) {
  const element = document.getElementById(id);
  if (!element) return;
  if (isHtml) element.innerHTML = value;
  else element.textContent = value || "—";
}

function renderIncidentDrawerDetails(event) {
  const item = event.rawData || {};
  const actions = item.suggested_actions?.map(action => action.action).filter(Boolean).join("\n") || event.solution || "Investigate incident manually";
  const supporting = item.supporting_events?.map(supportingEvent => `Event ID ${supportingEvent.event_id} · ${supportingEvent.role || "related"} · ${supportingEvent.count || 1} occurrence${supportingEvent.count === 1 ? "" : "s"}`).join("\n") || "No supporting events recorded.";
  const confidence = Math.round(Number(event.confidence || 0) * 100);
  const severityClass = `severity-${String(event.severity || "unknown").toLowerCase()}`;
  const statusClass = `status-${String(event.status || "pending").toLowerCase().replace(/\s+/g, "-")}`;

  setDrawerValue("drawerTitle", `Incident ${item.incident_id || event.eventId}`);
  setDrawerValue("drawerId", item.incident_id || "—");
  setDrawerValue("drawerEventId", event.eventId);
  setDrawerValue("drawerTime", event.timestamp);
  setDrawerValue("drawerSource", event.source);
  setDrawerValue("drawerSeverity", `<span class="${severityClass}">${event.severity}</span>`, true);
  setDrawerValue("drawerConfidence", `<div class="confidence-meter"><span style="width: ${confidence}%"></span></div><strong>${confidence}%</strong>`, true);
  setDrawerValue("drawerStatus", `<span class="${statusClass}">${event.status}</span>`, true);
  setDrawerValue("drawerApprovedTime", event.approvedAt);
  setDrawerValue("drawerMessage", event.message);
  setDrawerValue("drawerRCA", item.llm_explanation || item.root_cause?.reason_code || event.source);
  setDrawerValue("drawerActions", actions);
  setDrawerValue("drawerEvents", supporting);
  setDrawerValue("drawerScript", item.remediation_script || "No remediation script assigned.");
  setDrawerValue("drawerExecStatus", item.status || event.status);
  document.querySelectorAll("#eventTable tr.selected").forEach(row => row.classList.remove("selected"));
  const row = [...document.querySelectorAll("#eventTable tr")].find(row => row.getAttribute("aria-label") === `Open incident ${item.incident_id || event.eventId}`);
  if (row) row.classList.add("selected");
  if (typeof window.openIncidentDrawer === "function") window.openIncidentDrawer();
}

function checkAutoRemediation() {

    fetch("http://localhost:5000/auto_remediation_log.json?_=" + Date.now())

        .then(response => response.json())

        .then(data => {

            if (!data || data.length === 0)
                return;

            const latest = data[data.length - 1];

            if (latest.timestamp !== lastAutoLogTime) {

                lastAutoLogTime = latest.timestamp;

                localStorage.setItem(
                    "lastAutoLogTime",
                    latest.timestamp
                );

                showAutoPopup(latest);

            }

        })

        .catch(console.error);

}
// =========================================
// SHOW AUTO REMEDIATION POPUP
// =========================================

function showAutoPopup(log) {

    fetch("http://localhost:5000/cleanup-result")

        .then(r => r.json())

        .then(result => {

            const oldPopup =
                document.querySelector(".auto-toast");

            if (oldPopup)
                oldPopup.remove();

            const wrapper =
                document.createElement("div");

            wrapper.className = "auto-toast";

            wrapper.innerHTML = `

                <div class="toast-title">

                    ✅ Auto Remediation Executed

                </div>

                <hr>

                <p><b>Event ID:</b> ${log.event_id}</p>

                <p><b>Action:</b> Disk Cleanup</p>

                <p>✔ Temporary Files Deleted</p>

                <p>✔ Cleanup Folder Cleared</p>

                <p><b>Files Deleted:</b> ${result.files_deleted}</p>

                <p><b>Recovered:</b> ${result.recovered_gb} GB</p>

                <small>${result.time}</small>

            `;

            document.body.appendChild(wrapper);

            setTimeout(() => {

                wrapper.remove();

            }, 5000);

        });

}
// =========================================
// LOAD AUTO REMEDIATION HISTORY
// =========================================

// Keep the original data source, but present every auto-remediation event in
// the single Windows-style toast already present in the page.
function showAutoPopup(log) {
  fetch("http://localhost:5000/cleanup-result")
    .then(response => response.json())
    .then(result => {
      const title = "Auto Remediation Executed";
      const message = `Event ID: ${log.event_id || "—"} · Action: ${log.script || "Disk Cleanup"}\nFiles deleted: ${result.files_deleted ?? "—"} · Disk space recovered: ${result.recovered_gb ?? "—"} GB\n${log.timestamp || result.time || ""}`;
      if (typeof window.showAutoRemediationToast === "function") {
        window.showAutoRemediationToast(title, message);
      }
    })
    .catch(console.error);
}



// =========================================
// AUTO REFRESH
// =========================================
// =========================================
// SUMMARY CARDS
// =========================================

function updateSummaryCards() {

    document.getElementById("totalCount").textContent =
        events.length;

    document.getElementById("pendingCount").textContent =
        events.filter(e => e.status === "Pending").length;

    document.getElementById("approvedCount").textContent =
        events.filter(e => e.status === "Approved").length;

    document.getElementById("rejectedCount").textContent =
        events.filter(e => e.status === "Rejected").length;

    updateDashboardCharts();

}

let statusChartInstance;
let severityChartInstance;
let trendChartInstance;
let confidenceChartInstance;

function updateDashboardCharts() {
    if (typeof Chart === "undefined") return;

    const palette = { blue: "#2563EB", green: "#16A34A", amber: "#F59E0B", red: "#DC2626", slate: "#64748B" };
    const counts = (key, labels) => labels.map(label => events.filter(event => String(event[key] || "").toLowerCase() === label.toLowerCase()).length);
    const baseOptions = { responsive: true, maintainAspectRatio: false, animation: { duration: 500 }, plugins: { legend: { position: "bottom", labels: { usePointStyle: true, boxWidth: 8, padding: 14, font: { family: "Inter", size: 11 } } } } };
    const recreate = (current, canvasId, config) => {
      if (current) current.destroy();
      const canvas = document.getElementById(canvasId);
      return canvas ? new Chart(canvas, config) : undefined;
    };

    const statusLabels = ["Pending", "Approved", "Rejected", "Auto Remediated"];
    statusChartInstance = recreate(statusChartInstance, "statusChart", {
      type: "pie", data: { labels: statusLabels, datasets: [{ data: counts("status", statusLabels), backgroundColor: [palette.amber, palette.blue, palette.red, palette.green], borderWidth: 2, borderColor: "#fff" }] }, options: baseOptions
    });
    const severityLabels = ["Critical", "Error", "Warning"];
    severityChartInstance = recreate(severityChartInstance, "severityChart", {
      type: "doughnut", data: { labels: severityLabels, datasets: [{ data: counts("severity", severityLabels), backgroundColor: ["#7F1D1D", palette.red, palette.amber], borderWidth: 2, borderColor: "#fff" }] }, options: { ...baseOptions, cutout: "66%" }
    });
    const trendByDay = new Map();
    events.filter(event => event.rawTimestamp && event.rawTimestamp !== "-").forEach(event => {
      const day = new Date(event.rawTimestamp).toLocaleDateString([], { month: "short", day: "numeric" });
      trendByDay.set(day, (trendByDay.get(day) || 0) + 1);
    });
    const chronological = [...trendByDay.entries()].slice(-7);
    trendChartInstance = recreate(trendChartInstance, "trendChart", {
      type: "line", data: { labels: chronological.map(entry => entry[0]), datasets: [{ label: "Incidents", data: chronological.map(entry => entry[1]), borderColor: palette.blue, backgroundColor: "rgba(37,99,235,.12)", fill: true, tension: .35, pointRadius: 4, pointBackgroundColor: palette.blue }] }, options: { ...baseOptions, scales: { y: { beginAtZero: true, ticks: { precision: 0 }, grid: { color: "#EEF2F7" } }, x: { grid: { display: false } } } }
    });
    const confidenceLabels = ["0–49%", "50–69%", "70–84%", "85–100%"];
    const confidenceData = [0, 0, 0, 0];
    events.forEach(event => { const score = Number(event.confidence || 0) * 100; confidenceData[score < 50 ? 0 : score < 70 ? 1 : score < 85 ? 2 : 3]++; });
    confidenceChartInstance = recreate(confidenceChartInstance, "confidenceChart", {
      type: "bar", data: { labels: confidenceLabels, datasets: [{ label: "Incidents", data: confidenceData, backgroundColor: ["#FCA5A5", "#FCD34D", "#93C5FD", "#60A5FA"], borderRadius: 6, borderSkipped: false }] }, options: { ...baseOptions, scales: { y: { beginAtZero: true, ticks: { precision: 0 }, grid: { color: "#EEF2F7" } }, x: { grid: { display: false } } } }
    });
}
// =========================================
// SORT BY TIMESTAMP
// =========================================

function sortByTimestamp(ascending) {

    currentSort.field = "timestamp";
    currentSort.ascending = ascending;

    render();

}

// =========================================
// SORT BY CONFIDENCE
// =========================================

function sortByTimestamp() {

    if (currentSort.field === "timestamp")
        currentSort.ascending = !currentSort.ascending;
    else {
        currentSort.field = "timestamp";
        currentSort.ascending = true;
    }

    updateSortIcons();
    render();
}

function sortByConfidence() {

    if (currentSort.field === "confidence")
        currentSort.ascending = !currentSort.ascending;
    else {
        currentSort.field = "confidence";
        currentSort.ascending = true;
    }

    updateSortIcons();
    render();
}

function sortByEventId() {

    if (currentSort.field === "eventId")
        currentSort.ascending = !currentSort.ascending;
    else {
        currentSort.field = "eventId";
        currentSort.ascending = true;
    }

    updateSortIcons();
    render();
}

function sortByApprovedTime() {

    if (currentSort.field === "approvedTime")
        currentSort.ascending = !currentSort.ascending;
    else {
        currentSort.field = "approvedTime";
        currentSort.ascending = true;
    }

    updateSortIcons();
    render();
}

function updateSortIcons() {

    document.querySelectorAll(".sort-icons .up, .sort-icons .down")
        .forEach(icon => icon.classList.remove("active"));

    console.log(currentSort.field);

    const container = document.getElementById("sort-" + currentSort.field);

    console.log(container);

    if (!container) return;

    if (currentSort.ascending)
        container.querySelector(".up").classList.add("active");
    else
        container.querySelector(".down").classList.add("active");
}
function refreshDashboard() {

    const btn = document.getElementById("refreshBtn");

    btn.classList.add("spin");

    setTimeout(() => {
        location.reload();
    }, 650);
}