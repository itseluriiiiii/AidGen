// ----------------------------------------------------
// DOM ELEMENTS
// ----------------------------------------------------
const statusEl = document.getElementById("status");
const resultEl = document.getElementById("result");
const titleEl = document.getElementById("title");
const summaryEl = document.getElementById("summary");
const stepsEl = document.getElementById("steps");
const smsEl = document.getElementById("sms_text");
const copySmsBtn = document.getElementById("copy_sms");
const fallbackInfo = document.getElementById("fallback-info");
const instructionsEl = document.getElementById("instructions");

// ----------------------------------------------------
// FALLBACK DATA
// ----------------------------------------------------
const FALLBACK_DATA = {
  earthquake: {
    title: "Earthquake Safety",
    summary: "If you're indoors during an earthquake, stay there. Move away from windows and heavy furniture.",
    steps: [
      "Drop to your hands and knees",
      "Cover your head and neck with your arms",
      "Hold on to sturdy furniture",
      "If in bed, cover head with a pillow",
      "Stay indoors until the shaking stops"
    ],
    sms_template: "EARTHQUAKE ALERT! I'm at [LOCATION]. The building is shaking. Need immediate assistance!"
  },
  fire: {
    title: "Fire Emergency",
    summary: "Stay low and escape quickly.",
    steps: [
      "Crawl low under smoke",
      "Check door temperature first",
      "Use alternative exits if needed",
      "Go to meeting point",
      "Call emergency services"
    ],
    sms_template: "FIRE ALERT! Fire at [LOCATION]. Need immediate assistance!"
  },
  flood: {
    title: "Flood Safety",
    summary: "Move to higher ground immediately.",
    steps: [
      "Move to higher ground",
      "Avoid walking in moving water",
      "Never drive into floodwaters",
      "Avoid downed power lines",
      "Follow evacuation orders"
    ],
    sms_template: "FLOOD ALERT! Trapped at [LOCATION]. Water rising. Need help!"
  },
  tsunami: {
    title: "Tsunami Warning",
    summary: "If a strong quake occurs near the coast, move to higher ground immediately.",
    steps: [
      "Go to higher ground immediately",
      "Follow evacuation signs",
      "Do NOT go to shore",
      "Stay away until official all-clear",
      "Monitor alerts"
    ],
    sms_template: "TSUNAMI WARNING! At [LOCATION]. Moving to high ground."
  }
};

// ----------------------------------------------------
// ONLINE / OFFLINE INDICATOR
// ----------------------------------------------------
function setOnline(isOnline) {
  statusEl.textContent = isOnline ? "ONLINE" : "OFFLINE";
  statusEl.className = isOnline ? "status online" : "status offline";
}
setOnline(navigator.onLine);

window.addEventListener("online", () => setOnline(true));
window.addEventListener("offline", () => setOnline(false));

// ----------------------------------------------------
// GET USER LOCATION
// ----------------------------------------------------
function getLocation() {
  return new Promise((resolve) => {
    statusEl.textContent = "Getting your location...";
    statusEl.className = "status-info";
    statusEl.style.display = "block";

    if (!navigator.geolocation) {
      statusEl.textContent = "Geolocation not supported.";
      statusEl.className = "status-error";
      return resolve(null);
    }

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        statusEl.style.display = "none";
        resolve(pos);
      },
      () => {
        statusEl.textContent = "Unable to access location.";
        statusEl.className = "status-warning";
        setTimeout(() => (statusEl.style.display = "none"), 3000);
        resolve(null);
      },
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }
    );
  });
}

// ----------------------------------------------------
// DISPLAY EMERGENCY RESULT
// ----------------------------------------------------
function showResult(data, type, location) {
  titleEl.textContent =
    data.title || `${type.charAt(0).toUpperCase() + type.slice(1)} Emergency`;
  summaryEl.textContent = data.summary || "";

  stepsEl.innerHTML = "";
  (data.steps || []).forEach((step) => {
    const li = document.createElement("li");
    li.textContent = step;
    stepsEl.appendChild(li);
  });

  const sms = (data.sms_template || "").replace("[LOCATION]", location);
  smsEl.textContent = sms;

  resultEl.classList.remove("hidden");
  resultEl.scrollIntoView({ behavior: "smooth" });
}

