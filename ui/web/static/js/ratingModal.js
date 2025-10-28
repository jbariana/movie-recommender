/**
 * ratingModal.js
 * Star rating modal for adding/updating movie ratings.
 * Creates and manages the popup modal with 5-star rating interface.
 */

// Create and manage the rating modal
const outputDiv = document.getElementById("output");

const ratingModal = document.createElement("div");
ratingModal.id = "rating-modal";
ratingModal.className = "rating-modal hidden";
ratingModal.innerHTML = `
  <div class="rating-modal-content">
    <h3 id="rating-modal-title">Rate Movie</h3>
    <div class="star-rating">
      <span class="star" data-value="1">★</span>
      <span class="star" data-value="2">★</span>
      <span class="star" data-value="3">★</span>
      <span class="star" data-value="4">★</span>
      <span class="star" data-value="5">★</span>
    </div>
    <div class="rating-modal-buttons">
      <button id="rating-modal-submit">Submit</button>
      <button id="rating-modal-cancel">Cancel</button>
    </div>
  </div>
`;
document.body.appendChild(ratingModal);

let currentMovieId = null;
let currentMovieTitle = null;

export function showRatingModal(movieId, movieTitle) {
  currentMovieId = movieId;
  currentMovieTitle = movieTitle;
  document.getElementById(
    "rating-modal-title"
  ).textContent = `Rate: ${movieTitle}`;
  ratingModal.classList.remove("hidden");

  // Reset stars
  document
    .querySelectorAll(".star")
    .forEach((s) => s.classList.remove("selected", "hover"));
}

function hideRatingModal() {
  ratingModal.classList.add("hidden");
  currentMovieId = null;
  currentMovieTitle = null;
}

// Star hover effect
ratingModal.addEventListener("mouseover", (e) => {
  if (e.target.classList.contains("star")) {
    const value = parseInt(e.target.dataset.value);
    document.querySelectorAll(".star").forEach((s, idx) => {
      s.classList.toggle("hover", idx < value);
    });
  }
});

ratingModal.addEventListener("mouseout", (e) => {
  if (e.target.classList.contains("star")) {
    document
      .querySelectorAll(".star")
      .forEach((s) => s.classList.remove("hover"));
  }
});

// Star click to select rating
ratingModal.addEventListener("click", (e) => {
  if (e.target.classList.contains("star")) {
    const value = parseInt(e.target.dataset.value);
    document.querySelectorAll(".star").forEach((s, idx) => {
      s.classList.toggle("selected", idx < value);
    });
  }
});

// Submit rating
document
  .getElementById("rating-modal-submit")
  .addEventListener("click", async () => {
    const selectedStars = document.querySelectorAll(".star.selected");
    if (selectedStars.length === 0) {
      alert("Please select a rating");
      return;
    }

    const rating = selectedStars.length;

    try {
      const res = await fetch("/api/button-click", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          button: "add_rating_submit",
          movie_id: currentMovieId,
          rating: rating,
        }),
        credentials: "same-origin",
      });

      const text = await res.text();
      let data;
      try {
        data = JSON.parse(text);
      } catch {
        data = { text };
      }

      if (!res.ok) {
        outputDiv.textContent =
          data?.error || data?.message || `Server error (${res.status})`;
        hideRatingModal();
        return;
      }

      if (data?.ok) {
        outputDiv.textContent = data.message || "Rating added successfully.";
        hideRatingModal();
        // Refresh the current view
        const lastButton = sessionStorage.getItem("lastButton");
        if (lastButton) {
          const { handleActionButton } = await import("./actionHandler.js");
          handleActionButton(lastButton);
        }
      } else {
        outputDiv.textContent =
          data?.error || data?.message || "Failed to add rating.";
        hideRatingModal();
      }
    } catch (err) {
      outputDiv.textContent = "Error contacting backend.";
      console.error("Network error adding rating:", err);
      hideRatingModal();
    }
  });

// Cancel rating
document.getElementById("rating-modal-cancel").addEventListener("click", () => {
  hideRatingModal();
});

// Close modal on outside click
ratingModal.addEventListener("click", (e) => {
  if (e.target === ratingModal) {
    hideRatingModal();
  }
});
