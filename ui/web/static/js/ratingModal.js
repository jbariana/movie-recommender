/**
 * ratingModal.js
 * Handles the movie rating modal UI
 */

import { isLoggedIn } from "./utils.js";
import { invalidateCache, preloadRecommendations } from "./recsCache.js";

let currentMovieId = null;
let currentMovieTitle = null;
let selectedRating = 0;
let existingRating = null;

const modal = document.getElementById("rating-modal");
const modalTitle = document.getElementById("rating-modal-title");
const stars = document.querySelectorAll(".star");
const submitBtn = document.getElementById("rating-modal-submit");
const removeBtn = document.getElementById("rating-modal-remove");
const cancelBtn = document.getElementById("rating-modal-cancel");
const watchlistBtn = document.getElementById("rating-modal-watchlist");
const favoriteBtn = document.getElementById("rating-modal-favorite");

// ✅ Helper to get current username from session
async function getCurrentUsername() {
  try {
    const res = await fetch("/session", { credentials: "same-origin" });
    if (!res.ok) return null;
    const data = await res.json();
    return data.username || null;
  } catch {
    return null;
  }
}

// Star hover/click handlers
stars.forEach((star, index) => {
  star.addEventListener("mouseenter", () => {
    updateStarDisplay(index + 1);
  });

  star.addEventListener("click", () => {
    selectedRating = index + 1;
    updateStarDisplay(selectedRating);
    submitBtn.disabled = false;
  });
});

// Reset stars on mouse leave
document.querySelector(".star-rating")?.addEventListener("mouseleave", () => {
  updateStarDisplay(selectedRating);
});

function updateStarDisplay(rating) {
  stars.forEach((star, index) => {
    star.classList.toggle("selected", index < rating);
    star.classList.toggle("hover", index < rating);
  });
}

// Submit rating
submitBtn?.addEventListener("click", async () => {
  const username = await getCurrentUsername();
  if (!username) {
    alert("Please log in to rate movies.");
    return;
  }

  if (selectedRating === 0) {
    alert("Please select a rating.");
    return;
  }

  submitBtn.disabled = true;
  submitBtn.textContent = "Saving...";

  try {
    const response = await fetch("/api/button-click", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "same-origin",
      body: JSON.stringify({
        button: "add_rating_submit",
        movie_id: currentMovieId,
        rating: selectedRating,
      }),
    });

    const data = await response.json();

    if (!response.ok || data.error) {
      alert(data.error || "Failed to save rating");
      submitBtn.disabled = false;
      submitBtn.textContent = "Save Rating";
      return;
    }

    // Invalidate cache and preload new recommendations
    invalidateCache();
    preloadRecommendations(); // Start loading in background

    window.dispatchEvent(
      new CustomEvent("ratingUpdated", {
        detail: {
          movie_id: currentMovieId,
          rating: selectedRating,
          title: currentMovieTitle,
        },
      })
    );

    closeModal();
  } catch (error) {
    console.error("Failed to save rating:", error);
    alert("Failed to save rating. Please try again.");
    submitBtn.disabled = false;
    submitBtn.textContent = "Save Rating";
  }
});

// Remove rating
removeBtn?.addEventListener("click", async () => {
  if (!confirm(`Remove your rating for "${currentMovieTitle}"?`)) {
    return;
  }

  removeBtn.disabled = true;
  removeBtn.textContent = "Removing...";

  try {
    // ✅ Use remove_rating (from your ratings.js)
    const response = await fetch("/api/button-click", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "same-origin",
      body: JSON.stringify({
        button: "remove_rating",
        movie_id: currentMovieId,
      }),
    });

    const data = await response.json();

    if (!response.ok || data.error) {
      throw new Error(data.error || "Failed to remove rating");
    }

    window.dispatchEvent(
      new CustomEvent("ratingUpdated", {
        detail: { movie_id: currentMovieId, rating: 0 },
      })
    );

    closeModal();
  } catch (error) {
    console.error("Failed to remove rating:", error);
    alert("Failed to remove rating. Please try again.");
    removeBtn.disabled = false;
    removeBtn.textContent = "Remove Rating";
  }
});

// Add to watchlist (no rating required)
watchlistBtn?.addEventListener("click", async () => {
  const username = await getCurrentUsername();
  if (!username) {
    alert("Please log in first.");
    return;
  }
  toggleWatchlist(currentMovieId, currentMovieTitle, username);
});

// Add to favorites (no rating required)
favoriteBtn?.addEventListener("click", async () => {
  const username = await getCurrentUsername();
  if (!username) {
    alert("Please log in first.");
    return;
  }
  toggleFavorite(currentMovieId, currentMovieTitle, username);
});

