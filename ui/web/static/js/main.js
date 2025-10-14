const outputDiv = document.getElementById("output");

// --- Add Rating ---
const addBtn = document.getElementById("add_rating_button");
const addBox = document.getElementById("add-rating-box");
const addInputId = document.createElement("input");
const addInputRating = document.createElement("input");
const addSubmit = document.createElement("button");
const addCancel = document.createElement("button");

addInputId.type = "text";
addInputId.placeholder = "Movie ID";
addInputId.id = "add_rating_input_id";

addInputRating.type = "number";
addInputRating.placeholder = "Rating (1–5)";
addInputRating.id = "add_rating_input_rating";

addSubmit.textContent = "Submit";
addSubmit.id = "add_rating_submit";

addCancel.textContent = "Cancel";
addCancel.id = "add_rating_cancel";

addBox.innerHTML = ""; // clear out any existing HTML
addBox.append(addInputId, addInputRating, addSubmit, addCancel);

function hideAddBox() {
  addBox.classList.remove("visible");
  addBox.setAttribute("aria-hidden", "true");
  addInputId.value = "";
  addInputRating.value = "";
}

function showAddBox() {
  addBox.classList.add("visible");
  addBox.setAttribute("aria-hidden", "false");
  addInputId.focus();
}

addBtn.addEventListener("click", (e) => {
  e.stopPropagation();
  addBox.classList.contains("visible") ? hideAddBox() : showAddBox();
});

addCancel.addEventListener("click", (e) => {
  e.preventDefault();
  hideAddBox();
});

addSubmit.addEventListener("click", async (e) => {
  e.preventDefault();
  const movieId = addInputId.value.trim();
  const rating = addInputRating.value.trim();

  if (!movieId || !rating) {
    outputDiv.textContent = "Please enter both Movie ID and Rating.";
    return;
  }

  outputDiv.textContent = "Adding rating...";
  try {
    const res = await fetch("/api/button-click", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        button: "add_rating_submit",
        movie_id: movieId,
        rating: rating,
      }),
    });

    const data = await res.json();
    if (data?.ok) {
      outputDiv.textContent = data.message || "Rating added successfully.";
      hideAddBox();
    } else {
      outputDiv.textContent = data?.error || "Failed to add rating.";
    }
  } catch (err) {
    outputDiv.textContent = "Error contacting backend.";
    console.error(err);
  }
});

// --- Remove Rating ---
const removeBtn = document.getElementById("remove_rating_button");
removeBtn.addEventListener("click", async () => {
  const movieId = prompt("Enter Movie ID to remove rating:");
  if (!movieId) return;
  outputDiv.textContent = "Removing rating...";
  try {
    const res = await fetch("/api/button-click", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        button: "remove_rating_button",
        movie_id: movieId,
      }),
    });
    const data = await res.json();
    outputDiv.textContent = data?.message || data?.error || "Done.";
  } catch (err) {
    outputDiv.textContent = "Error contacting backend.";
    console.error(err);
  }
});

// --- Generic Handlers ---
document.querySelectorAll("button").forEach((button) => {
  if (
    [
      "add_rating_button",
      "add_rating_submit",
      "add_rating_cancel",
      "remove_rating_button",
    ].includes(button.id)
  )
    return;

  button.addEventListener("click", async () => {
    if (addBox.classList.contains("visible")) hideAddBox();
    outputDiv.textContent = "Loading...";

    try {
      const res = await fetch("/api/button-click", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ button: button.id }),
      });
      const data = await res.json();

      outputDiv.innerHTML = "";
      const movies = Array.isArray(data) ? data : data?.ratings || [];
      const isRecs = data?.source === "recs";

      if (!movies.length) {
        outputDiv.textContent = "No movies to display.";
        return;
      }

      movies.forEach((m) => {
        const title = m.title ?? m.movie ?? "Untitled";
        const rating = m.rating ?? null;

        const movieEl = document.createElement("div");
        movieEl.classList.add("movie");

        const titleEl = document.createElement("span");
        titleEl.classList.add("movie-title");
        titleEl.textContent = title;

        const ratingEl = document.createElement("span");
        ratingEl.classList.add("movie-rating");

        if (rating !== null && !Number.isNaN(Number(rating))) {
          ratingEl.textContent = isRecs
            ? ` (projected: ${Number(rating).toFixed(2)})`
            : ` (${Number(rating).toFixed(0)})`;
        }

        movieEl.append(titleEl, ratingEl);
        outputDiv.appendChild(movieEl);
      });
    } catch (err) {
      outputDiv.textContent = "Error contacting backend.";
      console.error(err);
    }
  });
});
