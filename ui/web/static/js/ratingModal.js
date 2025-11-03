/**
 * ratingModal.js
 * star rating modal for adding/updating movie ratings
 * creates and manages the popup modal with 5-star rating interface
 */

//get reference to output div for status messages
const outputDiv = document.getElementById("output");

//create modal element with star rating interface
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

//track current movie being rated
let currentMovieId = null;
let currentMovieTitle = null;

//show rating modal for a specific movie
export function showRatingModal(movieId, movieTitle) {
  currentMovieId = movieId;
  currentMovieTitle = movieTitle;

  //update modal title with movie name
  document.getElementById(
    "rating-modal-title"
  ).textContent = `Rate: ${movieTitle}`;

  //show modal
  ratingModal.classList.remove("hidden");

  //reset star selection state
  document
    .querySelectorAll(".star")
    .forEach((s) => s.classList.remove("selected", "hover"));
}

//hide rating modal and clear state
function hideRatingModal() {
  ratingModal.classList.add("hidden");
  currentMovieId = null;
  currentMovieTitle = null;
}

//star hover effect to preview rating
ratingModal.addEventListener("mouseover", (e) => {
  if (e.target.classList.contains("star")) {
    const value = parseInt(e.target.dataset.value);
    //highlight all stars up to hovered star
    document.querySelectorAll(".star").forEach((s, idx) => {
      s.classList.toggle("hover", idx < value);
    });
  }
});

//remove hover effect when mouse leaves star
ratingModal.addEventListener("mouseout", (e) => {
  if (e.target.classList.contains("star")) {
    document
      .querySelectorAll(".star")
      .forEach((s) => s.classList.remove("hover"));
  }
});

//star click to select rating
ratingModal.addEventListener("click", (e) => {
  if (e.target.classList.contains("star")) {
    const value = parseInt(e.target.dataset.value);
    //mark all stars up to clicked star as selected
    document.querySelectorAll(".star").forEach((s, idx) => {
      s.classList.toggle("selected", idx < value);
    });
  }
});

//submit rating to backend
document
  .getElementById("rating-modal-submit")
  .addEventListener("click", async () => {
    //validate that user selected at least one star
    const selectedStars = document.querySelectorAll(".star.selected");
    if (selectedStars.length === 0) {
      alert("Please select a rating");
      return;
    }

    //count selected stars (1-5)
    const rating = selectedStars.length;

    try {
      //send rating to backend API
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

      //parse response (handle both JSON and plain text)
      const text = await res.text();
      let data;
      try {
        data = JSON.parse(text);
      } catch {
        data = { text };
      }

      //handle HTTP errors
      if (!res.ok) {
        outputDiv.textContent =
          data?.error || data?.message || `Server error (${res.status})`;
        hideRatingModal();
        return;
      }

      //handle successful rating submission
      if (data?.ok) {
        outputDiv.textContent = data.message || "Rating added successfully.";
        hideRatingModal();

        //refresh the current view to show updated rating
        const lastButton = sessionStorage.getItem("lastButton");
        if (lastButton) {
          const { handleActionButton } = await import("./actionHandler.js");
          handleActionButton(lastButton);
        }
      } else {
        //handle API errors
        outputDiv.textContent =
          data?.error || data?.message || "Failed to add rating.";
        hideRatingModal();
      }
    } catch (err) {
      //handle network errors
      outputDiv.textContent = "Error contacting backend.";
      console.error("Network error adding rating:", err);
      hideRatingModal();
    }
  });

//cancel button closes modal without saving
document.getElementById("rating-modal-cancel").addEventListener("click", () => {
  hideRatingModal();
});

//close modal when clicking outside of it
ratingModal.addEventListener("click", (e) => {
  if (e.target === ratingModal) {
    hideRatingModal();
  }
});
