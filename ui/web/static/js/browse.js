/**
 * browse.js
 * Content-based recommendations + optional filter/sort catalog.
 */

// ✅ Import all necessary functions from shared.js
import {
  initLoginUI,
  renderLoggedIn,
  renderLoggedOut,
  checkSession,
  setupNavigation,
} from "./shared.js";
import { initSearch } from "./search.js";
import { showRatingModal } from "./ratingModal.js";
import {
  getCachedRecommendations,
  getRecommendations,
  preloadRecommendations,
  invalidateCache,
} from "./recsCache.js";

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

function readUrlParams() {
  const u = new URLSearchParams(window.location.search);
  return {
    genre: u.get("genre") || "",
    sort: u.get("sort") || "title",
    dir: u.get("dir") || "asc",
    page: parseInt(u.get("page") || "1", 10),
  };
}

function writeUrlParams(params, replace = false) {
  const current = new URL(window.location.href);
  const merged = {
    genre: params.genre ?? state.genre,
    sort: params.sort ?? state.sort,
    dir: params.dir ?? state.dir,
    page: params.page ?? state.page,
  };
  // Drop empty params for clean URLs
  const qs = toQuery({
    genre: merged.genre || undefined,
    sort: merged.sort || undefined,
    dir: merged.dir || undefined,
    page: merged.page > 1 ? merged.page : undefined,
  });
  const nextUrl = `${current.pathname}${qs ? "?" + qs : ""}`;
  if (replace) {
    history.replaceState(null, "", nextUrl);
  } else {
    history.pushState(null, "", nextUrl);
  }
}

