/**
 * shared.js
 * shared utilities for login, navigation, search, and home actions
 */

import { showRatingModal } from "./ratingModal.js";

let LOGGED_OUT_HTML = "";

// ------------------------------
// Login UI (legacy nav slot)
// ------------------------------
export function initLoginUI() {
  const loginForm = document.getElementById("login_form");
  if (loginForm) LOGGED_OUT_HTML = loginForm.innerHTML;
}

export function renderLoggedIn(username) {
  const loginForm = document.getElementById("login_form");
  if (!loginForm) return;

  loginForm.innerHTML = `
    <span class="nav-username">${username}</span>
    <button id="logout_button" type="button">Logout</button>
    <small id="login_status" class="login-status">Logged in</small>
  `;

  document.getElementById("logout_button")?.addEventListener("click", async () => {
    await fetch("/logout", { method: "POST", credentials: "same-origin" });
    window.location.href = "/";
  });
}

export function renderLoggedOut() {
  const loginForm = document.getElementById("login_form");
  if (!loginForm) return;

  // Keep your old markup, but if you’ve disabled /login on the backend,
  // show links to the auth pages instead of posting to /login.
  loginForm.innerHTML = `
    <a class="nav-tab" href="/auth/login">Login</a>
    <a class="nav-tab" href="/auth/signup">Sign&nbsp;up</a>
    <small id="login_status" class="login-status"></small>
  `;
}

// ------------------------------
// Session
// ------------------------------
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

// ------------------------------
// Navigation helpers
// ------------------------------
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

// ------------------------------
// Movie grid renderer
// ------------------------------
export function renderMovieTiles(movies) {
  const grid = document.createElement("div");
  grid.className = "movie-grid";

  movies.forEach((movie) => {
    const tile = document.createElement("div");
    tile.className = "movie-tile";
    tile.dataset.movieId = movie.movie_id;

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
    meta.textContent = `${movie.year || ""}${movie.genres ? ` • ${movie.genres}` : ""}`;

    const rating = document.createElement("div");
    rating.className = "movie-tile-rating";
    rating.textContent = movie.rating ? `★ ${Number(movie.rating).toFixed(1)}` : "Unrated";

    tile.append(posterEl, title, meta, rating);
    tile.addEventListener("click", () => {
      showRatingModal(movie.movie_id, movie.title, movie.rating);
    });

    grid.appendChild(tile);
  });

  return grid;
}

// ------------------------------
// Search
// ------------------------------
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

// ======================================================
// NEW: Home actions wiring (View Statistics & Session)
// ======================================================
export function renderJSON(el, data, title = "") {
  const wrap = document.createElement("div");
  wrap.className = "json-block";
  if (title) {
    const h = document.createElement("h3");
    h.textContent = title;
    wrap.appendChild(h);
  }
  const pre = document.createElement("pre");
  pre.textContent = JSON.stringify(data, null, 2);
  wrap.appendChild(pre);
  el.innerHTML = "";
  el.appendChild(wrap);
}

export async function fireButton(buttonId, extraPayload = {}) {
  const res = await fetch("/api/button-click", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "same-origin",
    body: JSON.stringify({ button: buttonId, ...extraPayload }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return await res.json();
}

export function wireHomeActions(outputEl) {
  const statsBtn = document.getElementById("view_statistics_button");
  const sessBtn  = document.getElementById("check_session_button");

  if (statsBtn) {
    statsBtn.addEventListener("click", async () => {
      try {
        // Use the exact id your backend expects in api.api.handle_button_click
        // Change this string if your handler uses a different button name.
        const data = await fireButton("view_statistics_button");
        renderJSON(outputEl, data, "Rating Statistics");
      } catch (e) {
        outputEl.innerHTML = `<div class="error-message">Failed to load stats: ${e.message}</div>`;
      }
    });
  }

  if (sessBtn) {
    sessBtn.addEventListener("click", async () => {
      try {
        const res = await fetch("/session", { credentials: "same-origin" });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        const title = data?.username ? `Logged in as: ${data.username}` : "No active session";
        renderJSON(outputEl, data, title);
      } catch (e) {
        outputEl.innerHTML = `<div class="error-message">Failed to check session: ${e.message}</div>`;
      }
    });
  }
}

