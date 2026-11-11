
// ======================================
// SENTINEL IDS - FRONTEND CONTROLLER
// ======================================

let lastEventID = 0;

let requestedStatus = "STOPPED";

let totalDisplayed = 0;

let audioContext = null;

let polling = false;


// ======================================
// DOM ELEMENTS
// ======================================

const trafficTable =
    document.getElementById("traffic-table");

const alertPanel =
    document.getElementById("alert-panel");

const systemStatus =
    document.getElementById("system-status");

const statusText =
    document.getElementById("status-text");


// ======================================
// CLOCK
// ======================================

function updateClock() {

    const now = new Date();

    document.getElementById("clock").textContent =
        now.toLocaleTimeString();

}

setInterval(updateClock, 1000);

updateClock();


// ======================================
// API REQUEST HELPER
// ======================================

async function apiRequest(url, options = {}) {

    const response = await fetch(url, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            ...options.headers
        }
    });

    if (!response.ok) {

        throw new Error(
            `Server returned HTTP ${response.status}`
        );

    }

    return await response.json();

}


// ======================================
// IDS CONTROL
// ======================================

async function controlIDS(action) {

    try {

        const result = await apiRequest(
            `/api/${action}`,
            {
                method: "POST"
            }
        );

        if (action === "start") {
            requestedStatus = "RUNNING";
        }

        if (action === "pause") {
            requestedStatus = "PAUSED";
        }

        if (action === "stop") {
            requestedStatus = "STOPPED";
        }

        updateStatus();

        console.log(result.message);

        await updateStatistics();

    } catch (error) {

        console.error("IDS control error:", error);

        alert(
            "Unable to control IDS.\n" + error.message
        );

    }

}


// ======================================
// STATUS INDICATOR
// ======================================

function updateStatus() {

    systemStatus.className = "live-status";

    const sidebarStatus =
        document.getElementById("sidebar-status");

    if (requestedStatus === "RUNNING") {

        statusText.textContent = "MONITORING";

        systemStatus.classList.add("running");

        sidebarStatus.textContent = "Monitoring active";

    }

    else if (requestedStatus === "PAUSED") {

        statusText.textContent = "PAUSED";

        systemStatus.classList.add("paused");

        sidebarStatus.textContent = "Monitoring paused";

    }

    else {

        statusText.textContent = "STOPPED";

        sidebarStatus.textContent = "Monitoring stopped";

    }

}


// ======================================
// STATISTICS
// ======================================

async function updateStatistics() {

    try {

        const stats = await apiRequest("/api/stats");

        document.getElementById(
            "active-sources"
        ).textContent = stats.active_sources;

        document.getElementById(
            "failed-attempts"
        ).textContent = stats.failed_attempts;

        document.getElementById(
            "total-alerts"
        ).textContent = stats.total_alerts;

        document.getElementById(
            "total-requests"
        ).textContent = stats.total_requests;

        document.getElementById(
            "alert-badge"
        ).textContent = `${stats.total_alerts} ALERTS`;

    } catch (error) {

        console.error("Statistics error:", error);

    }

}


// ======================================
// TRAFFIC TABLE
// ======================================

function addTraffic(event) {

    const emptyRow =
        document.getElementById("empty-row");

    if (emptyRow) {
        emptyRow.remove();
    }

    const row = document.createElement("tr");

    let rowClass = "success";

    if (event.status === "FAILED") {
        rowClass = "failed";
    }

    if (event.alert !== "NONE") {
        rowClass = "attack";
    }

    row.className = rowClass;

    const values = [
        event.timestamp,
        event.src_ip,
        event.dst_ip,
        event.request_type,
        event.status,
        event.attempt,
        event.alert
    ];

    values.forEach((value, index) => {

        const cell = document.createElement("td");

        if (index === 4) {

            const badge = document.createElement("span");

            badge.className = "status-badge";

            if (event.status === "SUCCESS") {

                badge.classList.add("badge-success");

            } else {

                badge.classList.add("badge-failed");

            }

            badge.textContent = event.status;

            cell.appendChild(badge);

        }

        else if (index === 6 && event.alert !== "NONE") {

            const badge = document.createElement("span");

            badge.className =
                "detection-badge badge-attack";

            badge.textContent = "BRUTE FORCE";

            cell.appendChild(badge);

        }

        else {

            cell.textContent = String(value);

        }

        row.appendChild(cell);

    });

    trafficTable.appendChild(row);

    totalDisplayed++;

    // Keep only the latest 200 displayed events

    while (trafficTable.children.length > 200) {

        trafficTable.removeChild(
            trafficTable.firstElementChild
        );

    }

    document.getElementById(
        "traffic-count"
    ).textContent =
        `Showing ${Math.min(totalDisplayed, 200)} requests`;

}


