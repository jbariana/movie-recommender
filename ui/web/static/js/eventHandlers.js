/**
 * eventHandlers.js
 * Event delegation and search autocomplete functionality.
 * Handles all user interactions: button clicks, keyboard input, and search.
 */

import { handleActionButton } from "./actionHandler.js";
import { showRatingModal } from "./ratingModal.js";

const outputDiv = document.getElementById("output");
const searchInput = document.getElementById("search_input");

// State for search autocomplete
let searchAutocompleteTimeout = null;
let searchDropdown = null;

// Create search dropdown
function createSearchDropdown() {
  if (searchDropdown) return;

  searchDropdown = document.createElement("div");
  searchDropdown.className = "autocomplete-dropdown";
  searchDropdown.id = "search-autocomplete-dropdown";
  searchDropdown.style.position = "absolute";
  searchDropdown.style.width = searchInput.offsetWidth + "px";

  const searchContainer = searchInput.parentElement;
  searchContainer.style.position = "relative";
  searchContainer.appendChild(searchDropdown);
}

// Search autocomplete functionality
if (searchInput) {
  createSearchDropdown();

  searchInput.addEventListener("input", async (e) => {
    const query = e.target.value.trim();

    clearTimeout(searchAutocompleteTimeout);

    if (query.length < 2) {
      searchDropdown.classList.remove("visible");
      searchDropdown.innerHTML = "";
      return;
    }

    searchAutocompleteTimeout = setTimeout(async () => {
      try {
        const res = await fetch("/api/button-click", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            button: "search",
            query: query,
          }),
          credentials: "same-origin",
        });

        if (!res.ok) return;

        const data = await res.json();
        const movies = Array.isArray(data) ? data : data?.ratings || [];

        if (movies.length === 0) {
          searchDropdown.innerHTML =
            "<div class='autocomplete-item'>No results found</div>";
          searchDropdown.classList.add("visible");
          return;
        }

        searchDropdown.innerHTML = "";
        movies.slice(0, 10).forEach((movie) => {
          const item = document.createElement("div");
          item.className = "autocomplete-item";
          item.dataset.movieId = movie.movie_id;

          const title = document.createElement("div");
          title.className = "autocomplete-item-title";
          title.textContent = movie.title;

          const meta = document.createElement("div");
          meta.className = "autocomplete-item-meta";
          const yearStr = movie.year ? `${movie.year}` : "";
          const genresStr = movie.genres ? ` • ${movie.genres}` : "";
          meta.textContent = `${yearStr}${genresStr}`;

          item.appendChild(title);
          item.appendChild(meta);

          item.addEventListener("click", () => {
            searchDropdown.classList.remove("visible");
            searchInput.value = movie.title;
            showRatingModal(movie.movie_id, movie.title, movie.rating);
          });

          searchDropdown.appendChild(item);
        });

        searchDropdown.classList.add("visible");
      } catch (err) {
        console.error("Search autocomplete error:", err);
      }
    }, 300);
  });
}

// Close search dropdown when clicking outside
document.addEventListener("click", (e) => {
  if (
    searchDropdown &&
    searchInput &&
    !searchInput.parentElement.contains(e.target)
  ) {
    searchDropdown.classList.remove("visible");
  }
});

// Delegate clicks for buttons
document.addEventListener("click", (ev) => {
  const btn = ev.target.closest("button");
  if (!btn) return;

  const id = btn.id;

  // ignore UI-only controls handled elsewhere
  const delegatedIgnore = [
    "add_rating_submit",
    "add_rating_cancel",
    "add_rating_button",
    "login_button",
    "logout_button",
  ];
  if (delegatedIgnore.includes(id)) return;

  // handle search button - now shows full results
  if (id === "search_button") {
    ev.preventDefault();
    const qEl = document.getElementById("search_input");
    const query = qEl ? qEl.value.trim() : "";
    if (!query) {
      outputDiv.textContent = "Enter a search term.";
      return;
    }
    // Close dropdown and show full results
    if (searchDropdown) {
      searchDropdown.classList.remove("visible");
    }
    handleActionButton("search", { query });
    return;
  }

  // map nav/profile/browse buttons to actions
  if (id === "view_ratings_button" || id === "nav_home") {
    ev.preventDefault();
    handleActionButton("view_ratings_button");
    return;
  }
  if (id === "get_rec_button") {
    ev.preventDefault();
    handleActionButton("get_rec_button");
    return;
  }
  if (id === "view_statistics_button") {
    ev.preventDefault();
    handleActionButton("view_statistics_button");
    return;
  }

  // fallback: if button id begins with a known action, forward it
  if (
    id &&
    (id.startsWith("view_") ||
      id.startsWith("get_") ||
      id.startsWith("remove_"))
  ) {
    ev.preventDefault();
    handleActionButton(id);
    return;
  }
});

// support Enter key in the search input to trigger full search
document.addEventListener("keydown", (ev) => {
  const active = document.activeElement;
  if (ev.key === "Enter" && active && active.id === "search_input") {
    ev.preventDefault();
    const query = active.value.trim();
    if (!query) {
      outputDiv.textContent = "Enter a search term.";
      return;
    }
    // Close dropdown and show full results
    if (searchDropdown) {
      searchDropdown.classList.remove("visible");
    }
    handleActionButton("search", { query });
  }
});
