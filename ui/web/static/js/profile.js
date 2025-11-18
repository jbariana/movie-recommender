/**
 * profile.js
 * Profile page functionality
 */

import { showRatingModal } from "./ratingModal.js";

let currentUsername = null;

// Get DOM elements
const profileAvatar = document.getElementById("profile-avatar");
const profileUsername = document.getElementById("profile-username");
const statRatings = document.getElementById("stat-ratings");
const statWatchlist = document.getElementById("stat-watchlist");
const statFavorites = document.getElementById("stat-favorites");

const ratingsContent = document.getElementById("ratings-content");
const watchlistContent = document.getElementById("watchlist-content");
const favoritesContent = document.getElementById("favorites-content");
const statisticsContent = document.getElementById("statistics-content");

// ✅ Helper to get first genre
function getFirstGenre(genresString) {
  if (!genresString) return "";
  const genres = genresString
    .split("|")
    .map((g) => g.trim())
    .filter((g) => g);
  return genres.length > 0 ? genres[0] : "";
}

// Load ratings
async function loadRatings() {
  ratingsContent.innerHTML = '<p class="loading">Loading ratings...</p>';

  try {
    const response = await fetch("/api/button-click", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "same-origin",
      body: JSON.stringify({ button: "view_ratings_button" }),
    });

    const data = await response.json();
    let ratings = data.ratings || [];

    if (ratings.length === 0) {
      ratingsContent.innerHTML =
        '<p class="info-message">You haven\'t rated any movies yet.</p>';
      return;
    }

    // ✅ Fetch missing movie details (including poster_url) in parallel
    const enhancedRatings = await Promise.all(
      ratings.map(async (rating) => {
        // If poster_url is missing or null, fetch movie details
        if (!rating.poster_url) {
          try {
            const res = await fetch(`/api/movies/${rating.movie_id}`);
            if (res.ok) {
              const movie = await res.json();
              return {
                ...rating,
                poster_url: movie.poster_url,
                genres: movie.genres || rating.genres,
                year: movie.year || rating.year,
              };
            }
          } catch (err) {
            console.warn(`Failed to fetch movie ${rating.movie_id}:`, err);
          }
        }
        return rating;
      })
    );

    renderMovieList(enhancedRatings, ratingsContent, "rating");
  } catch (err) {
    console.error("Failed to load ratings:", err);
    ratingsContent.innerHTML =
      '<p class="error-message">Failed to load ratings.</p>';
  }
}

async function loadWatchlist() {
  const container = document.getElementById("watchlist-content");
  container.innerHTML = '<p class="loading">Loading watchlist...</p>';

  const username = sessionStorage.getItem("username");
  if (!username) {
    container.innerHTML =
      '<p class="info-message">Please log in to view watchlist.</p>';
    return;
  }

  try {
    const key = `watchlist:${username}`;
    const stored = localStorage.getItem(key);
    const watchlist = stored ? JSON.parse(stored) : [];

    if (watchlist.length === 0) {
      container.innerHTML =
        '<p class="info-message">No movies in watchlist. Add some movies to watch later!</p>';
      return;
    }

    const moviePromises = watchlist.map(async (wl) => {
      try {
        const res = await fetch(`/api/movies/${wl.movie_id}`);
        if (!res.ok) return null;
        const movie = await res.json();
        return {
          ...movie,
          added_at: wl.timestamp,
        };
      } catch {
        return null;
      }
    });

    const movies = (await Promise.all(moviePromises)).filter((m) => m !== null);
    movies.sort((a, b) => (b.added_at || 0) - (a.added_at || 0));

    const grid = document.createElement("div");
    grid.className = "movie-grid";

    movies.forEach((m) => {
      const card = document.createElement("div");
      card.className = "movie-tile";
      card.style.cursor = "pointer";

      const posterHtml = m.poster_url
        ? `<img src="${m.poster_url}" alt="${m.title}" class="movie-poster-img" loading="lazy">`
        : `<div class="movie-poster-tile">🎬</div>`;

      // ✅ Use only first genre
      const firstGenre = getFirstGenre(m.genres);
      const metaText = `${m.year || ""} ${firstGenre ? "• " + firstGenre : ""}`;

      card.innerHTML = `
        ${posterHtml}
        <div class="movie-tile-title">${m.title || "Untitled"}</div>
        <div class="movie-tile-meta">${metaText}</div>
        <div class="movie-tile-actions">
          <button class="btn-icon btn-watchlist active" data-movie-id="${
            m.movie_id
          }" title="Remove from watchlist">
            🔖
          </button>
        </div>
      `;

      card.addEventListener("click", (e) => {
        if (!e.target.closest(".btn-icon")) {
          showRatingModal(m.movie_id, m.title);
        }
      });

      const watchlistBtn = card.querySelector(".btn-watchlist");
      watchlistBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        if (confirm(`Remove "${m.title}" from watchlist?`)) {
          watchlist.splice(
            watchlist.findIndex(
              (w) => String(w.movie_id) === String(m.movie_id)
            ),
            1
          );
          localStorage.setItem(key, JSON.stringify(watchlist));
          loadWatchlist();
        }
      });

      grid.appendChild(card);
    });

    container.innerHTML = "";
    container.appendChild(grid);
  } catch (err) {
    console.error("Failed to load watchlist:", err);
    container.innerHTML =
      '<p class="error-message">Failed to load watchlist.</p>';
  }
}

