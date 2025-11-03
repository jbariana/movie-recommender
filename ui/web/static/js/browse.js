/**
 * browse.js
 * dedicated script for the browse page
 * auto-loads recommendations in a tile grid layout with client-side pagination
 */

import { isLoggedIn } from "./utils.js";
import { showRatingModal } from "./ratingModal.js";
import {
  initLoginUI,
  renderLoggedIn,
  renderLoggedOut,
  checkSession,
  setupNavigation,
  renderMovieTiles,
} from "./shared.js";
import { initSearch } from "./search.js";

const outputDiv = document.getElementById("output");
let currentPage = 0;
let allRecommendations = [];
const PAGE_SIZE = 30;

//load all recommendations from API once
async function loadAllRecommendations() {
  try {
    //request recommendations from backend
    const response = await fetch("/api/button-click", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ button: "get_rec_button" }),
      credentials: "same-origin",
    });

    //handle HTTP errors
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();

    //handle API errors
    if (data.error) {
      return [];
    }

    return data.ratings || [];
  } catch (error) {
    console.error("Failed to load recommendations:", error);
    return [];
  }
}

//load initial page of recommendations
async function loadRecommendations() {
  try {
    //show loading indicator
    outputDiv.innerHTML =
      '<div class="loading">Loading recommendations...</div>';

    //fetch all recommendations from backend
    const newRecs = await loadAllRecommendations();

    //handle empty results
    if (newRecs.length === 0) {
      outputDiv.innerHTML =
        '<div class="info-message">No recommendations available. Try rating some movies first!</div>';
      return;
    }

    //store recommendations and render first page
    allRecommendations = newRecs;
    currentPage = 0;
    renderPage();
  } catch (error) {
    console.error("Failed to load recommendations:", error);
    outputDiv.innerHTML = `<div class="error-message">Failed to load recommendations: ${error.message}</div>`;
  }
}

//render current page of recommendations
function renderPage() {
  //calculate page boundaries
  const startIdx = currentPage * PAGE_SIZE;
  const endIdx = startIdx + PAGE_SIZE;
  const pageMovies = allRecommendations.slice(startIdx, endIdx);

  //handle out of bounds page number
  if (pageMovies.length === 0 && currentPage > 0) {
    currentPage = Math.max(
      0,
      Math.floor((allRecommendations.length - 1) / PAGE_SIZE)
    );
    renderPage();
    return;
  }

  //handle empty recommendations
  if (allRecommendations.length === 0) {
    outputDiv.innerHTML =
      '<div class="info-message">No recommendations available.</div>';
    return;
  }

  //create container for page
  const container = document.createElement("div");
  container.className = "browse-container";

  //render movie tiles for current page
  const grid = renderMovieTiles(pageMovies);
  container.appendChild(grid);

  //add pagination controls if multiple pages exist
  const totalPages = Math.ceil(allRecommendations.length / PAGE_SIZE);
  if (totalPages > 1) {
    const controls = document.createElement("div");
    controls.className = "pagination-controls";

    //create previous button
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

    //create next button
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

  //render page to DOM
  outputDiv.innerHTML = "";
  outputDiv.appendChild(container);
}

//initialize browse page
async function init() {
  //set up login UI
  initLoginUI();

  //check if user is logged in
  const username = await checkSession();
  if (username) {
    //show logged in state and load recommendations
    renderLoggedIn(username);
    await loadRecommendations();
  } else {
    //show logged out state
    renderLoggedOut();
    outputDiv.innerHTML =
      '<p>Please <a href="/">login</a> to see recommendations.</p>';
  }

  //set up navigation handlers
  setupNavigation();

  //initialize search functionality
  const searchInput = document.getElementById("search_input");
  const searchButton = document.getElementById("search_button");
  if (searchInput && searchButton) {
    initSearch(searchInput, searchButton, outputDiv);
  }

  //reload recommendations after login
  window.addEventListener("userLoggedIn", loadRecommendations);
}

init();
