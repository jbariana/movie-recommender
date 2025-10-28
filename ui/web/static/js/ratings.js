/**
 * ratings.js
 * Legacy "Add Rating" box with autocomplete search.
 * Provides an alternative way to add ratings via a dropdown form.
 * Also handles the "Remove Rating" button functionality.
 */

const outputDiv = document.getElementById("output");

//dynamically builds the input UI for adding a new movie rating
const addBtn = document.getElementById("add_rating_button");
const addBox = document.getElementById("add-rating-box");

//create and configure input fields + buttons programmatically
const autocompleteContainer = document.createElement("div");
autocompleteContainer.className = "autocomplete-container";

const addInputTitle = document.createElement("input");
const autocompleteDropdown = document.createElement("div");
const addInputRating = document.createElement("input");
const addSubmit = document.createElement("button");
const addCancel = document.createElement("button");

addInputTitle.type = "text";
addInputTitle.placeholder = "Search movie title...";
addInputTitle.id = "add_rating_input_title";

autocompleteDropdown.className = "autocomplete-dropdown";
autocompleteDropdown.id = "autocomplete-dropdown";

addInputRating.type = "number";
addInputRating.placeholder = "Rating (1–5)";
addInputRating.min = "1";
addInputRating.max = "5";
addInputRating.step = "0.5";
addInputRating.id = "add_rating_input_rating";

addSubmit.textContent = "Submit";
addSubmit.id = "add_rating_submit";
addSubmit.disabled = true;

addCancel.textContent = "Cancel";
addCancel.id = "add_rating_cancel";

autocompleteContainer.appendChild(addInputTitle);
autocompleteContainer.appendChild(autocompleteDropdown);

//inject the form elements into the add rating box container
if (addBox) {
  addBox.innerHTML = "";
  addBox.append(autocompleteContainer, addInputRating, addSubmit, addCancel);
}

let selectedMovieId = null;
let autocompleteTimeout = null;

//utility functions to toggle the visibility of the add rating box
function hideAddBox() {
  if (!addBox) return;
  addBox.classList.remove("visible");
  addBox.setAttribute("aria-hidden", "true");
  addInputTitle.value = "";
  addInputRating.value = "";
  autocompleteDropdown.classList.remove("visible");
  autocompleteDropdown.innerHTML = "";
  selectedMovieId = null;
  addSubmit.disabled = true;
}

function showAddBox() {
  if (!addBox) return;
  addBox.classList.add("visible");
  addBox.setAttribute("aria-hidden", "false");
  addInputTitle.focus();
}

// Autocomplete functionality
addInputTitle.addEventListener("input", async (e) => {
  const query = e.target.value.trim();

  clearTimeout(autocompleteTimeout);

  if (query.length < 2) {
    autocompleteDropdown.classList.remove("visible");
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
        body: JSON.stringify({
          button: "search",
          query: query,
        }),
        credentials: "same-origin",
      });

      if (!res.ok) return;

      const data = await res.json();
      const movies = Array.isArray(data) ? data : data?.ratings || [];

      if (movies.length === 0) {
        autocompleteDropdown.innerHTML =
          "<div class='autocomplete-item'>No results found</div>";
        autocompleteDropdown.classList.add("visible");
        return;
      }

      autocompleteDropdown.innerHTML = "";
      movies.slice(0, 10).forEach((movie) => {
        const item = document.createElement("div");
        item.className = "autocomplete-item";
        item.dataset.movieId = movie.movie_id;

        const title = document.createElement("div");
        title.className = "autocomplete-item-title";
        title.textContent = movie.title;

        const meta = document.createElement("div");
        meta.className = "autocomplete-item-meta";
        const yearStr = movie.year ? `${movie.year}` : "";
        const genresStr = movie.genres ? ` • ${movie.genres}` : "";
        meta.textContent = `${yearStr}${genresStr}`;

        item.appendChild(title);
        item.appendChild(meta);

        item.addEventListener("click", () => {
          selectedMovieId = movie.movie_id;
          addInputTitle.value = movie.title;
          autocompleteDropdown.classList.remove("visible");
          addInputRating.focus();
          addSubmit.disabled = false;
        });

        autocompleteDropdown.appendChild(item);
      });

      autocompleteDropdown.classList.add("visible");
    } catch (err) {
      console.error("Autocomplete error:", err);
    }
  }, 300);
});