function toggleWatchlist(movieId, title, username) {
  const key = `watchlist:${username}`;
  let watchlist = [];
  try {
    const stored = localStorage.getItem(key);
    watchlist = stored ? JSON.parse(stored) : [];
  } catch {}

  const idx = watchlist.findIndex(
    (m) => String(m.movie_id) === String(movieId)
  );

  if (idx >= 0) {
    watchlist.splice(idx, 1);
    watchlistBtn.classList.remove("active");
    watchlistBtn.textContent = "🔖 Add to Watchlist";
  } else {
    watchlist.push({
      movie_id: movieId,
      title: title,
      timestamp: Date.now(),
    });
    watchlistBtn.classList.add("active");
    watchlistBtn.textContent = "🔖 In Watchlist";
  }

  localStorage.setItem(key, JSON.stringify(watchlist));

  window.dispatchEvent(
    new CustomEvent("watchlistUpdated", {
      detail: { movie_id: movieId },
    })
  );
}

function toggleFavorite(movieId, title, username) {
  const key = `favorites:${username}`;
  let favorites = [];
  try {
    const stored = localStorage.getItem(key);
    favorites = stored ? JSON.parse(stored) : [];
  } catch {}

  const idx = favorites.findIndex(
    (m) => String(m.movie_id) === String(movieId)
  );

  if (idx >= 0) {
    favorites.splice(idx, 1);
    favoriteBtn.classList.remove("active");
    favoriteBtn.textContent = "♥ Add to Favorites";
  } else {
    favorites.push({
      movie_id: movieId,
      title: title,
      timestamp: Date.now(),
    });
    favoriteBtn.classList.add("active");
    favoriteBtn.textContent = "♥ Favorited";
  }

  localStorage.setItem(key, JSON.stringify(favorites));

  window.dispatchEvent(
    new CustomEvent("favoritesUpdated", {
      detail: { movie_id: movieId },
    })
  );
}

// Cancel button
cancelBtn?.addEventListener("click", closeModal);

// Close on background click
modal?.addEventListener("click", (e) => {
  if (e.target === modal) {
    closeModal();
  }
});

// Close on Escape key
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && !modal.classList.contains("hidden")) {
    closeModal();
  }
});

function closeModal() {
  modal.classList.add("hidden");
  selectedRating = 0;
  existingRating = null;
  currentMovieId = null;
  currentMovieTitle = null;
  updateStarDisplay(0);
  submitBtn.disabled = true;
  submitBtn.textContent = "Save Rating";
  removeBtn.textContent = "Remove Rating";
  removeBtn.classList.add("hidden");
  watchlistBtn.classList.remove("active");
  favoriteBtn.classList.remove("active");
  watchlistBtn.textContent = "🔖 Add to Watchlist";
  favoriteBtn.textContent = "♥ Add to Favorites";
}

export async function showRatingModal(movieId, movieTitle) {
  const username = await getCurrentUsername();
  if (!username) {
    alert("Please log in to rate movies.");
    return;
  }

  currentMovieId = movieId;
  currentMovieTitle = movieTitle;
  selectedRating = 0;
  existingRating = null;

  modalTitle.textContent = movieTitle || `Movie ${movieId}`;

  // Check if user already rated this movie
  try {
    const response = await fetch("/api/button-click", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "same-origin",
      body: JSON.stringify({ button: "view_ratings_button" }),
    });

    const data = await response.json();
    const ratings = data.ratings || [];
    const existing = ratings.find(
      (r) => String(r.movie_id) === String(movieId)
    );

    if (existing) {
      existingRating = existing.rating;
      selectedRating = existing.rating;
      updateStarDisplay(selectedRating);
      removeBtn.classList.remove("hidden");
      submitBtn.disabled = false;
    } else {
      removeBtn.classList.add("hidden");
      submitBtn.disabled = true;
    }
  } catch (error) {
    console.error("Failed to check existing rating:", error);
  }

  // Check watchlist/favorites status
  try {
    const wlKey = `watchlist:${username}`;
    const favKey = `favorites:${username}`;
    const watchlist = JSON.parse(localStorage.getItem(wlKey) || "[]");
    const favorites = JSON.parse(localStorage.getItem(favKey) || "[]");

    const inWatchlist = watchlist.some(
      (m) => String(m.movie_id) === String(movieId)
    );
    const inFavorites = favorites.some(
      (m) => String(m.movie_id) === String(movieId)
    );

    if (inWatchlist) {
      watchlistBtn.classList.add("active");
      watchlistBtn.textContent = "🔖 In Watchlist";
    } else {
      watchlistBtn.classList.remove("active");
      watchlistBtn.textContent = "🔖 Add to Watchlist";
    }

    if (inFavorites) {
      favoriteBtn.classList.add("active");
      favoriteBtn.textContent = "♥ Favorited";
    } else {
      favoriteBtn.classList.remove("active");
      favoriteBtn.textContent = "♥ Add to Favorites";
    }
  } catch {}

  modal.classList.remove("hidden");
}
