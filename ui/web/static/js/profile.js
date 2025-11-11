// ui/web/static/js/profile.js
import { checkSession, renderMovieTiles } from "./shared.js";

let currentSortOrder = "date"; // "date" | "rating" | "title"
let ratingsData = [];
let favoritesData = [];
let watchlistData = [];

// ===== per-user storage =====
let USERNAME = null;
const favKey = () => (USERNAME ? `favorites:${USERNAME}` : "favorites");
const wlKey  = () => (USERNAME ? `watchlist:${USERNAME}` : "watchlist");

function loadFromStorage(key, fallback = []) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}
function saveToStorage(key, val) {
  try { localStorage.setItem(key, JSON.stringify(val)); } catch {}
}

// ---- tiny helpers -----------------------------------------------------------
function toast(msg, isError = false) {
  const el = document.createElement("div");
  el.className = isError ? "error-message" : "success-message";
  el.style.marginBottom = "0.75rem";
  el.textContent = msg;
  const area = document.getElementById("ratings-list") || document.body;
  area.prepend(el);
  setTimeout(() => el.remove(), 2500);
}

function updateHeaderStats() {
  const totalEl = document.getElementById("total-ratings");
  const avgEl = document.getElementById("avg-rating");
  if (totalEl) totalEl.textContent = ratingsData.length;

  const avg =
    ratingsData.length > 0
      ? ratingsData.reduce((s, r) => s + (r.rating || 0), 0) / ratingsData.length
      : 0;
  if (avgEl) avgEl.textContent = avg.toFixed(1);
}

// ---- Tab switching ----------------------------------------------------------
const tabs = document.querySelectorAll(".profile-tab");
const tabContents = document.querySelectorAll(".profile-tab-content");

function activateTab(tabName) {
  tabs.forEach((t) => {
    const active = t.dataset.tab === tabName;
    t.classList.toggle("active", active);
  });
  tabContents.forEach((c) => {
    c.classList.toggle("active", c.id === `tab-${tabName}`);
  });

  // lazy load per tab
  if (tabName === "ratings" && ratingsData.length === 0) {
    loadRatings();
  } else if (tabName === "favorites") {
    loadFavorites();
  } else if (tabName === "watchlist") {
    loadWatchlist();
  } else if (tabName === "statistics") {
    loadStatistics();
  }
}

tabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    const targetTab = tab.dataset.tab;
    activateTab(targetTab);
    // keep URL in sync (no reload)
    const url = new URL(window.location.href);
    url.searchParams.set("tab", targetTab);
    history.replaceState(null, "", url.toString());
  });
});

// ---- Sort ratings button ----------------------------------------------------
document.getElementById("sort-ratings")?.addEventListener("click", () => {
  if (currentSortOrder === "date") {
    currentSortOrder = "rating";
    document.getElementById("sort-ratings").textContent = "Sort by Rating ▼";
    sortRatings("rating");
  } else if (currentSortOrder === "rating") {
    currentSortOrder = "title";
    document.getElementById("sort-ratings").textContent = "Sort by Title ▼";
    sortRatings("title");
  } else {
    currentSortOrder = "date";
    document.getElementById("sort-ratings").textContent = "Sort by Date ▼";
    sortRatings("date");
  }
});

function sortRatings(by) {
  const sorted = [...ratingsData];

  if (by === "date") {
    sorted.sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0));
  } else if (by === "rating") {
    sorted.sort((a, b) => (b.rating || 0) - (a.rating || 0));
  } else if (by === "title") {
    sorted.sort((a, b) =>
      (a.title || "").localeCompare(b.title || "", undefined, { sensitivity: "base" })
    );
  }

  ratingsData = sorted;
  renderRatings();
}

