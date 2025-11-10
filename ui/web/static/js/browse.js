/**
 * browse.js
 * Existing recommendations view + new optional filter/sort catalog.
 */

import { isLoggedIn } from "./utils.js";
import { showRatingModal } from "./ratingModal.js";
import {
  initLoginUI,
  renderLoggedIn,
  renderLoggedOut,
  checkSession,
  setupNavigation,
  renderMovieTiles,
} from "./shared.js";
import { initSearch } from "./search.js";

const outputDiv = document.getElementById("output");

// ---------------- Existing recommendations state ----------------
let recCurrentPage = 0;
let allRecommendations = [];
const REC_PAGE_SIZE = 30;

// ---------------- Catalog (filter/sort) state ----------------
const genreSelect = document.getElementById("genreSelect");
const sortSelect  = document.getElementById("sortSelect");
const dirSelect   = document.getElementById("dirSelect");
const applyBtn    = document.getElementById("applyFiltersBtn");
const resetBtn    = document.getElementById("resetFiltersBtn");
const metaSpan    = document.getElementById("browseMeta");
const pager       = document.getElementById("browsePager");
const prevBtn     = document.getElementById("prevBtn");
const nextBtn     = document.getElementById("nextBtn");
const pageInfo    = document.getElementById("pageInfo");
const getRecsBtn  = document.getElementById("getRecsBtn");

let mode = "recs"; // "recs" | "catalog"
const state = {
  genre: "",
  sort: "title",
  dir: "asc",
  page: 1,
  page_size: 20,
  total: 0,
};

function toQuery(o) {
  const p = new URLSearchParams();
  for (const [k, v] of Object.entries(o)) {
    if (v !== "" && v != null) p.set(k, v);
  }
  return p.toString();
}

// ---------------- API helpers for new catalog ----------------
async function fetchGenres() {
  try {
    const r = await fetch("/api/genres");
    if (!r.ok) return;
    const data = await r.json();
    for (const g of data.genres || []) {
      const opt = document.createElement("option");
      opt.value = g;
      opt.textContent = g;
      genreSelect.appendChild(opt);
    }
  } catch (e) {
    console.warn("genres fetch failed", e);
  }
}

async function fetchMoviesPage() {
  const q = toQuery({
    genre: state.genre,
    sort: state.sort,
    dir: state.dir,
    page: state.page,
    page_size: state.page_size,
  });
  const r = await fetch(`/api/movies?${q}`);
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

// ---------------- Existing recommendations flow ----------------
async function loadAllRecommendations() {
  try {
    const response = await fetch("/api/button-click", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ button: "get_rec_button" }),
      credentials: "same-origin",
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    if (data.error) return [];
    return data.ratings || [];
  } catch (error) {
    console.error("Failed to load recommendations:", error);
    return [];
  }
}

function renderRecsPage() {
  const startIdx = recCurrentPage * REC_PAGE_SIZE;
  const endIdx = startIdx + REC_PAGE_SIZE;
  const pageMovies = allRecommendations.slice(startIdx, endIdx);

  if (pageMovies.length === 0 && recCurrentPage > 0) {
    recCurrentPage = Math.max(0, Math.floor((allRecommendations.length - 1) / REC_PAGE_SIZE));
    return renderRecsPage();
  }

  if (allRecommendations.length === 0) {
    outputDiv.innerHTML = '<div class="info-message">No recommendations available.</div>';
    return;
  }

  const container = document.createElement("div");
  container.className = "browse-container";
  const grid = renderMovieTiles(pageMovies);
  container.appendChild(grid);

  const totalPages = Math.ceil(allRecommendations.length / REC_PAGE_SIZE);
  if (totalPages > 1) {
    const controls = document.createElement("div");
    controls.className = "pagination-controls";

    const prev = document.createElement("button");
    prev.className = "pagination-btn";
    prev.textContent = "← Previous";
    prev.disabled = recCurrentPage === 0;
    prev.onclick = () => {
      if (recCurrentPage > 0) {
        recCurrentPage--;
        renderRecsPage();
        window.scrollTo({ top: 0, behavior: "smooth" });
      }
    };

    const next = document.createElement("button");
    next.className = "pagination-btn";
    next.textContent = "Next →";
    next.disabled = endIdx >= allRecommendations.length;
    next.onclick = () => {
      if (endIdx < allRecommendations.length) {
        recCurrentPage++;
        renderRecsPage();
        window.scrollTo({ top: 0, behavior: "smooth" });
      }
    };

    controls.appendChild(prev);
    controls.appendChild(next);
    container.appendChild(controls);
  }

  outputDiv.innerHTML = "";
  outputDiv.appendChild(container);
}

