/**
 * shared.js
 * Shared utilities for login, navigation, and search across pages.
 * Reduces code duplication between index and browse pages.
 */

import { showRatingModal } from "./ratingModal.js";

// Logged out HTML template
let LOGGED_OUT_HTML = "";

export function initLoginUI() {
  const loginForm = document.getElementById("login_form");
  if (loginForm) {
    LOGGED_OUT_HTML = loginForm.innerHTML;
  }
}

export function renderLoggedIn(username) {
  const loginForm = document.getElementById("login_form");
  if (!loginForm) return;

  loginForm.innerHTML = `
    <span class="nav-username">${username}</span>
    <button id="logout_button" type="button">Logout</button>
    <small id="login_status" class="login-status">Logged in</small>
  `;

  document
    .getElementById("logout_button")
    .addEventListener("click", async () => {
      await fetch("/logout", { method: "POST", credentials: "same-origin" });
      window.location.href = "/";
    });
}

export function renderLoggedOut() {
  const loginForm = document.getElementById("login_form");
  if (!loginForm) return;

  loginForm.innerHTML = LOGGED_OUT_HTML;

  const btn = document.getElementById("login_button");
  const input = document.getElementById("username");

  if (btn && input) {
    btn.onclick = async () => {
      const username = input.value.trim();
      if (!username) return;

      const res = await fetch("/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username }),
        credentials: "same-origin",
      });

      if (res.ok) {
        renderLoggedIn(username);
        // Trigger custom event for pages to handle post-login
        window.dispatchEvent(new CustomEvent("userLoggedIn"));
      }
    };
  }
}

export async function checkSession() {
  try {
    const res = await fetch("/session", { credentials: "same-origin" });
    if (res.ok) {
      const data = await res.json();
      return data?.username || null;
    }
  } catch (e) {
    console.error("Session check failed:", e);
  }
  return null;
}

export function setupNavigation() {
  document.addEventListener("click", (ev) => {
    const btn = ev.target.closest("button, a");
    if (!btn) return;

    if (btn.id === "nav_home") {
      ev.preventDefault();
      window.location.href = "/";
    }

    if (btn.id === "view_ratings_button") {
      ev.preventDefault();
      window.location.href = "/?view=profile";
    }
  });
}

/**
 * Render movie tiles grid (shared grid format for all pages)
 */
export function renderMovieTiles(movies) {
  const grid = document.createElement("div");
  grid.className = "movie-grid";

  movies.forEach((movie) => {
    const tile = document.createElement("div");
    tile.className = "movie-tile";
    tile.dataset.movieId = movie.movie_id;

    // Poster: image if available, else placeholder
    let posterEl;
    if (movie.poster_url) {
      posterEl = document.createElement("img");
      posterEl.className = "movie-poster-img";
      posterEl.src = movie.poster_url;
      posterEl.alt = movie.title || `ID ${movie.movie_id}`;
      posterEl.loading = "lazy";
      posterEl.onerror = function () {
        this.style.display = "none";
        const placeholder = document.createElement("div");
        placeholder.className = "movie-poster-tile";
        placeholder.textContent = "No Poster";
        this.parentNode.insertBefore(placeholder, this);
      };
    } else {
      posterEl = document.createElement("div");
      posterEl.className = "movie-poster-tile";
      posterEl.textContent = "No Poster";
    }

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
      ? `★ ${Number(movie.rating).toFixed(1)}`
      : "Unrated";

    tile.appendChild(posterEl);
    tile.appendChild(title);
    tile.appendChild(meta);
    tile.appendChild(rating);

    tile.addEventListener("click", () => {
      showRatingModal(movie.movie_id, movie.title, movie.rating);
    });

    grid.appendChild(tile);
  });

  return grid;
}

export function setupSearch(onSearch) {
  const searchInput = document.getElementById("search_input");
  const searchButton = document.getElementById("search_button");

  if (!searchButton || !searchInput) return;

  const handleSearch = () => {
    const query = searchInput.value.trim();
    if (query && onSearch) {
      onSearch(query);
    }
  };

  searchButton.addEventListener("click", (e) => {
    e.preventDefault();
    handleSearch();
  });

  searchInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleSearch();
    }
  });
}
