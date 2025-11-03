/**
 * shared.js
 * Shared utilities for login, navigation, and search across pages.
 * Reduces code duplication between index and browse pages.
 */

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
