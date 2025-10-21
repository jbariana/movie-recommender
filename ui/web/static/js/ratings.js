const outputDiv = document.getElementById("output");

//dynamically builds the input UI for adding a new movie rating
const addBtn = document.getElementById("add_rating_button");
const addBox = document.getElementById("add-rating-box");

//create and configure input fields + buttons programmatically
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

//inject the form elements into the add rating box container
if (addBox) {
  addBox.innerHTML = "";
  addBox.append(addInputId, addInputRating, addSubmit, addCancel);
}

//utility functions to toggle the visibility of the add rating box
function hideAddBox() {
  if (!addBox) return;
  addBox.classList.remove("visible");
  addBox.setAttribute("aria-hidden", "true");
  addInputId.value = "";
  addInputRating.value = "";
}

function showAddBox() {
  if (!addBox) return;
  addBox.classList.add("visible");
  addBox.setAttribute("aria-hidden", "false");
  addInputId.focus();
}

//clicking the main “Add Rating” button toggles the add box visibility
if (addBtn) {
  addBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    addBox &&
      (addBox.classList.contains("visible") ? hideAddBox() : showAddBox());
  });
}

//“Cancel” button closes the box and clears inputs
if (addCancel) {
  addCancel.addEventListener("click", (e) => {
    e.preventDefault();
    hideAddBox();
  });
}

//handle “Submit” click — sends rating data to backend
if (addSubmit) {
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
        credentials: "same-origin",
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
}

//simple prompt-based workflow to remove an existing rating
const removeBtn = document.getElementById("remove_rating_button");
if (removeBtn) {
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
        credentials: "same-origin",
      });

      const data = await res.json();
      outputDiv.textContent = data?.message || data?.error || "Done.";
    } catch (err) {
      outputDiv.textContent = "Error contacting backend.";
      console.error(err);
    }
  });
}