// ---- New: content-based recs via /api/recommendations/content ----
function renderContentRecs(items) {
  // Simple neutral cards (don’t rely on renderMovieTiles)
  const container = document.createElement("div");
  container.className = "browse-container";

  const grid = document.createElement("div");
  grid.style.display = "grid";
  grid.style.gridTemplateColumns = "repeat(auto-fill, minmax(220px,1fr))";
  grid.style.gap = "1rem";

  for (const m of items) {
    const card = document.createElement("div");
    card.style.background = "#0b1220";
    card.style.border = "1px solid #1f2937";
    card.style.borderRadius = "12px";
    card.style.padding = ".75rem";
    card.style.color = "#e2e8f0";

    // If score <= 1 → cosine similarity; else → weighted average rating (cold start)
    const isSimilarity = typeof m.score === "number" && m.score <= 1.0001;
    const metricLabel  = isSimilarity ? "Similarity" : "Weighted rating";
    const metricValue  = (m.score ?? 0).toFixed(3);

    card.innerHTML = `
      <div style="font-weight:600;">
        ${m.title ?? "(untitled)"}${m.year ? " (" + m.year + ")" : ""}
      </div>
      <div style="color:#94a3b8;">${m.genres ?? ""}</div>
      <div style="color:#94a3b8;">${metricLabel}: ${metricValue}</div>
    `;

    // Make the card clickable to rate
    card.style.cursor = "pointer";
    card.setAttribute("role", "button");
    card.setAttribute("tabindex", "0");
    card.addEventListener("click", () => {
      try { showRatingModal(m.movie_id, m.title); } catch {}
    });
    card.addEventListener("keypress", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        try { showRatingModal(m.movie_id, m.title); } catch {}
      }
    });

    grid.appendChild(card);
  }

  container.appendChild(grid);
  outputDiv.innerHTML = "";
  outputDiv.appendChild(container);
  metaSpan.textContent = `Personalized picks: ${items.length}`;
  pager.style.display = "none";
}

async function loadContentRecs(k = 12) {
  mode = "recs";
  pager.style.display = "none";
  metaSpan.textContent = "";
  outputDiv.innerHTML = '<div class="loading">Finding picks for you…</div>';

  try {
    const r = await fetch(`/api/recommendations/content?k=${k}`, { credentials: "same-origin" });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const data = await r.json();
    if (data.error) {
      outputDiv.innerHTML = `<div class="info-message">${data.error}</div>`;
      return;
    }
    renderContentRecs(data.items || []);
  } catch (e) {
    console.error(e);
    outputDiv.innerHTML = `<div class="error-message">Failed: ${e.message}</div>`;
  }
}

async function loadRecommendations() {
  mode = "recs";
  pager.style.display = "none";
  metaSpan.textContent = "";
  outputDiv.innerHTML = '<div class="loading">Loading recommendations...</div>';

  const recs = await loadAllRecommendations();
  if (recs.length === 0) {
    outputDiv.innerHTML = '<div class="info-message">No recommendations available. Try rating some movies first!</div>';
    return;
  }
  allRecommendations = recs;
  recCurrentPage = 0;
  renderRecsPage();
}

