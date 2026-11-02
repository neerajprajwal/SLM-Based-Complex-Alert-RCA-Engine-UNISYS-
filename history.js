let lastHistoryCount = -1;
let lastLatestTimestamp = "";
let currentSort = "desc";
let currentFilter = "all";
let eventSort = "none";

function loadHistory() {

    fetch("auto_remediation_log.json?_=" + new Date().getTime())

        .then(response => response.json())

        .then(logs => {

            if (!Array.isArray(logs)) return;

            const latestTimestamp =
                logs.length > 0
                    ? logs[logs.length - 1].timestamp
                    : "";

            // Nothing changed
            // Skip reload only during automatic refresh


lastHistoryCount = logs.length;
lastLatestTimestamp = latestTimestamp;

            const table =
                document.getElementById("historyTable");

            // =========================================
            // SUMMARY CARDS
            // =========================================

            document.getElementById("totalLogs").textContent =
                logs.length;

            const successCount = logs.filter(log =>
                (log.result || "").toLowerCase() === "success"
            ).length;

            const failureCount = logs.length - successCount;

            document.getElementById("successCount").textContent =
                successCount;

            document.getElementById("failureCount").textContent =
                failureCount;

            // =========================================
            // TABLE
            // =========================================

            table.innerHTML = "";

            let filteredLogs = [...logs];

// Filter
if(currentFilter !== "all"){
    filteredLogs = filteredLogs.filter(log =>
        (log.result || "").toLowerCase() === currentFilter.toLowerCase()
    );
}

// Sort
if(eventSort !== "none"){

    filteredLogs.sort((a,b)=>{

        const e1 = Number(a.event_id);
        const e2 = Number(b.event_id);

        return eventSort === "asc"
            ? e1 - e2
            : e2 - e1;

    });

}
else{

    filteredLogs.sort((a,b)=>{

        const t1 = new Date(a.timestamp.replace(" ", "T"));
        const t2 = new Date(b.timestamp.replace(" ", "T"));

        return currentSort === "desc"
            ? t2 - t1
            : t1 - t2;

    });

}
//new
if(filteredLogs.length === 0){

    table.innerHTML = `
        <tr>
            <td colspan="6" style="
                text-align:center;
                padding:40px;
                font-size:16px;
                color:#6B7280;
                font-weight:600;">
                ✓ No remediation logs found for the selected filter.
            </td>
        </tr>
    `;
    return;
}

filteredLogs.forEach(log => {

                
            const status = (log.result || "").toLowerCase();

            let statusBadge = "";
            let rowClass = "";

            if (status === "success") {

                statusBadge = `<span class="status-success">Success</span>`;
                rowClass = "history-success";

            }
            else if (status === "in progress") {

                statusBadge = `<span class="status-progress">In Progress</span>`;
                rowClass = "history-progress";

            }
            else {

                statusBadge = `<span class="status-failed">Failed</span>`;
                rowClass = "history-failed";

            }

            const row = document.createElement("tr");

            row.className = rowClass;

                row.innerHTML = `
                    <td>${log.timestamp}</td>

                    <td>${log.incident_id}</td>

                    <td>${log.event_id}</td>

                    <td>${log.script}</td>

                    <td>${log.mode}</td>

                    <td>${statusBadge}</td>
                `;

                table.appendChild(row);

            });

        })

        .catch(() => {

            console.log("No history available.");

        });

}


loadHistory();

setInterval(loadHistory, 3000);

// ======================================
// TIME SORT & STATUS FILTER
// ======================================

window.addEventListener("DOMContentLoaded", function () {

    document.getElementById("timeHeader").addEventListener("click", function () {

        eventSort = "none";  
        currentSort = currentSort === "desc" ? "asc" : "desc";

        loadHistory();

    });
    document.getElementById("eventHeader").addEventListener("click", function () {

        currentSort = "desc"; 
        eventSort = eventSort === "asc" ? "desc" : "asc";

    loadHistory();

});

    document.getElementById("statusFilter").addEventListener("change", function () {

        currentFilter = this.value;

        loadHistory();

    });

});