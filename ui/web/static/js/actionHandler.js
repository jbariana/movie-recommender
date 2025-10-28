/**
 * actionHandler.js
 * Centralized handler for all button actions and API requests.
 * Manages communication with backend and coordinates view updates.
 */

import { isLoggedIn } from "./utils.js";
import { renderMovies } from "./movieRenderer.js";

const outputDiv = document.getElementById("output");
const addBox = document.getElementById("add-rating-box");

export async function handleActionButton(buttonId, payload = {}) {
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

    renderMovies(movies, isRecs, outputDiv);
  } catch (err) {
    outputDiv.textContent = "Error contacting backend.";
    console.error(err);
  }
}