async function loadFavorites() {
  const container = document.getElementById("favorites-content");
  container.innerHTML = '<p class="loading">Loading favorites...</p>';

  const username = sessionStorage.getItem("username");
  if (!username) {
    container.innerHTML =
      '<p class="info-message">Please log in to view favorites.</p>';
    return;
  }

  try {
    const key = `favorites:${username}`;
    const stored = localStorage.getItem(key);
    const favorites = stored ? JSON.parse(stored) : [];

    if (favorites.length === 0) {
      container.innerHTML =
        '<p class="info-message">No favorites yet. Add movies to your favorites!</p>';
      return;
    }

    const moviePromises = favorites.map(async (fav) => {
      try {
        const res = await fetch(`/api/movies/${fav.movie_id}`);
        if (!res.ok) return null;
        const movie = await res.json();
        return {
          ...movie,
          favorited_at: fav.timestamp,
        };
      } catch {
        return null;
      }
    });

    const movies = (await Promise.all(moviePromises)).filter((m) => m !== null);
    movies.sort((a, b) => (b.favorited_at || 0) - (a.favorited_at || 0));

    const grid = document.createElement("div");
    grid.className = "movie-grid";

    movies.forEach((m) => {
      const card = document.createElement("div");
      card.className = "movie-tile";
      card.style.cursor = "pointer";

      const posterHtml = m.poster_url
        ? `<img src="${m.poster_url}" alt="${m.title}" class="movie-poster-img" loading="lazy">`
        : `<div class="movie-poster-tile">🎬</div>`;

      // ✅ Use only first genre
      const firstGenre = getFirstGenre(m.genres);
      const metaText = `${m.year || ""} ${firstGenre ? "• " + firstGenre : ""}`;

      card.innerHTML = `
        ${posterHtml}
        <div class="movie-tile-title">${m.title || "Untitled"}</div>
        <div class="movie-tile-meta">${metaText}</div>
        <div class="movie-tile-actions">
          <button class="btn-icon btn-favorite active" data-movie-id="${
            m.movie_id
          }" title="Remove from favorites">
            ♥
          </button>
        </div>
      `;

      card.addEventListener("click", (e) => {
        if (!e.target.closest(".btn-icon")) {
          showRatingModal(m.movie_id, m.title);
        }
      });

      const favoriteBtn = card.querySelector(".btn-favorite");
      favoriteBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        if (confirm(`Remove "${m.title}" from favorites?`)) {
          favorites.splice(
            favorites.findIndex(
              (f) => String(f.movie_id) === String(m.movie_id)
            ),
            1
          );
          localStorage.setItem(key, JSON.stringify(favorites));
          loadFavorites();
        }
      });

      grid.appendChild(card);
    });

    container.innerHTML = "";
    container.appendChild(grid);
  } catch (err) {
    console.error("Failed to load favorites:", err);
    container.innerHTML =
      '<p class="error-message">Failed to load favorites.</p>';
  }
}

function renderMovieList(movies, container, type) {
  const grid = document.createElement("div");
  grid.className = "movie-grid";

  movies.forEach((movie) => {
    const card = document.createElement("div");
    card.className = "movie-tile";
    card.style.cursor = "pointer";

    const posterHtml = movie.poster_url
      ? `<img src="${movie.poster_url}" alt="${movie.title}" class="movie-poster-img" loading="lazy">`
      : `<div class="movie-poster-tile">🎬</div>`;

    // ✅ Use only first genre
    const firstGenre = getFirstGenre(movie.genres);

    let metaText = "";
    let ratingText = "";

    if (type === "rating") {
      // For ratings tab, show rating prominently
      const meta = `${movie.year || ""} ${firstGenre ? "• " + firstGenre : ""}`;
      metaText = `<div class="movie-tile-meta">${meta}</div>`;
      ratingText = `<div class="movie-tile-rating">★ ${
        movie.rating || 0
      }/5</div>`;
    } else {
      // For other tabs
      const meta = `${movie.year || ""} ${firstGenre ? "• " + firstGenre : ""}`;
      metaText = `<div class="movie-tile-meta">${meta}</div>`;
    }

    card.innerHTML = `
      ${posterHtml}
      <div class="movie-tile-title">${movie.title || "Untitled"}</div>
      ${metaText}
      ${ratingText}
    `;

    card.addEventListener("click", () => {
      showRatingModal(movie.movie_id, movie.title);
    });

    grid.appendChild(card);
  });

  container.innerHTML = "";
  container.appendChild(grid);
}

