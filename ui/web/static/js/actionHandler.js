/**
 * actionHandler.js
 * Centralized handler for all button actions and API requests.
 * Manages communication with backend and coordinates view updates.
 */

import { isLoggedIn } from "./utils.js";
import { renderMovieTiles } from "./shared.js";

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

    // Handle statistics view specially
    if (buttonId === "view_statistics_button") {
      renderStatistics(data);
      return;
    }

    const movies = Array.isArray(data) ? data : data?.ratings || [];

    if (!movies.length) {
      // If server returned a message (e.g. ok/message on add/remove), show it
      if (data?.message) {
        outputDiv.textContent = data.message;
        return;
      }
      outputDiv.textContent = "No movies to display.";
      return;
    }

    // Render all results in grid tile format (like browse page)
    const grid = renderMovieTiles(movies);
    outputDiv.innerHTML = "";
    outputDiv.appendChild(grid);
  } catch (err) {
    outputDiv.textContent = "Error contacting backend.";
    console.error(err);
  }
}

/**
 * Render statistics in a nice formatted view
 */
function renderStatistics(data) {
  const container = document.createElement("div");
  container.className = "statistics-container";

  const title = document.createElement("h2");
  title.textContent = "Rating Statistics";
  title.className = "statistics-title";
  container.appendChild(title);

  // Parse statistics data
  const stats = data?.statistics || data?.stats || {};
  const total = stats.total_ratings || stats.total || 0;
  const avgRating = stats.average_rating || stats.avg || 0;
  const topGenres = stats.top_genres || [];

  // Overview card
  const overviewCard = document.createElement("div");
  overviewCard.className = "stats-card";

  const overviewTitle = document.createElement("h3");
  overviewTitle.textContent = "Overview";
  overviewCard.appendChild(overviewTitle);

  const totalStat = document.createElement("div");
  totalStat.className = "stat-item";
  totalStat.innerHTML = `
    <span class="stat-label">Total Ratings</span>
    <span class="stat-value">${total}</span>
  `;
  overviewCard.appendChild(totalStat);

  const avgStat = document.createElement("div");
  avgStat.className = "stat-item";
  avgStat.innerHTML = `
    <span class="stat-label">Average Rating</span>
    <span class="stat-value">${
      avgRating ? avgRating.toFixed(1) : "0"
    } / 5.0</span>
  `;
  overviewCard.appendChild(avgStat);

  container.appendChild(overviewCard);

  // Top genres card
  if (topGenres.length > 0) {
    const genresCard = document.createElement("div");
    genresCard.className = "stats-card";

    const genresTitle = document.createElement("h3");
    genresTitle.textContent = "Top Genres";
    genresCard.appendChild(genresTitle);

    topGenres.forEach((genre, idx) => {
      const genreItem = document.createElement("div");
      genreItem.className = "stat-item genre-item";

      const rank = document.createElement("span");
      rank.className = "genre-rank";
      rank.textContent = `#${idx + 1}`;

      const name = document.createElement("span");
      name.className = "genre-name";
      name.textContent = genre.genre || genre.name || genre;

      const count = document.createElement("span");
      count.className = "genre-count";
      count.textContent = `${genre.count || 0} rated`;

      genreItem.appendChild(rank);
      genreItem.appendChild(name);
      genreItem.appendChild(count);
      genresCard.appendChild(genreItem);
    });

    container.appendChild(genresCard);
  } else {
    const noGenres = document.createElement("div");
    noGenres.className = "stats-card";
    noGenres.innerHTML =
      '<p style="color: var(--muted); margin: 0;">No genre data available yet.</p>';
    container.appendChild(noGenres);
  }

  outputDiv.innerHTML = "";
  outputDiv.appendChild(container);
}
