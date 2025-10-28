import { showRatingModal } from "./ratingModal.js";

export function renderMovies(movies, isRecs, outputDiv) {
  outputDiv.innerHTML = "";

  if (!movies.length) {
    outputDiv.textContent = "No movies to display.";
    return;
  }

  movies.forEach((m) => {
    const title = m.title ?? m.movie ?? (m.movie_id ? `ID ${m.movie_id}` : "Untitled");
    const year = m.year ? ` (${m.year})` : "";
    const genres = m.genres ? m.genres : "";
    const rating = m.rating ?? null;
    const posterUrl = m.poster_url || null;

    const movieEl = document.createElement("div");
    movieEl.classList.add("movie");
    movieEl.style.cursor = "pointer";

    movieEl.addEventListener("click", () => {
      showRatingModal(m.movie_id, title);
    });

    // Add poster image
    if (posterUrl) {
      const posterImg = document.createElement("img");
      posterImg.src = posterUrl;
      posterImg.alt = title;
      posterImg.classList.add("movie-poster");
      posterImg.loading = "lazy";
      movieEl.appendChild(posterImg);
    }

    // Movie info container
    const infoEl = document.createElement("div");
    infoEl.classList.add("movie-info");

    const titleEl = document.createElement("div");
    titleEl.classList.add("movie-title");
    titleEl.textContent = `${title}${year}`;

    const metaEl = document.createElement("div");
    metaEl.classList.add("movie-meta");
    if (genres) {
      metaEl.textContent = genres;
    }

    infoEl.appendChild(titleEl);
    if (genres) {
      infoEl.appendChild(metaEl);
    }

    // Rating display (if applicable)
    if (rating !== null && !Number.isNaN(Number(rating))) {
      const ratingEl = document.createElement("div");
      ratingEl.classList.add("movie-rating");

      if (isRecs) {
        ratingEl.textContent = `Predicted: ${Number(rating).toFixed(1)}`;
      } else {
        // This is either from profile or search with user rating
        ratingEl.textContent = `★ ${Number(rating).toFixed(1)}`;
        ratingEl.style.color = "var(--accent)"; // Blue for user ratings
      }

      infoEl.appendChild(ratingEl);
    }

    movieEl.appendChild(infoEl);
    outputDiv.appendChild(movieEl);
  });
}