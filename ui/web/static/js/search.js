/**
 * search.js
 * Unified search functionality for autocomplete and full results
 * Used on both home and browse pages
 */

import { showRatingModal } from "./ratingModal.js";
import { renderMovieTiles } from "./shared.js";

let searchAutocompleteTimeout = null;
let searchDropdown = null;

/**
 * Create search dropdown for autocomplete
 */
function createSearchDropdown(searchInput) {
  if (searchDropdown) return searchDropdown;

  searchDropdown = document.createElement("div");
  searchDropdown.className = "autocomplete-dropdown";
  searchDropdown.id = "search-autocomplete-dropdown";
  searchDropdown.style.position = "absolute";
  searchDropdown.style.width = searchInput.offsetWidth + "px";

  const searchContainer = searchInput.parentElement;
  searchContainer.style.position = "relative";
  searchContainer.appendChild(searchDropdown);

  return searchDropdown;
}

/**
 * Initialize search autocomplete
 */
export function initSearchAutocomplete(searchInput) {
  if (!searchInput) return;

  const dropdown = createSearchDropdown(searchInput);

  searchInput.addEventListener("input", async (e) => {
    const query = e.target.value.trim();

    clearTimeout(searchAutocompleteTimeout);

    if (query.length < 2) {
      dropdown.classList.remove("visible");
      dropdown.innerHTML = "";
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
          dropdown.innerHTML =
            "<div class='autocomplete-item'>No results found</div>";
          dropdown.classList.add("visible");
          return;
        }

        dropdown.innerHTML = "";
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
            dropdown.classList.remove("visible");
            searchInput.value = movie.title;
            showRatingModal(movie.movie_id, movie.title, movie.rating);
          });

          dropdown.appendChild(item);
        });

        dropdown.classList.add("visible");
      } catch (err) {
        console.error("Search autocomplete error:", err);
      }
    }, 300);
  });
}

/**
 * Execute full search and display results in grid format
 */
export async function executeSearch(query, outputDiv) {
  if (!query || !outputDiv) return;

  // Close autocomplete dropdown if open
  if (searchDropdown) {
    searchDropdown.classList.remove("visible");
  }

  outputDiv.innerHTML = '<div class="loading">Searching...</div>';

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
      outputDiv.innerHTML = '<div class="info-message">No results found.</div>';
    } else {
      const grid = renderMovieTiles(movies);
      outputDiv.innerHTML = "";
      outputDiv.appendChild(grid);
    }
  } catch (err) {
    console.error("Search error:", err);
    outputDiv.innerHTML = '<div class="error-message">Search failed.</div>';
  }
}

/**
 * Setup search button and Enter key handlers
 */
export function initSearchHandlers(searchInput, searchButton, outputDiv) {
  if (!searchInput || !searchButton || !outputDiv) return;

  const handleSearch = () => {
    const query = searchInput.value.trim();
    if (!query) {
      outputDiv.textContent = "Enter a search term.";
      return;
    }
    executeSearch(query, outputDiv);
  };

  // Search button click
  searchButton.addEventListener("click", (e) => {
    e.preventDefault();
    handleSearch();
  });

  // Enter key in search input
  searchInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleSearch();
    }
  });
}

/**
 * Close dropdown when clicking outside
 */
export function initSearchClickOutside(searchInput) {
  document.addEventListener("click", (e) => {
    if (
      searchDropdown &&
      searchInput &&
      !searchInput.parentElement.contains(e.target)
    ) {
      searchDropdown.classList.remove("visible");
    }
  });
}

/**
 * Initialize all search functionality
 */
export function initSearch(searchInput, searchButton, outputDiv) {
  initSearchAutocomplete(searchInput);
  initSearchHandlers(searchInput, searchButton, outputDiv);
  initSearchClickOutside(searchInput);
}
