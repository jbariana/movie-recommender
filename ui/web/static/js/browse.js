/**
 * browse.js
 * Content-based recommendations + optional filter/sort catalog.
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

// ---------------- Content recommendations state ----------------
let contentCurrentPage = 0;
let allContentRecs = [];
const CONTENT_PAGE_SIZE = 30;

// ---------------- Catalog (filter/sort) state ----------------
const genreSelect = document.getElementById("genreSelect");
const sortSelect = document.getElementById("sortSelect");
const dirSelect = document.getElementById("dirSelect");
const applyBtn = document.getElementById("applyFiltersBtn");
const resetBtn = document.getElementById("resetFiltersBtn");
const metaSpan = document.getElementById("browseMeta");
const pager = document.getElementById("browsePager");
const prevBtn = document.getElementById("prevBtn");
const nextBtn = document.getElementById("nextBtn");
const pageInfo = document.getElementById("pageInfo");
const getRecsBtn = document.getElementById("getRecsBtn");

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

// ---- Content-based recommendations with pagination ----
async function loadAllContentRecs() {
  try {
    console.log("Fetching content-based recommendations...");
    const r = await fetch(`/api/recommendations/content?k=100`, {
      credentials: "same-origin",
    });
    if (!r.ok) {
      console.error("Content API returned:", r.status);
      throw new Error(`HTTP ${r.status}`);
    }
    const data = await r.json();
    console.log("Content recommendations received:", data.items?.length || 0);
    if (data.error) {
      console.error("Content API error:", data.error);
      return [];
    }
    return data.items || [];
  } catch (e) {
    console.error("Failed to load content recommendations:", e);
    return [];
  }
}

function renderContentRecsPage() {
  const startIdx = contentCurrentPage * CONTENT_PAGE_SIZE;
  const endIdx = startIdx + CONTENT_PAGE_SIZE;
  const pageMovies = allContentRecs.slice(startIdx, endIdx);

  if (pageMovies.length === 0 && contentCurrentPage > 0) {
    contentCurrentPage = Math.max(
      0,
      Math.floor((allContentRecs.length - 1) / CONTENT_PAGE_SIZE)
    );
    return renderContentRecsPage();
  }

  if (allContentRecs.length === 0) {
    outputDiv.innerHTML =
      '<div class="info-message">No recommendations available. Try rating some movies first!</div>';
    metaSpan.textContent = "";
    pager.style.display = "none";
    return;
  }

  const container = document.createElement("div");
  container.className = "browse-container";

  const grid = document.createElement("div");
  grid.style.display = "grid";
  grid.style.gridTemplateColumns = "repeat(auto-fill, minmax(220px,1fr))";
  grid.style.gap = "1rem";

  for (const m of pageMovies) {
    const card = document.createElement("div");
    card.style.background = "#0b1220";
    card.style.border = "1px solid #1f2937";
    card.style.borderRadius = "12px";
    card.style.padding = ".75rem";
    card.style.color = "#e2e8f0";

    const isSimilarity = typeof m.score === "number" && m.score <= 1.0001;
    const metricLabel = isSimilarity ? "Similarity" : "Weighted rating";
    const metricValue = (m.score ?? 0).toFixed(3);

    card.innerHTML = `
      <div style="font-weight:600;">
        ${m.title ?? "(untitled)"}${m.year ? " (" + m.year + ")" : ""}
      </div>
      <div style="color:#94a3b8;">${m.genres ?? ""}</div>
      <div style="color:#94a3b8;">${metricLabel}: ${metricValue}</div>
    `;

    card.style.cursor = "pointer";
    card.setAttribute("role", "button");
    card.setAttribute("tabindex", "0");
    card.addEventListener("click", () => {
      try {
        showRatingModal(m.movie_id, m.title);
      } catch {}
    });
    card.addEventListener("keypress", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        try {
          showRatingModal(m.movie_id, m.title);
        } catch {}
      }
    });

    grid.appendChild(card);
  }

  container.appendChild(grid);

  // Add pagination controls
  const totalPages = Math.ceil(allContentRecs.length / CONTENT_PAGE_SIZE);
  if (totalPages > 1) {
    const controls = document.createElement("div");
    controls.className = "pagination-controls";

    const prev = document.createElement("button");
    prev.className = "pagination-btn";
    prev.textContent = "← Previous";
    prev.disabled = contentCurrentPage === 0;
    prev.onclick = () => {
      if (contentCurrentPage > 0) {
        contentCurrentPage--;
        renderContentRecsPage();
        window.scrollTo({ top: 0, behavior: "smooth" });
      }
    };

    const next = document.createElement("button");
    next.className = "pagination-btn";
    next.textContent = "Next →";
    next.disabled = endIdx >= allContentRecs.length;
    next.onclick = () => {
      if (endIdx < allContentRecs.length) {
        contentCurrentPage++;
        renderContentRecsPage();
        window.scrollTo({ top: 0, behavior: "smooth" });
      }
    };

    const pageDisplay = document.createElement("span");
    pageDisplay.className = "page-display";
    pageDisplay.textContent = `Page ${contentCurrentPage + 1} of ${totalPages}`;

    controls.appendChild(prev);
    controls.appendChild(pageDisplay);
    controls.appendChild(next);
    container.appendChild(controls);
  }

  outputDiv.innerHTML = "";
  outputDiv.appendChild(container);

  metaSpan.textContent = `Total recommendations: ${allContentRecs.length}`;
  pager.style.display = "none"; // Use inline pagination instead
}

async function loadContentRecs() {
  mode = "recs";
  pager.style.display = "none";
  metaSpan.textContent = "";
  outputDiv.innerHTML = '<div class="loading">Finding picks for you…</div>';

  const recs = await loadAllContentRecs();
  if (recs.length === 0) {
    outputDiv.innerHTML =
      '<div class="info-message">No recommendations available. Try rating some movies first!</div>';
    return;
  }

  allContentRecs = recs;
  contentCurrentPage = 0;
  renderContentRecsPage();
}

// ---------------- New catalog (filter/sort) flow ----------------
function renderCatalog(items, page, total) {
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
    card.innerHTML = `
      <div style="font-weight:600;">${m.title ?? "(untitled)"}${
      m.year ? " (" + m.year + ")" : ""
    }</div>
      <div style="color:#94a3b8;">${m.genres ?? ""}</div>
      <div style="color:#94a3b8;">Avg ★ ${(m.avg_rating ?? 0).toFixed(2)}</div>
    `;

    card.style.cursor = "pointer";
    card.setAttribute("role", "button");
    card.setAttribute("tabindex", "0");
    card.addEventListener("click", () => {
      try {
        showRatingModal(m.movie_id, m.title);
      } catch {}
    });
    card.addEventListener("keypress", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        try {
          showRatingModal(m.movie_id, m.title);
        } catch {}
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
    prevBtn.disabled = !data.has_prev;
    nextBtn.disabled = !data.has_next;
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

    // ✅ Show loading immediately
    outputDiv.innerHTML = '<p class="loading">Loading recommendations...</p>';
    metaSpan.textContent = "";
    pager.style.display = "none";

    // ✅ Load content-based recommendations (don't await - let it happen in background)
    loadContentRecs().catch((err) => {
      console.error("Failed to load recommendations:", err);
      outputDiv.innerHTML =
        '<p class="error-message">Failed to load recommendations. Please try again.</p>';
    });

    // ✅ Load genres in parallel
    fetchGenres().catch((err) => {
      console.warn("Failed to load genres:", err);
    });
  } else {
    renderLoggedOut();
    outputDiv.innerHTML =
      '<p>Please <a href="/">login</a> to see recommendations.</p>';
  }

  setupNavigation();

  const searchInput = document.getElementById("search_input");
  const searchButton = document.getElementById("search_button");
  if (searchInput && searchButton) {
    initSearch(searchInput, searchButton, outputDiv);
  }

  applyBtn?.addEventListener("click", () => {
    state.genre = genreSelect.value;
    state.sort = sortSelect.value;
    state.dir = dirSelect.value;
    state.page = 1;
    loadCatalogPage();
  });

  resetBtn?.addEventListener("click", () => {
    genreSelect.value = "";
    sortSelect.value = "title";
    dirSelect.value = "asc";
    state.genre = "";
    state.sort = "title";
    state.dir = "asc";
    state.page = 1;
    pager.style.display = "none";
    metaSpan.textContent = "";
    loadContentRecs();
  });

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

  getRecsBtn?.addEventListener("click", () => {
    loadContentRecs();
  });

  window.addEventListener("userLoggedIn", async () => {
    await fetchGenres();
    loadContentRecs();
  });
}

init();
