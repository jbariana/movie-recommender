/**
 * browse.js
 * Dedicated script for the browse page.
 * Auto-loads recommendations in a tile grid layout with client-side pagination.
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
  renderMovieTiles,
} from "./shared.js";

const outputDiv = document.getElementById("output");
let currentPage = 0;
let allRecommendations = [];
const PAGE_SIZE = 30;

/**
 * Load ALL recommendations from API once
 */
async function loadAllRecommendations() {
  try {
    const response = await fetch("/api/button-click", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ button: "get_rec_button" }),
      credentials: "same-origin",
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();

    if (data.error) {
      return [];
    }

    return data.ratings || [];
  } catch (error) {
    console.error("Failed to load recommendations:", error);
    return [];
  }
}

/**
 * Load initial page
 */
async function loadRecommendations() {
  try {
    outputDiv.innerHTML =
      '<div class="loading">Loading recommendations...</div>';

    const newRecs = await loadAllRecommendations();

    if (newRecs.length === 0) {
      outputDiv.innerHTML =
        '<div class="info-message">No recommendations available. Try rating some movies first!</div>';
      return;
    }

    allRecommendations = newRecs;
    currentPage = 0;
    renderPage();
  } catch (error) {
    console.error("Failed to load recommendations:", error);
    outputDiv.innerHTML = `<div class="error-message">Failed to load recommendations: ${error.message}</div>`;
  }
}

/**
 * Render current page of recommendations
 */
function renderPage() {
  const startIdx = currentPage * PAGE_SIZE;
  const endIdx = startIdx + PAGE_SIZE;
  const pageMovies = allRecommendations.slice(startIdx, endIdx);

  if (pageMovies.length === 0 && currentPage > 0) {
    // Went past the end, go back
    currentPage = Math.max(
      0,
      Math.floor((allRecommendations.length - 1) / PAGE_SIZE)
    );
    renderPage();
    return;
  }

  if (allRecommendations.length === 0) {
    outputDiv.innerHTML =
      '<div class="info-message">No recommendations available.</div>';
    return;
  }

  // Create container
  const container = document.createElement("div");
  container.className = "browse-container";

  // Movie grid
  const grid = renderMovieTiles(pageMovies);
  container.appendChild(grid);

  // Pagination controls (only show if more than one page)
  const totalPages = Math.ceil(allRecommendations.length / PAGE_SIZE);
  if (totalPages > 1) {
    const controls = document.createElement("div");
    controls.className = "pagination-controls";

    const prevBtn = document.createElement("button");
    prevBtn.className = "pagination-btn";
    prevBtn.textContent = "← Previous";
    prevBtn.disabled = currentPage === 0;
    prevBtn.onclick = () => {
      if (currentPage > 0) {
        currentPage--;
        renderPage();
        window.scrollTo({ top: 0, behavior: "smooth" });
      }
    };

    const nextBtn = document.createElement("button");
    nextBtn.className = "pagination-btn";
    nextBtn.textContent = "Next →";
    nextBtn.disabled = endIdx >= allRecommendations.length;
    nextBtn.onclick = () => {
      if (endIdx < allRecommendations.length) {
        currentPage++;
        renderPage();
        window.scrollTo({ top: 0, behavior: "smooth" });
      }
    };

    controls.appendChild(prevBtn);
    controls.appendChild(nextBtn);
    container.appendChild(controls);
  }

  outputDiv.innerHTML = "";
  outputDiv.appendChild(container);
}

// Search handler - now uses shared tile renderer
async function handleSearch(query) {
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
      // Show search results in grid format using shared renderer
      const grid = renderMovieTiles(movies);
      outputDiv.innerHTML = "";
      outputDiv.appendChild(grid);
    }
  } catch (err) {
    outputDiv.innerHTML = '<div class="error-message">Search failed.</div>';
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
