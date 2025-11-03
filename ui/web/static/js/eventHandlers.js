/**
 * eventHandlers.js
 * Event delegation for buttons and navigation.
 * Search functionality moved to search.js
 */

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
    "search_button", // Now handled in search.js
  ];
  if (delegatedIgnore.includes(id)) return;

  // handle Home button - navigate to index
  if (id === "nav_home") {
    ev.preventDefault();
    window.location.href = "/";
    return;
  }

  // map nav/profile buttons to actions
  if (id === "view_ratings_button") {
    ev.preventDefault();
    handleActionButton("view_ratings_button");
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