// ✅ Helper to get first genre
function getFirstGenre(genresString) {
  if (!genresString) return "";
  const genres = genresString
    .split("|")
    .map((g) => g.trim())
    .filter((g) => g);
  return genres.length > 0 ? genres[0] : "";
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

// ---- Content-based recommendations with caching ----
async function loadAllContentRecs() {
  try {
    console.log("📊 Loading content-based recommendations...");

    // Try to get cached recommendations first
    let recs = getCachedRecommendations();

    if (recs && recs.length > 0) {
      console.log(`⚡ Using ${recs.length} cached recommendations (instant!)`);
      return recs;
    }

    // If not cached, wait for them to load
    console.log("⏳ Waiting for recommendations to load...");
    recs = await getRecommendations();

    if (!recs || recs.length === 0) {
      console.warn("⚠️ No recommendations available");
      return [];
    }

    return recs;
  } catch (e) {
    console.error("❌ Failed to load content recommendations:", e);
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
  grid.className = "movie-grid";

  for (const m of pageMovies) {
    const card = document.createElement("div");
    card.className = "movie-tile";
    card.style.cursor = "pointer";

    // ✅ Use poster_url if available
    const posterHtml = m.poster_url
      ? `<img src="${m.poster_url}" alt="${m.title}" class="movie-poster-img" loading="lazy">`
      : `<div class="movie-poster-tile">🎬</div>`;

    // ✅ Get only first genre
    const firstGenre = getFirstGenre(m.genres);
    const metaText = `${m.year || ""} ${firstGenre ? "• " + firstGenre : ""}`;

    const isSimilarity = typeof m.score === "number" && m.score <= 1.0001;
    const metricLabel = isSimilarity ? "Similarity" : "Score";
    const metricValue = (m.score ?? 0).toFixed(3);

    card.innerHTML = `
      ${posterHtml}
      <div class="movie-tile-title">${m.title ?? "(untitled)"}</div>
      <div class="movie-tile-meta">${metaText}</div>
      <div class="movie-tile-meta">${metricLabel}: ${metricValue}</div>
    `;

    card.addEventListener("click", () => {
      try {
        showRatingModal(m.movie_id, m.title);
      } catch (err) {
        console.error("Failed to open rating modal:", err);
      }
    });

    card.addEventListener("keypress", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        try {
          showRatingModal(m.movie_id, m.title);
        } catch (err) {
          console.error("Failed to open rating modal:", err);
        }
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

  // Show loading state (will be instant if cached)
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
  grid.className = "movie-grid";

  for (const m of items) {
    const card = document.createElement("div");
    card.className = "movie-tile";
    card.style.cursor = "pointer";

    // ✅ Use poster_url if available
    const posterHtml = m.poster_url
      ? `<img src="${m.poster_url}" alt="${m.title}" class="movie-poster-img" loading="lazy">`
      : `<div class="movie-poster-tile">🎬</div>`;

    // ✅ Get only first genre
    const firstGenre = getFirstGenre(m.genres);
    const metaText = `${m.year || ""} ${firstGenre ? "• " + firstGenre : ""}`;

    card.innerHTML = `
      ${posterHtml}
      <div class="movie-tile-title">${m.title ?? "(untitled)"}</div>
      <div class="movie-tile-meta">${metaText}</div>
      <div class="movie-tile-rating">★ ${(m.avg_rating ?? 0).toFixed(2)}</div>
    `;

    card.addEventListener("click", () => {
      try {
        showRatingModal(m.movie_id, m.title);
      } catch (err) {
        console.error("Failed to open rating modal:", err);
      }
    });

    card.addEventListener("keypress", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        try {
          showRatingModal(m.movie_id, m.title);
        } catch (err) {
          console.error("Failed to open rating modal:", err);
        }
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

    // 🔥 Preload recommendations in the background immediately after login
    preloadRecommendations().catch((err) => {
      console.warn("Background preload failed:", err);
    });
  } else {
    renderLoggedOut();
  }

  setupNavigation();

  const searchInput = document.getElementById("search_input");
  const searchButton = document.getElementById("search_button");
  if (searchInput && searchButton) {
    initSearch(searchInput, searchButton, outputDiv);
  }

  // Always fetch genres first so we can preselect from URL
  await fetchGenres();

  // Read URL params (supports chips like /browse?genre=Action)
  const params = readUrlParams();
  if (genreSelect) genreSelect.value = params.genre || "";
  if (sortSelect) sortSelect.value = params.sort || "title";
  if (dirSelect) dirSelect.value = params.dir || "asc";

  state.genre = params.genre || "";
  state.sort = params.sort || "title";
  state.dir = params.dir || "asc";
  state.page =
    Number.isFinite(params.page) && params.page > 0 ? params.page : 1;

  if (state.genre) {
    // If a genre is preselected via URL, show catalog immediately
    writeUrlParams({}, true); // normalize/clean URL (remove empty params)
    await loadCatalogPage();
  } else if (username) {
    // Default for logged-in users: recommendations
    outputDiv.innerHTML = '<p class="loading">Loading recommendations...</p>';
    metaSpan && (metaSpan.textContent = "");
    pager && (pager.style.display = "none");
    await loadContentRecs();
  } else {
    // Not logged in: show catalog
    await loadCatalogPage();
  }

  // ---- Controls ----
  applyBtn?.addEventListener("click", () => {
    state.genre = genreSelect.value;
    state.sort = sortSelect.value;
    state.dir = dirSelect.value;
    state.page = 1;
    writeUrlParams({}); // reflect filters in URL
    loadCatalogPage();
  });

  resetBtn?.addEventListener("click", () => {
    if (genreSelect) genreSelect.value = "";
    if (sortSelect) sortSelect.value = "title";
    if (dirSelect) dirSelect.value = "asc";
    state.genre = "";
    state.sort = "title";
    state.dir = "asc";
    state.page = 1;
    pager && (pager.style.display = "none");
    metaSpan && (metaSpan.textContent = "");
    // Clean the URL and go back to recs if logged in, else catalog
    writeUrlParams({ genre: "", page: 1 }, true);
    if (username) {
      loadContentRecs();
    } else {
      loadCatalogPage();
    }
  });

  prevBtn?.addEventListener("click", () => {
    if (mode !== "catalog") return;
    if (state.page > 1) {
      state.page -= 1;
      writeUrlParams({ page: state.page });
      loadCatalogPage();
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  });

  nextBtn?.addEventListener("click", () => {
    if (mode !== "catalog") return;
    state.page += 1;
    writeUrlParams({ page: state.page });
    loadCatalogPage();
    window.scrollTo({ top: 0, behavior: "smooth" });
  });

  getRecsBtn?.addEventListener("click", () => {
    // Switch to recommendations view
    writeUrlParams({ genre: "", page: 1 }, true);
    loadContentRecs();
  });

  // Handle browser back/forward to keep filters in sync
  window.addEventListener("popstate", () => {
    const p = readUrlParams();
    if (genreSelect) genreSelect.value = p.genre || "";
    if (sortSelect) sortSelect.value = p.sort || "title";
    if (dirSelect) dirSelect.value = p.dir || "asc";
    state.genre = p.genre || "";
    state.sort = p.sort || "title";
    state.dir = p.dir || "asc";
    state.page = Number.isFinite(p.page) && p.page > 0 ? p.page : 1;
    if (state.genre || mode === "catalog") {
      loadCatalogPage();
    } else {
      loadContentRecs();
    }
  });

  // Listen for rating updates to invalidate cache
  window.addEventListener("ratingUpdated", () => {
    console.log("🔄 Rating updated - invalidating cache");
    invalidateCache();
    // Preload new recommendations in background
    if (username) {
      preloadRecommendations();
    }
  });

  // Also refresh recs on login event
  window.addEventListener("userLoggedIn", async () => {
    await fetchGenres();
    // Preload immediately
    preloadRecommendations();
    loadContentRecs();
  });
}

init();