async function loadStatistics() {
  statisticsContent.innerHTML = '<p class="loading">Loading statistics...</p>';

  try {
    const response = await fetch("/api/user/stats", {
      credentials: "same-origin",
    });

    if (!response.ok) throw new Error("Failed to load statistics");

    const stats = await response.json();

    const statsHTML = `
      <div class="stats-grid">
        <div class="stat-card">
          <h3>Total Ratings</h3>
          <p class="stat-big">${stats.total_ratings || 0}</p>
        </div>
        <div class="stat-card">
          <h3>Average Rating</h3>
          <p class="stat-big">${(stats.average_rating || 0).toFixed(2)} / 5</p>
        </div>
        <div class="stat-card">
          <h3>Top Genres</h3>
          <ul class="genre-list">
            ${
              stats.top_genres && stats.top_genres.length > 0
                ? stats.top_genres
                    .map(
                      (g) =>
                        `<li>${g.genre} <span class="genre-count">(${g.count})</span></li>`
                    )
                    .join("")
                : "<li>No genre data available</li>"
            }
          </ul>
        </div>
      </div>
    `;

    statisticsContent.innerHTML = statsHTML;
  } catch (err) {
    console.error("Failed to load statistics:", err);
    statisticsContent.innerHTML =
      '<p class="error-message">Failed to load statistics.</p>';
  }
}

// Tab switching
document.querySelectorAll(".profile-tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    const targetTab = tab.dataset.tab;

    // Update active tab
    document.querySelectorAll(".profile-tab").forEach((t) => {
      t.classList.remove("active");
    });
    tab.classList.add("active");

    // Update active content
    document.querySelectorAll(".profile-tab-content").forEach((content) => {
      content.classList.remove("active");
    });
    document.getElementById(`${targetTab}-content`).classList.add("active");

    // Load content for the selected tab
    switch (targetTab) {
      case "ratings":
        loadRatings();
        break;
      case "watchlist":
        loadWatchlist();
        break;
      case "favorites":
        loadFavorites();
        break;
      case "statistics":
        loadStatistics();
        break;
    }
  });
});

// Update counts
function updateCounts() {
  const username = sessionStorage.getItem("username");
  if (!username) return;

  // Ratings count (will be loaded from API)
  fetch("/api/button-click", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "same-origin",
    body: JSON.stringify({ button: "view_ratings_button" }),
  })
    .then((res) => res.json())
    .then((data) => {
      const count = (data.ratings || []).length;
      statRatings.textContent = count;
    })
    .catch(() => {
      statRatings.textContent = "0";
    });

  // Watchlist count
  const watchlistKey = `watchlist:${username}`;
  const watchlistData = localStorage.getItem(watchlistKey);
  const watchlist = watchlistData ? JSON.parse(watchlistData) : [];
  statWatchlist.textContent = watchlist.length;

  // Favorites count
  const favoritesKey = `favorites:${username}`;
  const favoritesData = localStorage.getItem(favoritesKey);
  const favorites = favoritesData ? JSON.parse(favoritesData) : [];
  statFavorites.textContent = favorites.length;
}

// Initialize
async function init() {
  // Check if user is logged in
  try {
    const response = await fetch("/session", { credentials: "same-origin" });
    if (response.ok) {
      const data = await response.json();
      const username = data?.username;

      if (username) {
        currentUsername = username;
        sessionStorage.setItem("username", username);

        // Update profile UI
        profileUsername.textContent = username;
        profileAvatar.textContent = username[0].toUpperCase();

        // Update counts
        updateCounts();

        // Load initial tab (ratings)
        loadRatings();
      } else {
        // Not logged in, redirect to login
        window.location.href = "/auth/login";
      }
    } else {
      window.location.href = "/auth/login";
    }
  } catch (err) {
    console.error("Failed to check session:", err);
    window.location.href = "/auth/login";
  }
}

init();
