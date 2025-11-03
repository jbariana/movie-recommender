/**
 * eventHandlers.js
 * event delegation for buttons and navigation
 * search functionality moved to search.js
 */

import { handleActionButton } from "./actionHandler.js";

const outputDiv = document.getElementById("output");

//delegate clicks for all buttons using event bubbling
document.addEventListener("click", (ev) => {
  //find closest button element (handles clicks on nested elements)
  const btn = ev.target.closest("button");
  if (!btn) return;

  const id = btn.id;

  //ignore UI-only controls handled in other modules
  const delegatedIgnore = [
    "add_rating_submit",
    "add_rating_cancel",
    "add_rating_button",
    "login_button",
    "logout_button",
    "search_button", // handled in search.js
  ];
  if (delegatedIgnore.includes(id)) return;

  //handle home button navigation
  if (id === "nav_home") {
    ev.preventDefault();
    window.location.href = "/";
    return;
  }

  //handle view ratings button
  if (id === "view_ratings_button") {
    ev.preventDefault();
    handleActionButton("view_ratings_button");
    return;
  }

  //handle view statistics button
  if (id === "view_statistics_button") {
    ev.preventDefault();
    handleActionButton("view_statistics_button");
    return;
  }

  //fallback: forward any button with known action prefix
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
