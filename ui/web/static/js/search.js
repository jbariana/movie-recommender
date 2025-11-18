/**
 * search.js
 * Movie search with autocomplete
 */

import { showRatingModal } from "./ratingModal.js";

let searchTimeout = null;

export function initSearch(searchInput, searchButton, outputDiv) {
  if (!searchInput || !searchButton) return;

  // Autocomplete dropdown
  const dropdown = document.createElement("div");
  dropdown.className = "autocomplete-dropdown";
  searchInput.parentElement.style.position = "relative";
  searchInput.parentElement.appendChild(dropdown);

  let selectedIndex = -1;

  // Hide dropdown when clicking outside
  document.addEventListener("click", (e) => {
    if (!searchInput.contains(e.target) && !dropdown.contains(e.target)) {
      dropdown.classList.remove("visible");
    }
  });

  // Search input typing (autocomplete)
  searchInput.addEventListener("input", () => {
    const query = searchInput.value.trim();

    if (query.length < 2) {
      dropdown.classList.remove("visible");
      return;
    }

    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(async () => {
      try {
        const res = await fetch(
          `/api/movies/search?q=${encodeURIComponent(query)}&limit=8`
        );
        if (!res.ok) throw new Error("Search failed");

        const data = await res.json();
        const movies = data.results || [];

        if (movies.length === 0) {
          dropdown.innerHTML =
            '<div class="autocomplete-item" style="cursor:default;color:var(--muted);">No results</div>';
          dropdown.classList.add("visible");
          return;
        }

        dropdown.innerHTML = "";
        movies.forEach((m, idx) => {
          const item = document.createElement("div");
          item.className = "autocomplete-item";
          item.dataset.index = idx;
          item.innerHTML = `
            <div class="autocomplete-item-title">${m.title || "Untitled"}</div>
            <div class="autocomplete-item-meta">${m.year || ""} ${
            m.genres ? "• " + m.genres : ""
          }</div>
          `;

          item.addEventListener("click", () => {
            searchInput.value = "";
            dropdown.classList.remove("visible");
            showRatingModal(m.movie_id, m.title);
          });

          dropdown.appendChild(item);
        });

        dropdown.classList.add("visible");
        selectedIndex = -1;
      } catch (err) {
        console.error("Autocomplete failed:", err);
        dropdown.classList.remove("visible");
      }
    }, 300);
  });

  // Keyboard navigation in dropdown
  searchInput.addEventListener("keydown", (e) => {
    const items = dropdown.querySelectorAll(".autocomplete-item");

    if (items.length > 0) {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        selectedIndex = Math.min(selectedIndex + 1, items.length - 1);
        updateDropdownSelection(items, selectedIndex);
        return;
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        selectedIndex = Math.max(selectedIndex - 1, 0);
        updateDropdownSelection(items, selectedIndex);
        return;
      } else if (e.key === "Escape") {
        dropdown.classList.remove("visible");
        selectedIndex = -1;
        return;
      }
    }

    // Enter key - navigate to search page
    if (e.key === "Enter") {
      e.preventDefault();

      if (selectedIndex >= 0 && selectedIndex < items.length) {
        // Click the selected autocomplete item
        items[selectedIndex].click();
      } else {
        // Navigate to search results page
        const query = searchInput.value.trim();
        if (query.length >= 2) {
          window.location.href = `/search?q=${encodeURIComponent(query)}`;
        }
      }
    }
  });

  // Search button click - navigate to search page
  searchButton.addEventListener("click", () => {
    const query = searchInput.value.trim();
    dropdown.classList.remove("visible");

    if (query.length >= 2) {
      window.location.href = `/search?q=${encodeURIComponent(query)}`;
    }
  });
}

function updateDropdownSelection(items, selectedIndex) {
  items.forEach((item, idx) => {
    item.classList.toggle("selected", idx === selectedIndex);
  });
}
