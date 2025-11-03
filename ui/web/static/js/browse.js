/**
 * browse.js
 * Dedicated script for the browse page.
 * Auto-loads recommendations in a tile grid layout.
 */

import { isLoggedIn } from "./utils.js";
import { showRatingModal } from "./ratingModal.js";
import {
  initLoginUI,
  renderLoggedIn,
  renderLoggedOut,
  checkSession,
  setupNavigation,
  setupSearch,
} from "./shared.js";

const outputDiv = document.getElementById("output");

// Render movies in tile/grid layout
function renderMovieTiles(movies) {
  const grid = document.createElement("div");
  grid.className = "movie-grid";

  movies.forEach((movie) => {
    const tile = document.createElement("div");
    tile.className = "movie-tile";
    tile.dataset.movieId = movie.movie_id;

    const placeholder = document.createElement("div");
    placeholder.className = "movie-poster-tile";
    placeholder.textContent = "No Poster";

    const title = document.createElement("div");
    title.className = "movie-tile-title";
    title.textContent = movie.title;

    const meta = document.createElement("div");
    meta.className = "movie-tile-meta";
    const yearStr = movie.year ? `${movie.year}` : "";
    const genresStr = movie.genres ? ` • ${movie.genres}` : "";
    meta.textContent = `${yearStr}${genresStr}`;

    const rating = document.createElement("div");
    rating.className = "movie-tile-rating";
    rating.textContent = movie.rating
      ? `★ ${movie.rating.toFixed(1)}`
      : "Predicted";

    tile.appendChild(placeholder);
    tile.appendChild(title);
    tile.appendChild(meta);
    tile.appendChild(rating);

    tile.addEventListener("click", () => {
      showRatingModal(movie.movie_id, movie.title, movie.rating);
    });

    grid.appendChild(tile);
  });

  outputDiv.innerHTML = "";
  outputDiv.appendChild(grid);
}

// Load recommendations
async function loadRecommendations() {
  const loggedIn = await isLoggedIn();

  if (!loggedIn) {
    outputDiv.innerHTML =
      '<p>Please <a href="/">login</a> to see recommendations.</p>';
    return;
  }

  outputDiv.textContent = "Loading recommendations...";

  try {
    const res = await fetch("/api/button-click", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ button: "get_rec_button" }),
      credentials: "same-origin",
    });

    if (!res.ok) {
      outputDiv.textContent = "Failed to load recommendations.";
      return;
    }

    const data = await res.json();
    const movies = data?.ratings || [];

    if (movies.length === 0) {
      outputDiv.innerHTML =
        '<p>No recommendations yet. <a href="/">Rate some movies</a> to get started!</p>';
      return;
    }

    renderMovieTiles(movies);
  } catch (err) {
    console.error("Error loading recommendations:", err);
    outputDiv.textContent = "Error loading recommendations.";
  }
}

// Search handler
async function handleSearch(query) {
  outputDiv.textContent = "Searching...";

  try {
    const res = await fetch("/api/button-click", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ button: "search", query }),
      credentials: "same-origin",
    });

    const data = await res.json();
    const movies = data?.ratings || [];

    if (movies.length === 0) {
      outputDiv.textContent = "No results found.";
    } else {
      renderMovieTiles(movies);
    }
  } catch (err) {
    outputDiv.textContent = "Search failed.";
  }
}

// Initialize
async function init() {
  initLoginUI();

  const username = await checkSession();
  if (username) {
    renderLoggedIn(username);
    await loadRecommendations();
  } else {
    renderLoggedOut();
    outputDiv.innerHTML =
      '<p>Please <a href="/">login</a> to see recommendations.</p>';
  }

  setupNavigation();
  setupSearch(handleSearch);

  // Reload recommendations after login
  window.addEventListener("userLoggedIn", loadRecommendations);
}

init();