// ---------------- New catalog (filter/sort) flow ----------------
function renderCatalog(items, page, total) {
  const container = document.createElement("div");
  container.className = "browse-container";

  // Simple neutral cards (don’t rely on renderMovieTiles format)
  const grid = document.createElement("div");
  grid.style.display = "grid";
  grid.style.gridTemplateColumns = "repeat(auto-fill, minmax(220px,1fr))";
  grid.style.gap = "1rem";

  for (const m of items) {
    const card = document.createElement("div");
    card.style.background = "#0b1220";
    card.style.border = "1px solid #1f2937";
    card.style.borderRadius = "12px";
    card.style.padding = ".75rem";
    card.style.color = "#e2e8f0";
    card.innerHTML = `
      <div style="font-weight:600;">${m.title ?? "(untitled)"}${m.year ? " ("+m.year+")" : ""}</div>
      <div style="color:#94a3b8;">${m.genres ?? ""}</div>
      <div style="color:#94a3b8;">Avg ★ ${(m.avg_rating ?? 0).toFixed(2)}</div>
    `;

    // Make the card clickable to rate
    card.style.cursor = "pointer";
    card.setAttribute("role", "button");
    card.setAttribute("tabindex", "0");
    card.addEventListener("click", () => {
      try { showRatingModal(m.movie_id, m.title); } catch {}
    });
    card.addEventListener("keypress", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        try { showRatingModal(m.movie_id, m.title); } catch {}
      }
    });

    grid.appendChild(card);
  }

  container.appendChild(grid);
  outputDiv.innerHTML = "";
  outputDiv.appendChild(container);

  metaSpan.textContent = `Total: ${total}`;
  pageInfo.textContent = `Page ${page}`;
  pager.style.display = "flex";
}

async function loadCatalogPage() {
  mode = "catalog";
  outputDiv.innerHTML = '<div class="loading">Loading…</div>';
  try {
    const data = await fetchMoviesPage();
    renderCatalog(data.items || [], data.page || 1, data.total || 0);
    prevBtn.disabled = !(data.has_prev);
    nextBtn.disabled = !(data.has_next);
  } catch (e) {
    console.error(e);
    outputDiv.innerHTML = `<div class="error-message">Failed: ${e.message}</div>`;
  }
}

// ---------------- init ----------------
async function init() {
  initLoginUI();

  const username = await checkSession();
  if (username) {
    renderLoggedIn(username);
    // load genres for the new controls
    await fetchGenres();
    // default view = your existing recommendations
    await loadRecommendations();
  } else {
    renderLoggedOut();
    outputDiv.innerHTML = '<p>Please <a href="/">login</a> to see recommendations.</p>';
  }

  setupNavigation();

  // wire search (unchanged)
  const searchInput = document.getElementById("search_input");
  const searchButton = document.getElementById("search_button");
  if (searchInput && searchButton) {
    initSearch(searchInput, searchButton, outputDiv);
  }

  // controls: apply → switch to catalog
  applyBtn?.addEventListener("click", () => {
    state.genre = genreSelect.value;
    state.sort  = sortSelect.value;
    state.dir   = dirSelect.value;
    state.page  = 1;
    loadCatalogPage();
  });

  // controls: reset → back to recommendations
  resetBtn?.addEventListener("click", () => {
    genreSelect.value = "";
    sortSelect.value  = "title";
    dirSelect.value   = "asc";
    state.genre = "";
    state.sort  = "title";
    state.dir   = "asc";
    state.page  = 1;
    pager.style.display = "none";
    metaSpan.textContent = "";
    loadRecommendations();
  });

  // pager
  prevBtn?.addEventListener("click", () => {
    if (mode !== "catalog") return;
    if (state.page > 1) {
      state.page -= 1;
      loadCatalogPage();
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  });
  nextBtn?.addEventListener("click", () => {
    if (mode !== "catalog") return;
    state.page += 1;
    loadCatalogPage();
    window.scrollTo({ top: 0, behavior: "smooth" });
  });

  // "Get Recommendations" button → call content-based endpoint
  getRecsBtn?.addEventListener("click", () => {
    loadContentRecs(12);
  });

  // in case user logs in from another tab and fires this event
  window.addEventListener("userLoggedIn", async () => {
    await fetchGenres();
    await loadRecommendations();
  });
}

init();
