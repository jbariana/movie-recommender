import { handleActionButton } from "./actionHandler.js";

const outputDiv = document.getElementById("output");

// Delegate clicks for buttons
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