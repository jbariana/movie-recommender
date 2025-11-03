/**
 * search.js
 * unified search with autocomplete and full results display
 */

import { showRatingModal } from "./ratingModal.js";
import { renderMovieTiles } from "./shared.js";

let searchAutocompleteTimeout = null;
let searchDropdown = null;

//create or return existing search dropdown
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

//setup autocomplete dropdown on search input
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

    //debounce 300ms
    searchAutocompleteTimeout = setTimeout(async () => {
      try {
        const res = await fetch("/api/button-click", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ button: "search", query }),
          credentials: "same-origin",
        });

        if (!res.ok) return;

        const data = await res.json();
        const movies = data?.ratings || [];

        if (!movies.length) {
          dropdown.innerHTML =
            "<div class='autocomplete-item'>No results found</div>";
          dropdown.classList.add("visible");
          return;
        }

        //render autocomplete suggestions
        dropdown.innerHTML = movies
          .slice(0, 10)
          .map(
            (m) => `
          <div class="autocomplete-item" data-movie-id="${m.movie_id}">
            <div class="autocomplete-item-title">${m.title}</div>
            <div class="autocomplete-item-meta">${m.year || ""}${
              m.genres ? ` • ${m.genres}` : ""
            }</div>
          </div>
        `
          )
          .join("");

        //handle clicks on suggestions
        dropdown.querySelectorAll(".autocomplete-item").forEach((item) => {
          item.addEventListener("click", () => {
            const movieId = item.dataset.movieId;
            const title = item.querySelector(
              ".autocomplete-item-title"
            ).textContent;
            dropdown.classList.remove("visible");
            searchInput.value = title;
            showRatingModal(movieId, title);
          });
        });

        dropdown.classList.add("visible");
      } catch (err) {
        console.error("Search autocomplete error:", err);
      }
    }, 300);
  });
}

//execute full search and display results in grid
export async function executeSearch(query, outputDiv) {
  if (!query || !outputDiv) return;

  //close autocomplete dropdown
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

    if (!movies.length) {
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

//setup search button and enter key handlers
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

//close dropdown when clicking outside
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

//initialize all search functionality
export function initSearch(searchInput, searchButton, outputDiv) {
  initSearchAutocomplete(searchInput);
  initSearchHandlers(searchInput, searchButton, outputDiv);
  initSearchClickOutside(searchInput);
}
