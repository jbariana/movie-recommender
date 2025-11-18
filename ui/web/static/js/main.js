import "./login.js";
import "./ratings.js";
import "./utils.js";
import "./ratingModal.js";
import "./movieRenderer.js";
import "./actionHandler.js";
import "./eventHandlers.js";
import { initSearch } from "./search.js";
import { wireHomeActions } from "./shared.js";
import { preloadRecommendations } from "./recsCache.js";
import { isLoggedIn } from "./utils.js";

// Initialize search on home page
const searchInput = document.getElementById("search_input");
const searchButton = document.getElementById("search_button");
const outputDiv = document.getElementById("output");

if (searchInput && searchButton && outputDiv) {
  initSearch(searchInput, searchButton, outputDiv);
  wireHomeActions(outputDiv);
}

// Preload recommendations in the background if user is logged in
(async () => {
  const loggedIn = await isLoggedIn();
  if (loggedIn) {
    console.log("User logged in - preloading recommendations");
    preloadRecommendations().catch((err) => {
      console.warn("Background preload failed:", err);
    });
  }
})();
