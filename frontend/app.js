// ─── Configuration ────────────────────────────────────────────────────────────
// Edit these three values before deploying the frontend.
const CONFIG = {
  API_BASE:         "http://localhost:8000",       // Your backend URL
  SUPABASE_URL:     "https://YOUR_PROJECT.supabase.co",
  SUPABASE_ANON_KEY: "YOUR_SUPABASE_ANON_KEY",
};
// ─────────────────────────────────────────────────────────────────────────────

// Retailer → colour mapping for marker icons
const RETAILER_COLOURS = {
  "Tesco":       "#00539f",
  "Sainsbury's": "#f06c00",
  "Asda":        "#78be20",
  "Morrisons":   "#ffd700",
  "Waitrose":    "#3d8c40",
  "M&S":         "#000000",
  "Lidl":        "#0050aa",
  "Aldi":        "#003399",
  "Co-op":       "#00b1e7",
  "Iceland":     "#cc0000",
  "Greggs":      "#003087",
  "Boots":       "#003d90",
};
const DEFAULT_COLOUR = "#c0392b";

function markerColour(retailer) {
  return RETAILER_COLOURS[retailer] || DEFAULT_COLOUR;
}

function circleIcon(colour) {
  return L.divIcon({
    className: "",
    html: `<div style="
      width:14px;height:14px;border-radius:50%;
      background:${colour};border:2px solid #fff;
      box-shadow:0 1px 3px rgba(0,0,0,.4)"></div>`,
    iconSize: [14, 14],
    iconAnchor: [7, 7],
    popupAnchor: [0, -10],
  });
}

function formatDate(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
}

function excerpt(text, max = 100) {
  return text.length > max ? text.slice(0, max).trimEnd() + "…" : text;
}

function buildPopup(s) {
  const retailerLine = s.retailer ? `<div class="retailer">${s.retailer}</div>` : "";
  const postcodeLine = s.postcode ? `<div class="postcode">📍 ${s.postcode}</div>` : "";
  const link = s.post_url
    ? `<a href="${s.post_url}" target="_blank" rel="noopener">View post</a>`
    : `<span>${s.platform}</span>`;
  return `<div class="popup-inner">
    ${retailerLine}
    ${postcodeLine}
    <div class="excerpt">${excerpt(s.post_text)}</div>
    <div class="meta">${formatDate(s.created_at)} · ${link}</div>
  </div>`;
}

// ─── Map setup ────────────────────────────────────────────────────────────────
const map = L.map("map").setView([54.5, -2.5], 6);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: "© OpenStreetMap contributors",
  maxZoom: 18,
}).addTo(map);

const clusters = L.markerClusterGroup({ maxClusterRadius: 40 });
map.addLayer(clusters);

const markers = new Map(); // post id → marker

function addMarker(s) {
  if (!s.lat || !s.lng) return;
  if (markers.has(s.id)) return;
  const m = L.marker([s.lat, s.lng], { icon: circleIcon(markerColour(s.retailer)) })
    .bindPopup(buildPopup(s));
  clusters.addLayer(m);
  markers.set(s.id, m);
}

// ─── Stats bar ────────────────────────────────────────────────────────────────
let allSightings = [];

function updateStats() {
  document.getElementById("stat-total").textContent =
    `${allSightings.length} sighting${allSightings.length !== 1 ? "s" : ""}`;

  const withDates = allSightings.filter(s => s.created_at);
  if (withDates.length) {
    const earliest = withDates.reduce((a, b) =>
      a.created_at < b.created_at ? a : b
    );
    document.getElementById("stat-earliest").textContent =
      `earliest: ${formatDate(earliest.created_at)}`;
  }
}

// ─── Load initial sightings ───────────────────────────────────────────────────
async function loadSightings() {
  try {
    const resp = await fetch(`${CONFIG.API_BASE}/api/sightings`);
    if (!resp.ok) throw new Error(resp.statusText);
    const data = await resp.json();
    allSightings = data;
    data.forEach(addMarker);
    updateStats();
  } catch (err) {
    console.error("Failed to load sightings:", err);
  }
}

// ─── Supabase realtime ────────────────────────────────────────────────────────
function setupRealtime() {
  if (
    CONFIG.SUPABASE_URL.includes("YOUR_PROJECT") ||
    CONFIG.SUPABASE_ANON_KEY.includes("YOUR_")
  ) return; // not configured yet

  const client = supabase.createClient(CONFIG.SUPABASE_URL, CONFIG.SUPABASE_ANON_KEY);
  client
    .channel("sightings-inserts")
    .on(
      "postgres_changes",
      { event: "INSERT", schema: "public", table: "sightings" },
      ({ new: s }) => {
        allSightings.unshift(s);
        addMarker(s);
        updateStats();
        showToast(`New sighting${s.retailer ? ` at ${s.retailer}` : ""}${s.postcode ? ` · ${s.postcode}` : ""}!`);
      }
    )
    .subscribe();
}

// ─── Toast ────────────────────────────────────────────────────────────────────
const toastEl = document.createElement("div");
toastEl.id = "toast";
document.body.appendChild(toastEl);
let toastTimer;

function showToast(msg) {
  toastEl.textContent = msg;
  toastEl.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toastEl.classList.remove("show"), 3500);
}

// ─── Manual submission form ───────────────────────────────────────────────────
const overlay  = document.getElementById("modal-overlay");
const formErr  = document.getElementById("form-error");

document.getElementById("btn-report").addEventListener("click",  () => overlay.classList.remove("hidden"));
document.getElementById("btn-cancel").addEventListener("click",  () => overlay.classList.add("hidden"));
overlay.addEventListener("click", e => { if (e.target === overlay) overlay.classList.add("hidden"); });

document.getElementById("btn-submit").addEventListener("click", async () => {
  const text     = document.getElementById("f-text").value.trim();
  const postcode = document.getElementById("f-postcode").value.trim();
  const retailer = document.getElementById("f-retailer").value;

  formErr.classList.add("hidden");
  if (!text) {
    formErr.textContent = "Please describe what you saw.";
    formErr.classList.remove("hidden");
    return;
  }

  const btn = document.getElementById("btn-submit");
  btn.disabled = true;
  btn.textContent = "Submitting…";

  try {
    const resp = await fetch(`${CONFIG.API_BASE}/api/sightings`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, postcode, retailer }),
    });
    if (!resp.ok) throw new Error(await resp.text());

    const saved = await resp.json();
    if (!markers.has(saved.id)) {
      allSightings.unshift(saved);
      addMarker(saved);
      updateStats();
    }
    overlay.classList.add("hidden");
    document.getElementById("f-text").value = "";
    document.getElementById("f-postcode").value = "";
    document.getElementById("f-retailer").value = "";
    showToast("Sighting submitted — thank you!");
  } catch (err) {
    formErr.textContent = "Submission failed. Please try again.";
    formErr.classList.remove("hidden");
  } finally {
    btn.disabled = false;
    btn.textContent = "Submit sighting";
  }
});

// ─── Boot ─────────────────────────────────────────────────────────────────────
loadSightings();
setupRealtime();
