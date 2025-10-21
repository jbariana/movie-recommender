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
        m.title ??
        m.movie ??
        (m.movie_id !== undefined && m.movie_id !== null
          ? `ID ${m.movie_id}`
          : "Untitled");
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
}

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