// ---- Load & render ratings --------------------------------------------------
async function loadRatings() {
  const container = document.getElementById("ratings-list");
  container.innerHTML = '<p class="loading">Loading ratings...</p>';

  try {
    const response = await fetch("/api/button-click", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ button: "view_ratings_button" }),
      credentials: "same-origin",
    });

    const data = await response.json();
    ratingsData = data.ratings || [];

    updateHeaderStats();
    renderRatings();
  } catch (err) {
    console.error("Failed to load ratings:", err);
    container.innerHTML = '<p class="error-message">Failed to load ratings.</p>';
  }
}

function renderRatings() {
  const container = document.getElementById("ratings-list");

  if (ratingsData.length === 0) {
    container.innerHTML =
      '<p class="info-message">No ratings yet. Start rating movies!</p>';
    updateHeaderStats();
    return;
  }

  container.innerHTML = "";

  ratingsData.forEach((movie) => {
    const item = document.createElement("div");
    item.className = "movie-list-item";
    item.dataset.movieId = movie.movie_id;

    const stars = "★".repeat(Math.floor(movie.rating || 0));

    item.innerHTML = `
      <div class="movie-list-poster">
        ${
          movie.poster_url
            ? `<img src="${movie.poster_url}" alt="${movie.title}" style="width:100%;height:100%;object-fit:cover;border-radius:6px;">`
            : "🎬"
        }
      </div>
      <div class="movie-list-info">
        <div class="movie-list-title">${movie.title || movie.movie || "Untitled"}</div>
        <div class="movie-list-meta">
          ${movie.year ? movie.year + " • " : ""}${movie.genres || ""}
        </div>
      </div>
      <div class="movie-list-rating">
        <span class="rating-stars">${stars}</span>
        <span class="rating-value">${movie.rating || 0}</span>
      </div>
      <div class="movie-list-actions">
        <button class="btn-icon favorite"  title="Add to favorites" data-movie-id="${movie.movie_id}">♥</button>
        <button class="btn-icon watchlist" title="Add to watchlist" data-movie-id="${movie.movie_id}">🔖</button>
        <button class="btn-icon remove"    title="Remove rating"    data-movie-id="${movie.movie_id}">🗑️</button>
      </div>
    `;

    container.appendChild(item);
  });

  attachActionListeners();
}

function attachActionListeners() {
  document.querySelectorAll(".btn-icon.favorite").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      toggleFavorite(btn.dataset.movieId, btn);
    });
  });

  document.querySelectorAll(".btn-icon.watchlist").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      toggleWatchlist(btn.dataset.movieId, btn);
    });
  });

  document.querySelectorAll(".btn-icon.remove").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      e.stopPropagation();
      await deleteRating(btn.dataset.movieId);
    });
  });
}

async function deleteRating(movieId) {
  try {
    const res = await fetch("/api/button-click", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "same-origin",
      body: JSON.stringify({ button: "remove_rating", movie_id: movieId }),
    });
    const data = await res.json();

    if (!res.ok || data?.error) {
      toast(data?.error || `Failed to remove rating for ${movieId}`, true);
      return;
    }

    ratingsData = ratingsData.filter((m) => String(m.movie_id) !== String(movieId));
    renderRatings();
    updateHeaderStats();
    toast(data?.message || "Rating removed.");
  } catch (err) {
    console.error(err);
    toast("Error contacting backend.", true);
  }
}

// ---- Favorites & Watchlist (per-user local) --------------------------------
function toggleFavorite(movieId, btn) {
  const idx = favoritesData.findIndex((m) => String(m.movie_id) === String(movieId));

  if (idx >= 0) {
    favoritesData.splice(idx, 1);
    btn.classList.remove("active");
  } else {
    const movie = ratingsData.find((m) => String(m.movie_id) === String(movieId));
    if (movie) {
      favoritesData.push(movie);
      btn.classList.add("active");
    }
  }

  saveToStorage(favKey(), favoritesData);
  document.getElementById("total-favorites").textContent = favoritesData.length;
  if (document.getElementById("tab-favorites").classList.contains("active")) {
    renderFavorites();
  }
}

