import { checkSession } from "./shared.js";
import { showRatingModal } from "./ratingModal.js";

const searchInput = document.getElementById("search_input");
const searchButton = document.getElementById("search_button");
const resultsDiv = document.getElementById("search-results");
const queryDisplay = document.getElementById("search-query-display");
const countDisplay = document.getElementById("search-count");

// ✅ Helper to get first genre
function getFirstGenre(genresString) {
  if (!genresString) return "";
  const genres = genresString
    .split("|")
    .map((g) => g.trim())
    .filter((g) => g);
  return genres.length > 0 ? genres[0] : "";
}

async function performSearch() {
  const query = searchInput.value.trim();

  if (!query || query.length < 2) {
    resultsDiv.innerHTML =
      '<p class="info-message">Please enter at least 2 characters to search.</p>';
    queryDisplay.textContent = "";
    countDisplay.textContent = "";
    return;
  }

  const newUrl = `/search?q=${encodeURIComponent(query)}`;
  window.history.pushState({ query }, "", newUrl);

  resultsDiv.innerHTML = '<p class="loading">Searching...</p>';
  queryDisplay.textContent = `"${query}"`;
  countDisplay.textContent = "";

  try {
    const res = await fetch(
      `/api/movies/search?q=${encodeURIComponent(query)}&limit=100`
    );
    if (!res.ok) throw new Error("Search failed");

    const data = await res.json();
    const movies = data.results || [];

    if (movies.length === 0) {
      resultsDiv.innerHTML = `
        <div class="info-message" style="grid-column: 1 / -1;">
          <p>No results found for "${query}"</p>
          <p style="margin-top:0.5rem;color:var(--muted);font-size:0.9rem;">Try a different search term.</p>
        </div>
      `;
      countDisplay.textContent = "No movies found";
      return;
    }

    countDisplay.textContent = `${movies.length} ${
      movies.length === 1 ? "movie" : "movies"
    } found`;

    renderResults(movies);
  } catch (err) {
    console.error("Search failed:", err);
    resultsDiv.innerHTML =
      '<p class="error-message">Search failed. Please try again.</p>';
    countDisplay.textContent = "";
  }
}

function renderResults(movies) {
  resultsDiv.innerHTML = "";

  movies.forEach((m) => {
    const card = document.createElement("div");
    card.className = "movie-tile";
    card.style.cursor = "pointer";

    // ✅ Get only first genre
    const firstGenre = getFirstGenre(m.genres);
    const metaText = `${m.year || ""} ${firstGenre ? "• " + firstGenre : ""}`;

    card.innerHTML = `
      ${
        m.poster_url
          ? `<img src="${m.poster_url}" alt="${m.title}" class="movie-poster-img" loading="lazy">`
          : '<div class="movie-poster-tile">🎬</div>'
      }
      <div class="movie-tile-title">${m.title || "Untitled"}</div>
      <div class="movie-tile-meta">${metaText}</div>
    `;

    card.addEventListener("click", () => {
      try {
        showRatingModal(m.movie_id, m.title);
      } catch (err) {
        console.error("Failed to open rating modal:", err);
      }
    });

    resultsDiv.appendChild(card);
  });
}

searchButton.addEventListener("click", performSearch);

searchInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    e.preventDefault();
    performSearch();
  }
});

// Load search from URL query parameter
async function init() {
  await checkSession();

  const urlParams = new URLSearchParams(window.location.search);
  const query = urlParams.get("q");

  if (query) {
    searchInput.value = query;
    performSearch();
  } else {
    resultsDiv.innerHTML =
      '<p class="info-message">Enter a movie title to search.</p>';
    queryDisplay.textContent = "";
    countDisplay.textContent = "";
  }
}

init();
