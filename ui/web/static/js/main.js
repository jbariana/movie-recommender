import "./login.js";
import "./ratings.js";
import "./utils.js";
import "./ratingModal.js";
import "./movieRenderer.js";
import "./actionHandler.js";
import "./eventHandlers.js";
import { initSearch } from "./search.js";
import { wireHomeActions } from "./shared.js";  // <-- new

// initialize search on home page
const searchInput = document.getElementById("search_input");
const searchButton = document.getElementById("search_button");
const outputDiv   = document.getElementById("output");

if (searchInput && searchButton && outputDiv) {
  initSearch(searchInput, searchButton, outputDiv);
  // also wire the Home buttons to show results in #output
  wireHomeActions(outputDiv); // <-- new
}
