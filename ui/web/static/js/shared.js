/**
 * shared.js
 * shared utilities for login, navigation, and search across pages
 */

import { showRatingModal } from "./ratingModal.js";

let LOGGED_OUT_HTML = "";

//store original login form HTML
export function initLoginUI() {
  const loginForm = document.getElementById("login_form");
  if (loginForm) LOGGED_OUT_HTML = loginForm.innerHTML;
}

//render logged in state with username and logout button
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

//render logged out state with login form
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
        window.dispatchEvent(new CustomEvent("userLoggedIn"));
      }
    };
  }
}

//check if user is logged in
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

//setup navigation handlers
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

//render movies in tile grid format
export function renderMovieTiles(movies) {
  const grid = document.createElement("div");
  grid.className = "movie-grid";

  movies.forEach((movie) => {
    const tile = document.createElement("div");
    tile.className = "movie-tile";
    tile.dataset.movieId = movie.movie_id;

    //add poster or placeholder
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

    //add title
    const title = document.createElement("div");
    title.className = "movie-tile-title";
    title.textContent = movie.title;

    //add metadata (year and genres)
    const meta = document.createElement("div");
    meta.className = "movie-tile-meta";
    meta.textContent = `${movie.year || ""}${
      movie.genres ? ` • ${movie.genres}` : ""
    }`;

    //add rating display
    const rating = document.createElement("div");
    rating.className = "movie-tile-rating";
    rating.textContent = movie.rating
      ? `★ ${Number(movie.rating).toFixed(1)}`
      : "Unrated";

    tile.append(posterEl, title, meta, rating);

    //open rating modal on click
    tile.addEventListener("click", () => {
      showRatingModal(movie.movie_id, movie.title, movie.rating);
    });

    grid.appendChild(tile);
  });

  return grid;
}

//setup search handlers
export function setupSearch(onSearch) {
  const searchInput = document.getElementById("search_input");
  const searchButton = document.getElementById("search_button");

  if (!searchButton || !searchInput) return;

  const handleSearch = () => {
    const query = searchInput.value.trim();
    if (query && onSearch) onSearch(query);
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