function toggleWatchlist(movieId, btn) {
  const idx = watchlistData.findIndex((m) => String(m.movie_id) === String(movieId));

  if (idx >= 0) {
    watchlistData.splice(idx, 1);
    btn.classList.remove("active");
  } else {
    const movie = ratingsData.find((m) => String(m.movie_id) === String(movieId));
    if (movie) {
      watchlistData.push(movie);
      btn.classList.add("active");
    }
  }

  saveToStorage(wlKey(), watchlistData);
  document.getElementById("total-watchlist").textContent = watchlistData.length;
  if (document.getElementById("tab-watchlist").classList.contains("active")) {
    renderWatchlist();
  }
}

function loadFavorites() {
  favoritesData = loadFromStorage(favKey(), []);
  document.getElementById("total-favorites").textContent = favoritesData.length;
  renderFavorites();
}

function renderFavorites() {
  const container = document.getElementById("favorites-list");

  if (favoritesData.length === 0) {
    container.innerHTML =
      '<p class="info-message">No favorites yet. Click the ♥ icon on any movie to add it!</p>';
    return;
  }

  const grid = renderMovieTiles(favoritesData);
  container.innerHTML = "";
  container.appendChild(grid);
}

function loadWatchlist() {
  watchlistData = loadFromStorage(wlKey(), []);
  document.getElementById("total-watchlist").textContent = watchlistData.length;
  renderWatchlist();
}

function renderWatchlist() {
  const container = document.getElementById("watchlist-list");

  if (watchlistData.length === 0) {
    container.innerHTML =
      '<p class="info-message">No movies in watchlist. Click the 🔖 icon to add movies!</p>';
    return;
  }

  const grid = renderMovieTiles(watchlistData);
  container.innerHTML = "";
  container.appendChild(grid);
}

// ---- Statistics -------------------------------------------------------------
async function loadStatistics() {
  const container = document.getElementById("statistics-content");
  container.innerHTML = '<p class="loading">Loading statistics...</p>';

  try {
    const response = await fetch("/api/stats", {
      method: "GET",
      credentials: "same-origin",
    });

    if (!response.ok) throw new Error(`HTTP ${response.status}`);

    const stats = await response.json();

    let genreHtml = "";
    if (stats.top_genres && stats.top_genres.length > 0) {
      genreHtml = stats.top_genres
        .map(
          (g, i) => `
        <div class="genre-item">
          <span class="genre-rank">${i + 1}.</span>
          <span class="genre-name">${g.genre || "Unknown"}</span>
          <span class="genre-count">${g.count || 0} movies</span>
        </div>`
        )
        .join("");
    } else {
      genreHtml = '<p class="info-message">No genre data available</p>';
    }

    container.innerHTML = `
      <div class="stats-card">
        <h3>Rating Summary</h3>
        <div class="stat-item">
          <span class="stat-label">Total Ratings</span>
          <span class="stat-value">${stats.total_ratings || 0}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">Average Rating</span>
          <span class="stat-value">${
            stats.average_rating ? stats.average_rating.toFixed(2) : "0.00"
          } ★</span>
        </div>
      </div>

      <div class="stats-card">
        <h3>Top Genres</h3>
        ${genreHtml}
      </div>
    `;
  } catch (err) {
    console.error("Failed to load statistics:", err);
    container.innerHTML =
      '<p class="error-message">Failed to load statistics. Please try again.</p>';
  }
}

// ---- Initialize -------------------------------------------------------------
async function init() {
  USERNAME = await checkSession();
  if (!USERNAME) {
    window.location.href = "/auth/login";
    return;
  }

  // load per-user lists
  loadFavorites();
  loadWatchlist();

  // pick initial tab from ?tab= or #hash; default "ratings"
  const url = new URL(window.location.href);
  const requested =
    url.searchParams.get("tab") ||
    (window.location.hash ? window.location.hash.substring(1) : null) ||
    "ratings";

  const valid = ["ratings", "favorites", "watchlist", "statistics"];
  const initialTab = valid.includes(requested) ? requested : "ratings";

  activateTab(initialTab);
}

init();
