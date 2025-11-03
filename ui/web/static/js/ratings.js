/**
 * ratings.js
 * legacy "Add Rating" box with autocomplete search
 * also handles "Remove Rating" button
 */

const outputDiv = document.getElementById("output");
const addBtn = document.getElementById("add_rating_button");
const addBox = document.getElementById("add-rating-box");

let selectedMovieId = null;
let autocompleteTimeout = null;

//helper to show status messages
function showMessage(text, isError = false) {
  const msg = document.createElement("div");
  msg.className = "success-message";
  if (isError) msg.style.background = "#e74c3c";
  msg.textContent = text;
  outputDiv.insertBefore(msg, outputDiv.firstChild);
  setTimeout(() => msg.remove(), 3000);
}

//helper to refresh current view
async function refreshView() {
  const lastButton = sessionStorage.getItem("lastButton");
  if (lastButton) {
    const module = await import("./actionHandler.js");
    module.handleActionButton(lastButton);
  }
}

//build add rating form if container exists
if (addBox) {
  addBox.innerHTML = `
    <div class="autocomplete-container">
      <input type="text" placeholder="Search movie title..." id="add_rating_input_title">
      <div class="autocomplete-dropdown" id="autocomplete-dropdown"></div>
    </div>
    <input type="number" placeholder="Rating (1–5)" min="1" max="5" step="0.5" id="add_rating_input_rating">
    <button id="add_rating_submit" disabled>Submit</button>
    <button id="add_rating_cancel">Cancel</button>
  `;
}

const addInputTitle = document.getElementById("add_rating_input_title");
const addInputRating = document.getElementById("add_rating_input_rating");
const addSubmit = document.getElementById("add_rating_submit");
const addCancel = document.getElementById("add_rating_cancel");
const autocompleteDropdown = document.getElementById("autocomplete-dropdown");

//toggle add box
addBtn?.addEventListener("click", (e) => {
  e.stopPropagation();
  addBox?.classList.toggle("visible");
  if (addBox?.classList.contains("visible")) {
    addInputTitle?.focus();
  }
});

//close add box
addCancel?.addEventListener("click", () => {
  addBox?.classList.remove("visible");
  addInputTitle.value = "";
  addInputRating.value = "";
  autocompleteDropdown.innerHTML = "";
  selectedMovieId = null;
  addSubmit.disabled = true;
});

//autocomplete search
addInputTitle?.addEventListener("input", async (e) => {
  const query = e.target.value.trim();
  clearTimeout(autocompleteTimeout);

  if (query.length < 2) {
    autocompleteDropdown.innerHTML = "";
    selectedMovieId = null;
    addSubmit.disabled = true;
    return;
  }

  autocompleteTimeout = setTimeout(async () => {
    try {
      const res = await fetch("/api/button-click", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ button: "search", query }),
        credentials: "same-origin",
      });

      const data = await res.json();
      const movies = data?.ratings || [];

      if (!movies.length) {
        autocompleteDropdown.innerHTML =
          "<div class='autocomplete-item'>No results</div>";
        return;
      }

      autocompleteDropdown.innerHTML = movies
        .slice(0, 10)
        .map(
          (m) => `
        <div class="autocomplete-item" data-movie-id="${m.movie_id}">
          <div class="autocomplete-item-title">${m.title}</div>
          <div class="autocomplete-item-meta">${m.year || ""}${
            m.genres ? ` • ${m.genres}` : ""
          }</div>
        </div>
      `
        )
        .join("");

      //handle clicks on suggestions
      autocompleteDropdown
        .querySelectorAll(".autocomplete-item")
        .forEach((item) => {
          item.addEventListener("click", () => {
            selectedMovieId = item.dataset.movieId;
            addInputTitle.value = item.querySelector(
              ".autocomplete-item-title"
            ).textContent;
            autocompleteDropdown.innerHTML = "";
            addInputRating.focus();
            addSubmit.disabled = false;
          });
        });
    } catch (err) {
      console.error("Autocomplete error:", err);
    }
  }, 300);
});

//close dropdown on outside click
document.addEventListener("click", (e) => {
  if (!e.target.closest(".autocomplete-container")) {
    autocompleteDropdown.innerHTML = "";
  }
});

//submit rating
addSubmit?.addEventListener("click", async () => {
  if (!selectedMovieId || !addInputRating.value.trim()) {
    showMessage("Please select a movie and enter a rating.", true);
    return;
  }

  addSubmit.disabled = true;
  addSubmit.textContent = "Adding...";

  try {
    const res = await fetch("/api/button-click", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        button: "add_rating_submit",
        movie_id: selectedMovieId,
        rating: addInputRating.value.trim(),
      }),
      credentials: "same-origin",
    });

    const data = await res.json();

    if (data?.ok) {
      showMessage(data.message || "Rating added.");
      addBox?.classList.remove("visible");
      await refreshView();
    } else {
      showMessage(data?.error || "Failed to add rating.", true);
    }
  } catch (err) {
    showMessage("Error contacting backend.", true);
  } finally {
    addSubmit.disabled = false;
    addSubmit.textContent = "Submit";
  }
});

//remove rating
document
  .getElementById("remove_rating_button")
  ?.addEventListener("click", async () => {
    const movieId = prompt("Enter Movie ID to remove:");
    if (!movieId) return;

    showMessage("Removing...");

    try {
      const res = await fetch("/api/button-click", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ button: "remove_rating", movie_id: movieId }),
        credentials: "same-origin",
      });

      const data = await res.json();
      showMessage(data?.message || "Done.");
      await refreshView();
    } catch (err) {
      showMessage("Error contacting backend.", true);
    }
  });