// ======================================
// ALERT SOUND
// ======================================

function playAlertSound() {

    try {

        const AudioContextClass =
            window.AudioContext ||
            window.webkitAudioContext;

        if (!AudioContextClass) {
            return;
        }

        if (!audioContext) {

            audioContext = new AudioContextClass();

        }

        if (audioContext.state === "suspended") {

            audioContext.resume();

        }

        const oscillator =
            audioContext.createOscillator();

        const gain =
            audioContext.createGain();

        oscillator.connect(gain);

        gain.connect(audioContext.destination);

        oscillator.type = "sine";

        oscillator.frequency.value = 1000;

        gain.gain.setValueAtTime(
            0.12,
            audioContext.currentTime
        );

        gain.gain.exponentialRampToValueAtTime(
            0.001,
            audioContext.currentTime + 0.5
        );

        oscillator.start();

        oscillator.stop(
            audioContext.currentTime + 0.5
        );

    } catch (error) {

        console.log("Audio unavailable:", error);

    }

}


// ======================================
// DISPLAY SECURITY ALERT
// ======================================

function showAlert(event) {

    const emptyState =
        alertPanel.querySelector(".empty-state");

    if (emptyState) {
        emptyState.remove();
    }

    const entry = document.createElement("div");

    entry.className = "alert-entry";

    const time = document.createElement("span");

    time.className = "alert-time";

    time.textContent = event.timestamp;

    const message = document.createElement("strong");

    message.textContent =
        "⚠ BRUTE FORCE ATTACK DETECTED";

    const details = document.createElement("p");

    details.textContent =
        `SRC: ${event.src_ip} → DST: ${event.dst_ip}`;

    details.style.marginTop = "7px";

    entry.appendChild(time);

    entry.appendChild(message);

    entry.appendChild(details);

    alertPanel.prepend(entry);

    // Limit displayed alert history

    while (alertPanel.children.length > 30) {

        alertPanel.removeChild(
            alertPanel.lastElementChild
        );

    }

    playAlertSound();

    // Browser notification

    if (
        "Notification" in window &&
        Notification.permission === "granted"
    ) {

        new Notification(
            "SENTINEL IDS - Security Alert",
            {
                body:
                    `Brute force detected from ${event.src_ip}`
            }
        );

    }

}


// ======================================
// FETCH NETWORK EVENTS
// ======================================

async function updateTraffic() {

    try {

        const data = await apiRequest(
            `/api/events?after=${lastEventID}`
        );

        data.events.forEach(event => {

            addTraffic(event);

            if (event.alert !== "NONE") {

                showAlert(event);

            }

            lastEventID = Math.max(
                lastEventID,
                event.id
            );

        });

    } catch (error) {

        console.error("Traffic update error:", error);

    }

}


// ======================================
// CLEAR DISPLAY
// ======================================

function clearTraffic() {

    trafficTable.innerHTML = "";

    alertPanel.innerHTML = `
        <div class="empty-state">
            <div class="empty-icon">✓</div>
            <strong>No displayed alerts</strong>
            <p>New security alerts will appear here.</p>
        </div>
    `;

    totalDisplayed = 0;

    document.getElementById(
        "traffic-count"
    ).textContent = "Showing 0 requests";

    // Keep lastEventID unchanged.
    // This prevents old events from appearing again.

}


// ======================================
// BROWSER NOTIFICATION PERMISSION
// ======================================

async function requestNotificationPermission() {

    if (
        "Notification" in window &&
        Notification.permission === "default"
    ) {

        try {

            await Notification.requestPermission();

        } catch (error) {

            console.log(
                "Notification permission unavailable."
            );

        }

    }

}


// ======================================
// INITIALIZE DASHBOARD
// ======================================

async function initializeDashboard() {

    if (polling) {
        return;
    }

    polling = true;

    await updateStatistics();

    await updateTraffic();

    setInterval(updateStatistics, 1000);

    setInterval(updateTraffic, 500);

    // Request permission following user interaction

    document.addEventListener(
        "click",
        requestNotificationPermission,
        { once: true }
    );

}

initializeDashboard();
