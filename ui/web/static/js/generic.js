// get references to key DOM elements used for displaying content
const outputDiv = document.getElementById("output");
const addBox = document.getElementById("add-rating-box");

// helper: check session on server
async function isLoggedIn() {
  try {
    const res = await fetch("/session", { credentials: "same-origin" });
    if (!res.ok) return false;
    const data = await res.json();
    return Boolean(data && data.username);
  } catch (e) {
    return false;
  }
}

// centralized handler for button actions (delegated)
async function handleActionButton(buttonId, payload = {}) {
  // Store last button for refresh after rating
  sessionStorage.setItem("lastButton", buttonId);

  if (addBox && addBox.classList.contains("visible"))
    addBox.classList.remove("visible");

  // require login for actions
  const loggedIn = await isLoggedIn();
  if (!loggedIn) {
    outputDiv.textContent = "Please log in to use this action.";
    return;
  }

  outputDiv.textContent = "Loading...";

  try {
    const body = Object.assign({ button: buttonId }, payload);
    const res = await fetch("/api/button-click", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      credentials: "same-origin",
    });

    if (!res.ok) {
      let err = { message: "Request failed" };
      try {
        err = await res.json();
      } catch (e) {}
      outputDiv.textContent = err.message || "Request failed.";
      return;
    }

    const data = await res.json();
    outputDiv.innerHTML = "";

    const movies = Array.isArray(data) ? data : data?.ratings || [];
    const isRecs = data?.source === "recs";

    if (!movies.length) {
      // If server returned a message (e.g. ok/message on add/remove), show it
      if (data?.message) {
        outputDiv.textContent = data.message;
        return;
      }
      outputDiv.textContent = "No movies to display.";
      return;
    }

    movies.forEach((m) => {
      const title =
        m.title ?? m.movie ?? (m.movie_id ? `ID ${m.movie_id}` : "Untitled");
      const year = m.year ? ` (${m.year})` : "";
      const genres = m.genres ? m.genres : "";
      const rating = m.rating ?? null;
      const posterUrl = m.poster_url || null;

      const movieEl = document.createElement("div");
      movieEl.classList.add("movie");
      movieEl.style.cursor = "pointer";

      movieEl.addEventListener("click", () => {
        showRatingModal(m.movie_id, title);
      });

      // Add poster image
      if (posterUrl) {
        const posterImg = document.createElement("img");
        posterImg.src = posterUrl;
        posterImg.alt = title;
        posterImg.classList.add("movie-poster");
        posterImg.loading = "lazy";
        movieEl.appendChild(posterImg);
      }

      // Movie info container
      const infoEl = document.createElement("div");
      infoEl.classList.add("movie-info");

      const titleEl = document.createElement("div");
      titleEl.classList.add("movie-title");
      titleEl.textContent = `${title}${year}`;

      const metaEl = document.createElement("div");
      metaEl.classList.add("movie-meta");
      if (genres) {
        metaEl.textContent = genres;
      }

      infoEl.appendChild(titleEl);
      if (genres) {
        infoEl.appendChild(metaEl);
      }

      // Rating display (if applicable)
      if (rating !== null && !Number.isNaN(Number(rating))) {
        const ratingEl = document.createElement("div");
        ratingEl.classList.add("movie-rating");

        if (isRecs) {
          ratingEl.textContent = `Predicted: ${Number(rating).toFixed(1)}`;
        } else {
          // This is either from profile or search with user rating
          ratingEl.textContent = `★ ${Number(rating).toFixed(1)}`;
          ratingEl.style.color = "var(--accent)"; // Blue for user ratings
        }

        infoEl.appendChild(ratingEl);
      }

      movieEl.appendChild(infoEl);
      outputDiv.appendChild(movieEl);
    });
  } catch (err) {
    outputDiv.textContent = "Error contacting backend.";
    console.error(err);
  }
}

// Create rating modal elements
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

// Show rating modal
function showRatingModal(movieId, movieTitle) {
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

// Hide rating modal
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

// Delegate clicks for buttons so DOM replacements (login form) don't break listeners
document.addEventListener("click", (ev) => {
  const btn = ev.target.closest("button");
  if (!btn) return;

  const id = btn.id;

  // ignore UI-only controls handled elsewhere
  const delegatedIgnore = [
    "add_rating_submit",
    "add_rating_cancel",
    "add_rating_button",
    "login_button",
    "logout_button",
  ];
  if (delegatedIgnore.includes(id)) return;

  // handle search button
  if (id === "search_button") {
    ev.preventDefault();
    const qEl = document.getElementById("search_input");
    const query = qEl ? qEl.value.trim() : "";
    if (!query) {
      outputDiv.textContent = "Enter a search term.";
      return;
    }
    handleActionButton("search", { query });
    return;
  }

  // map nav/profile/browse buttons to actions
  if (id === "view_ratings_button" || id === "nav_home") {
    ev.preventDefault();
    handleActionButton("view_ratings_button");
    return;
  }
  if (id === "get_rec_button") {
    ev.preventDefault();
    handleActionButton("get_rec_button");
    return;
  }
  if (id === "view_statistics_button") {
    ev.preventDefault();
    handleActionButton("view_statistics_button");
    return;
  }

  // fallback: if button id begins with a known action, forward it
  if (
    id &&
    (id.startsWith("view_") ||
      id.startsWith("get_") ||
      id.startsWith("remove_"))
  ) {
    ev.preventDefault();
    handleActionButton(id);
    return;
  }
});

// support Enter key in the search input to trigger search
document.addEventListener("keydown", (ev) => {
  const active = document.activeElement;
  if (ev.key === "Enter" && active && active.id === "search_input") {
    ev.preventDefault();
    const query = active.value.trim();
    if (!query) {
      outputDiv.textContent = "Enter a search term.";
      return;
    }
    handleActionButton("search", { query });
  }
});
