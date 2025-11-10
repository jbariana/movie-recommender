import { checkSession, renderMovieTiles } from "./shared.js";

let currentSortOrder = "date"; // "date" | "rating" | "title"
let ratingsData = [];
let favoritesData = [];
let watchlistData = [];

// Tab switching
const tabs = document.querySelectorAll(".profile-tab");
const tabContents = document.querySelectorAll(".profile-tab-content");

tabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    const targetTab = tab.dataset.tab;

    // Update active tab
    tabs.forEach((t) => t.classList.remove("active"));
    tab.classList.add("active");

    // Update active content
    tabContents.forEach((content) => content.classList.remove("active"));
    document.getElementById(`tab-${targetTab}`).classList.add("active");

    // Load data for the tab if needed
    if (targetTab === "ratings" && ratingsData.length === 0) {
      loadRatings();
    } else if (targetTab === "favorites") {
      loadFavorites();
    } else if (targetTab === "watchlist") {
      loadWatchlist();
    } else if (targetTab === "statistics") {
      loadStatistics();
    }
  });
});

// Sort ratings button
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
      (a.title || "").localeCompare(b.title || "", undefined, {
        sensitivity: "base",
      })
    );
  }

  ratingsData = sorted;
  renderRatings();
}

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

    // Update stats
    document.getElementById("total-ratings").textContent = ratingsData.length;

    if (ratingsData.length > 0) {
      const avgRating =
        ratingsData.reduce((sum, r) => sum + (r.rating || 0), 0) /
        ratingsData.length;
      document.getElementById("avg-rating").textContent = avgRating.toFixed(1);
    }

    renderRatings();
  } catch (err) {
    console.error("Failed to load ratings:", err);
    container.innerHTML =
      '<p class="error-message">Failed to load ratings.</p>';
  }
}

function renderRatings() {
  const container = document.getElementById("ratings-list");

  if (ratingsData.length === 0) {
    container.innerHTML =
      '<p class="info-message">No ratings yet. Start rating movies!</p>';
    return;
  }

  container.innerHTML = "";

  ratingsData.forEach((movie) => {
    const item = document.createElement("div");
    item.className = "movie-list-item";

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
        <div class="movie-list-title">${
          movie.title || movie.movie || "Untitled"
        }</div>
        <div class="movie-list-meta">
          ${movie.year ? movie.year + " • " : ""}${movie.genres || ""}
        </div>
      </div>
      <div class="movie-list-rating">
        <span class="rating-stars">${stars}</span>
        <span class="rating-value">${movie.rating || 0}</span>
      </div>
      <div class="movie-list-actions">
        <button class="btn-icon favorite" title="Add to favorites" data-movie-id="${
          movie.movie_id
        }">
          ♥
        </button>
        <button class="btn-icon watchlist" title="Add to watchlist" data-movie-id="${
          movie.movie_id
        }">
          🔖
        </button>
      </div>
    `;

    container.appendChild(item);
  });

  // Add event listeners for favorite/watchlist buttons
  attachActionListeners();
}

function attachActionListeners() {
  document.querySelectorAll(".btn-icon.favorite").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const movieId = btn.dataset.movieId;
      toggleFavorite(movieId, btn);
    });
  });

  document.querySelectorAll(".btn-icon.watchlist").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const movieId = btn.dataset.movieId;
      toggleWatchlist(movieId, btn);
    });
  });
}

function toggleFavorite(movieId, btn) {
  // Check if already in favorites
  const index = favoritesData.findIndex((m) => m.movie_id == movieId);

  if (index >= 0) {
    // Remove from favorites
    favoritesData.splice(index, 1);
    btn.classList.remove("active");
    localStorage.setItem("favorites", JSON.stringify(favoritesData));
    document.getElementById("total-favorites").textContent =
      favoritesData.length;
    if (document.getElementById("tab-favorites").classList.contains("active")) {
      renderFavorites();
    }
  } else {
    // Add to favorites
    const movie = ratingsData.find((m) => m.movie_id == movieId);
    if (movie) {
      favoritesData.push(movie);
      btn.classList.add("active");
      localStorage.setItem("favorites", JSON.stringify(favoritesData));
      document.getElementById("total-favorites").textContent =
        favoritesData.length;
      if (
        document.getElementById("tab-favorites").classList.contains("active")
      ) {
        renderFavorites();
      }
    }
  }
}

function toggleWatchlist(movieId, btn) {
  const index = watchlistData.findIndex((m) => m.movie_id == movieId);

  if (index >= 0) {
    watchlistData.splice(index, 1);
    btn.classList.remove("active");
    localStorage.setItem("watchlist", JSON.stringify(watchlistData));
    document.getElementById("total-watchlist").textContent =
      watchlistData.length;
    if (document.getElementById("tab-watchlist").classList.contains("active")) {
      renderWatchlist();
    }
  } else {
    const movie = ratingsData.find((m) => m.movie_id == movieId);
    if (movie) {
      watchlistData.push(movie);
      btn.classList.add("active");
      localStorage.setItem("watchlist", JSON.stringify(watchlistData));
      document.getElementById("total-watchlist").textContent =
        watchlistData.length;
      if (
        document.getElementById("tab-watchlist").classList.contains("active")
      ) {
        renderWatchlist();
      }
    }
  }
}

function loadFavorites() {
  // Load from localStorage for now (backend will come later)
  const stored = localStorage.getItem("favorites");
  favoritesData = stored ? JSON.parse(stored) : [];
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
  const stored = localStorage.getItem("watchlist");
  watchlistData = stored ? JSON.parse(stored) : [];
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

async function loadStatistics() {
  const container = document.getElementById("statistics-content");
  container.innerHTML = '<p class="loading">Loading statistics...</p>';

  try {
    const response = await fetch("/api/stats", {
      method: "GET",
      credentials: "same-origin",
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const stats = await response.json();

    // Build genre items
    let genreHtml = "";
    if (stats.top_genres && stats.top_genres.length > 0) {
      genreHtml = stats.top_genres
        .map(
          (g, i) => `
        <div class="genre-item">
          <span class="genre-rank">${i + 1}.</span>
          <span class="genre-name">${g.genre || "Unknown"}</span>
          <span class="genre-count">${g.count || 0} movies</span>
        </div>
      `
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

// Initialize
async function init() {
  const username = await checkSession();
  if (!username) {
    window.location.href = "/auth/login";
    return;
  }

  // Load favorites and watchlist from localStorage
  loadFavorites();
  loadWatchlist();

  // Load ratings by default
  await loadRatings();
}

init();