// ----------------------------------------------------
// MAIN EMERGENCY HANDLER
// ----------------------------------------------------
async function handleEmergency(type) {
  resultEl.classList.add("hidden");
  fallbackInfo.classList.add("hidden");

  statusEl.textContent = "Processing...";
  statusEl.className = "status-info";
  statusEl.style.display = "block";

  // Location fetch with timeout
  let location = "[LOCATION UNAVAILABLE]";
  const position = await Promise.race([
    getLocation(),
    new Promise((resolve) => setTimeout(() => resolve(null), 15000))
  ]);

  if (position?.coords) {
    location = `Lat: ${position.coords.latitude.toFixed(
      4
    )}, Long: ${position.coords.longitude.toFixed(4)}`;
  }

  // Try server
  if (navigator.onLine) {
    try {
      const res = await fetch("/api/alert", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type, location })
      });

      if (res.ok) {
        const data = await res.json();
        showResult(data, type, location);
        statusEl.style.display = "none";
        return;
      }
    } catch {
      console.warn("Server error, fallback activated");
    }
  }

  // Fall back to local dataset
  fallbackInfo.classList.remove("hidden");
  showResult(FALLBACK_DATA[type], type, location);
  statusEl.style.display = "none";
}

window.handleEmergency = handleEmergency;

// ----------------------------------------------------
// FETCH AI SAFETY INSTRUCTIONS
// ----------------------------------------------------
async function getEmergencyInstructions(type, location = "") {
  if (!instructionsEl) return;

  // Loading state
  statusEl.textContent = "Getting safety instructions...";
  statusEl.className = "status-info";
  statusEl.style.display = "block";

  try {
    const response = await fetch("/api/emergency/instructions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ type, location })
    });

    const data = await response.json();

    if (!response.ok) throw new Error("Invalid server response");

    const info = data.instructions;

    instructionsEl.innerHTML = `
      <h3>${info.title}</h3>
      <p class="summary">${info.summary}</p>

      ${
        info.steps.length
          ? `
      <div class="steps">
        <h4>Steps to Take:</h4>
        <ol>${info.steps.map((s) => `<li>${s}</li>`).join("")}</ol>
      </div>`
          : ""
      }

      ${
        info.warnings.length
          ? `
      <div class="warnings">
        <h4>⚠ Important Warnings:</h4>
        <ul>${info.warnings
          .map((w) => `<li>${w}</li>`)
          .join("")}</ul>
      </div>`
          : ""
      }
    `;

    instructionsEl.style.display = "block";
    statusEl.style.display = "none";
    instructionsEl.scrollIntoView({ behavior: "smooth" });
  } catch (err) {
    console.error(err);
    statusEl.textContent = "Failed to load instructions.";
    statusEl.className = "status-error";
    setTimeout(() => (statusEl.style.display = "none"), 4000);
  }
}

// ----------------------------------------------------
// WHAT-TO-DO BUTTON HANDLER
// ----------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
  const whatBtn = document.querySelector(".what-to-do");
  if (!whatBtn) return;

  whatBtn.addEventListener("click", async (e) => {
    e.preventDefault();

    const path = window.location.pathname;
    let type = "general";
    if (path.includes("earthquake")) type = "earthquake";
    if (path.includes("fire")) type = "fire";
    if (path.includes("flood")) type = "flood";
    if (path.includes("tsunami")) type = "tsunami";

    let location = "";
    const pos = await getLocation();
    if (pos?.coords) {
      location = `Lat: ${pos.coords.latitude.toFixed(
        4
      )}, Long: ${pos.coords.longitude.toFixed(4)}`;
    }

    getEmergencyInstructions(type, location);
  });
});

// ----------------------------------------------------
// COPY SMS BUTTON
// ----------------------------------------------------
copySmsBtn.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(smsEl.textContent);
    const old = copySmsBtn.innerHTML;
    copySmsBtn.innerHTML = "✓ Copied";
    setTimeout(() => (copySmsBtn.innerHTML = old), 1500);
  } catch {
    alert("Failed to copy SMS");
  }
});
