/**
 * ratingModal.js
 * Star rating modal + favorite + watchlist checkboxes.
 *
 * Works from BOTH Browse and Profile:
 *  - Saves rating through /api/button-click (add_rating_submit)
 *  - Updates favorites/watchlist in localStorage per user
 *  - Dispatches a "ratingUpdated" event so profile.js can refresh
 */

// main output area used on Browse page (safe if it doesn't exist)
const outputDiv = document.getElementById("output");

// ---------- Create modal DOM once ----------
const ratingModal = document.createElement("div");
ratingModal.id = "rating-modal";
ratingModal.className = "rating-modal hidden";
ratingModal.innerHTML = `
  <div class="rating-modal-content">
    <h3 id="rating-modal-title">Rate Movie</h3>

    <div class="rating-modal-flags">
      <label>
        <input type="checkbox" id="rating-favorite" />
        ♥ Favorited
      </label>
      <label style="margin-left: 0.75rem;">
        <input type="checkbox" id="rating-watchlist" />
        In Watchlist
      </label>
    </div>

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

// cache elements
const favoriteCheckbox = document.getElementById("rating-favorite");
const watchlistCheckbox = document.getElementById("rating-watchlist");
const submitBtn = document.getElementById("rating-modal-submit");
const cancelBtn = document.getElementById("rating-modal-cancel");

// ---------- State ----------
let currentMovieId = null;
let currentMovieTitle = null;

// ---------- Helpers: per-user storage ----------
function getCurrentUsername() {
  const el = document.querySelector(".login-status b");
  return el ? el.textContent.trim() : null;
}

function favKey() {
  const u = getCurrentUsername();
  return u ? `favorites:${u}` : "favorites";
}
function wlKey() {
  const u = getCurrentUsername();
  return u ? `watchlist:${u}` : "watchlist";
}

function loadList(key, fallback = []) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

function saveList(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // ignore quota errors etc.
  }
}

function movieInList(list, movieId) {
  return list.some((m) => String(m.movie_id) === String(movieId));
}

function upsertMovie(list, movieId, title, rating) {
  const idx = list.findIndex((m) => String(m.movie_id) === String(movieId));
  const base = { movie_id: movieId, title: title || "Untitled" };
  if (rating != null) base.rating = rating;

  if (idx >= 0) {
    list[idx] = { ...list[idx], ...base };
  } else {
    list.push(base);
  }
}

function removeMovie(list, movieId) {
  return list.filter((m) => String(m.movie_id) !== String(movieId));
}

// ---------- Star UI helpers ----------
function clearStarState() {
  ratingModal
    .querySelectorAll(".star")
    .forEach((s) => s.classList.remove("selected", "hover"));
}

function applyHover(value) {
  ratingModal.querySelectorAll(".star").forEach((s) => {
    const v = parseInt(s.dataset.value, 10);
    s.classList.toggle("hover", v <= value);
  });
}

function selectStars(value) {
  ratingModal.querySelectorAll(".star").forEach((s) => {
    const v = parseInt(s.dataset.value, 10);
    s.classList.toggle("selected", v <= value);
  });
}

function getSelectedRating() {
  const selected = ratingModal.querySelectorAll(".star.selected");
  return selected.length;
}

// ---------- Public API ----------
export function showRatingModal(movieId, movieTitle) {
  currentMovieId = movieId;
  currentMovieTitle = movieTitle;

  // title
  document.getElementById(
    "rating-modal-title"
  ).textContent = `Rate: ${movieTitle}`;

  // reset stars
  clearStarState();

  // pre-check favorite / watchlist based on storage
  const favs = loadList(favKey(), []);
  const wls = loadList(wlKey(), []);
  favoriteCheckbox.checked = movieInList(favs, movieId);
  watchlistCheckbox.checked = movieInList(wls, movieId);

  // show modal
  ratingModal.classList.remove("hidden");
}

// ---------- Hide modal ----------
function hideRatingModal() {
  ratingModal.classList.add("hidden");
  currentMovieId = null;
  currentMovieTitle = null;
}

// ---------- Star interactions ----------
ratingModal.addEventListener("mouseover", (e) => {
  if (e.target.classList.contains("star")) {
    const value = parseInt(e.target.dataset.value, 10);
    applyHover(value);
  }
});

ratingModal.addEventListener("mouseout", (e) => {
  if (e.target.classList.contains("star")) {
    ratingModal
      .querySelectorAll(".star")
      .forEach((s) => s.classList.remove("hover"));
  }
});

ratingModal.addEventListener("click", (e) => {
  if (e.target.classList.contains("star")) {
    const value = parseInt(e.target.dataset.value, 10);
    selectStars(value);
  }
});

// ---------- Submit ----------
submitBtn.addEventListener("click", async () => {
  if (!currentMovieId) {
    hideRatingModal();
    return;
  }

  const rating = getSelectedRating();
  if (rating === 0) {
    alert("Please select a rating");
    return;
  }

  const favChecked = favoriteCheckbox.checked;
  const wlChecked = watchlistCheckbox.checked;

  try {
    const res = await fetch("/api/button-click", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "same-origin",
      body: JSON.stringify({
        button: "add_rating_submit",
        movie_id: currentMovieId,
        rating: rating,
      }),
    });

    const text = await res.text();
    let data;
    try {
      data = JSON.parse(text);
    } catch {
      data = { text };
    }

    if (!res.ok || data?.error || data?.ok === false) {
      if (outputDiv) {
        outputDiv.textContent =
          data?.error || data?.message || `Server error (${res.status})`;
      }
      hideRatingModal();
      return;
    }

    // --- update favorites / watchlist in localStorage ---
    let favs = loadList(favKey(), []);
    let wls = loadList(wlKey(), []);

    if (favChecked) {
      upsertMovie(favs, currentMovieId, currentMovieTitle, rating);
    } else {
      favs = removeMovie(favs, currentMovieId);
    }

    if (wlChecked) {
      upsertMovie(wls, currentMovieId, currentMovieTitle, rating);
    } else {
      wls = removeMovie(wls, currentMovieId);
    }

    saveList(favKey(), favs);
    saveList(wlKey(), wls);

    // notify profile.js so it can refresh without reload
    window.dispatchEvent(
      new CustomEvent("ratingUpdated", {
        detail: {
          movie_id: currentMovieId,
          rating,
          isFavorite: favChecked,
          inWatchlist: wlChecked,
        },
      })
    );

    if (outputDiv) {
      outputDiv.textContent = data.message || "Rating saved.";
    }

    hideRatingModal();
  } catch (err) {
    console.error("Network error adding rating:", err);
    if (outputDiv) {
      outputDiv.textContent = "Error contacting backend.";
    }
    hideRatingModal();
  }
});

// ---------- Cancel + click outside ----------
cancelBtn.addEventListener("click", () => {
  hideRatingModal();
});

ratingModal.addEventListener("click", (e) => {
  if (e.target === ratingModal) {
    hideRatingModal();
  }
});