// Close dropdown when clicking outside
document.addEventListener("click", (e) => {
  if (!autocompleteContainer.contains(e.target)) {
    autocompleteDropdown.classList.remove("visible");
  }
});

//clicking the main "Add Rating" button toggles the add box visibility
if (addBtn) {
  addBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    addBox &&
      (addBox.classList.contains("visible") ? hideAddBox() : showAddBox());
  });
}

//"Cancel" button closes the box and clears inputs
if (addCancel) {
  addCancel.addEventListener("click", (e) => {
    e.preventDefault();
    hideAddBox();
  });
}

//handle "Submit" click — sends rating data to backend
if (addSubmit) {
  addSubmit.addEventListener("click", async (e) => {
    e.preventDefault();

    if (!selectedMovieId || !addInputRating.value.trim()) {
      const msg = document.createElement("div");
      msg.className = "success-message";
      msg.style.background = "#e74c3c";
      msg.textContent = "Please select a movie and enter a rating.";
      outputDiv.insertBefore(msg, outputDiv.firstChild);
      setTimeout(() => msg.remove(), 3000);
      return;
    }

    const rating = addInputRating.value.trim();

    addSubmit.disabled = true;
    addSubmit.textContent = "Adding...";

    try {
      const res = await fetch("/api/button-click", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          button: "add_rating_submit",
          movie_id: selectedMovieId,
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
        console.error("Add rating failed", res.status, text);
        const msg = document.createElement("div");
        msg.className = "success-message";
        msg.style.background = "#e74c3c";
        msg.textContent =
          data?.error || data?.message || `Server error (${res.status})`;
        outputDiv.insertBefore(msg, outputDiv.firstChild);
        setTimeout(() => msg.remove(), 3000);
        return;
      }

      if (data?.ok) {
        const msg = document.createElement("div");
        msg.className = "success-message";
        msg.textContent = data.message || "Rating added successfully.";
        outputDiv.insertBefore(msg, outputDiv.firstChild);
        setTimeout(() => msg.remove(), 3000);
        hideAddBox();

        // Refresh current view
        const lastButton = sessionStorage.getItem("lastButton");
        if (lastButton) {
          const module = await import("./actionHandler.js");
          module.handleActionButton(lastButton);
        }
      } else {
        console.warn("Backend returned non-ok payload for add:", data);
        const msg = document.createElement("div");
        msg.className = "success-message";
        msg.style.background = "#e74c3c";
        msg.textContent =
          data?.error || data?.message || "Failed to add rating.";
        outputDiv.insertBefore(msg, outputDiv.firstChild);
        setTimeout(() => msg.remove(), 3000);
      }
    } catch (err) {
      const msg = document.createElement("div");
      msg.className = "success-message";
      msg.style.background = "#e74c3c";
      msg.textContent = "Error contacting backend.";
      outputDiv.insertBefore(msg, outputDiv.firstChild);
      setTimeout(() => msg.remove(), 3000);
      console.error("Network error adding rating:", err);
    } finally {
      addSubmit.disabled = false;
      addSubmit.textContent = "Submit";
    }
  });
}

//simple prompt-based workflow to remove an existing rating
const removeBtn = document.getElementById("remove_rating_button");
if (removeBtn) {
  removeBtn.addEventListener("click", async () => {
    const movieId = prompt("Enter Movie ID to remove rating:");
    if (!movieId) return;

    const msg = document.createElement("div");
    msg.className = "success-message";
    msg.textContent = "Removing rating...";
    outputDiv.insertBefore(msg, outputDiv.firstChild);

    try {
      const res = await fetch("/api/button-click", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          button: "remove_rating",
          movie_id: movieId,
        }),
        credentials: "same-origin",
      });

      const data = await res.json();
      msg.textContent = data?.message || data?.error || "Done.";
      setTimeout(() => msg.remove(), 3000);

      // Refresh current view
      const lastButton = sessionStorage.getItem("lastButton");
      if (lastButton) {
        const module = await import("./actionHandler.js");
        module.handleActionButton(lastButton);
      }
    } catch (err) {
      msg.textContent = "Error contacting backend.";
      msg.style.background = "#e74c3c";
      setTimeout(() => msg.remove(), 3000);
      console.error(err);
    }
  });
}
