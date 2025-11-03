/**
 * actionHandler.js
 * centralized handler for all button actions and API requests
 * manages communication with backend and coordinates view updates
 */

import { isLoggedIn } from "./utils.js";
import { renderMovieTiles } from "./shared.js";

const outputDiv = document.getElementById("output");
const addBox = document.getElementById("add-rating-box");

//handle button click actions and dispatch to backend
export async function handleActionButton(buttonId, payload = {}) {
  //store last button for refresh after rating
  sessionStorage.setItem("lastButton", buttonId);

  //hide add rating box if visible
  if (addBox && addBox.classList.contains("visible"))
    addBox.classList.remove("visible");

  //require login for all actions
  const loggedIn = await isLoggedIn();
  if (!loggedIn) {
    outputDiv.textContent = "Please log in to use this action.";
    return;
  }

  outputDiv.textContent = "Loading...";

  try {
    //build request payload with button ID
    const body = Object.assign({ button: buttonId }, payload);

    //send POST request to backend API
    const res = await fetch("/api/button-click", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      credentials: "same-origin",
    });

    //handle error responses
    if (!res.ok) {
      let err = { message: "Request failed" };
      try {
        err = await res.json();
      } catch (e) {}
      outputDiv.textContent = err.message || "Request failed.";
      return;
    }

    const data = await res.json();

    //handle statistics view with custom renderer
    if (buttonId === "view_statistics_button") {
      renderStatistics(data);
      return;
    }

    //extract movies array from response
    const movies = Array.isArray(data) ? data : data?.ratings || [];

    //handle empty results
    if (!movies.length) {
      //show success message if returned (e.g. "Rating saved")
      if (data?.message) {
        outputDiv.textContent = data.message;
        return;
      }
      outputDiv.textContent = "No movies to display.";
      return;
    }

    //render movies in tile grid format
    const grid = renderMovieTiles(movies);
    outputDiv.innerHTML = "";
    outputDiv.appendChild(grid);
  } catch (err) {
    outputDiv.textContent = "Error contacting backend.";
    console.error(err);
  }
}

//render statistics in formatted view with cards
function renderStatistics(data) {
  //create container for statistics page
  const container = document.createElement("div");
  container.className = "statistics-container";

  //add page title
  const title = document.createElement("h2");
  title.textContent = "Rating Statistics";
  title.className = "statistics-title";
  container.appendChild(title);

  //extract statistics from response
  const stats = data?.statistics || data?.stats || {};
  const total = stats.total_ratings || stats.total || 0;
  const avgRating = stats.average_rating || stats.avg || 0;
  const topGenres = stats.top_genres || [];

  //create overview card with total and average
  const overviewCard = document.createElement("div");
  overviewCard.className = "stats-card";

  const overviewTitle = document.createElement("h3");
  overviewTitle.textContent = "Overview";
  overviewCard.appendChild(overviewTitle);

  //add total ratings stat
  const totalStat = document.createElement("div");
  totalStat.className = "stat-item";
  totalStat.innerHTML = `
    <span class="stat-label">Total Ratings</span>
    <span class="stat-value">${total}</span>
  `;
  overviewCard.appendChild(totalStat);

  //add average rating stat
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

  //create top genres card if data available
  if (topGenres.length > 0) {
    const genresCard = document.createElement("div");
    genresCard.className = "stats-card";

    const genresTitle = document.createElement("h3");
    genresTitle.textContent = "Top Genres";
    genresCard.appendChild(genresTitle);

    //render each genre with rank and count
    topGenres.forEach((genre, idx) => {
      const genreItem = document.createElement("div");
      genreItem.className = "stat-item genre-item";

      //genre rank (#1, #2, etc)
      const rank = document.createElement("span");
      rank.className = "genre-rank";
      rank.textContent = `#${idx + 1}`;

      //genre name
      const name = document.createElement("span");
      name.className = "genre-name";
      name.textContent = genre.genre || genre.name || genre;

      //rating count for this genre
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
    //show message if no genre data available
    const noGenres = document.createElement("div");
    noGenres.className = "stats-card";
    noGenres.innerHTML =
      '<p style="color: var(--muted); margin: 0;">No genre data available yet.</p>';
    container.appendChild(noGenres);
  }

  //render statistics page
  outputDiv.innerHTML = "";
  outputDiv.appendChild(container);
}
