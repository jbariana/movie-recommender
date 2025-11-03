/**
 * movieRenderer.js
 * renders movie lists with posters, titles, genres, and ratings
 * handles both user ratings and recommendation displays
 */

import { showRatingModal } from "./ratingModal.js";

//render list of movies in vertical format (legacy view)
export function renderMovies(movies, isRecs, outputDiv) {
  //clear existing content
  outputDiv.innerHTML = "";

  //handle empty movie list
  if (!movies.length) {
    outputDiv.textContent = "No movies to display.";
    return;
  }

  //render each movie as a clickable card
  movies.forEach((m) => {
    //extract movie properties with fallbacks
    const title =
      m.title ?? m.movie ?? (m.movie_id ? `ID ${m.movie_id}` : "Untitled");
    const year = m.year ? ` (${m.year})` : "";
    const genres = m.genres ? m.genres : "";
    const rating = m.rating ?? null;
    const posterUrl = m.poster_url || null;

    //create movie container element
    const movieEl = document.createElement("div");
    movieEl.classList.add("movie");
    movieEl.style.cursor = "pointer";
    movieEl.title = rating
      ? "Click to update rating"
      : "Click to rate this movie";

    //open rating modal when clicked
    movieEl.addEventListener("click", () => {
      showRatingModal(m.movie_id, title, rating);
    });

    //add poster image if available
    if (posterUrl) {
      const posterImg = document.createElement("img");
      posterImg.src = posterUrl;
      posterImg.alt = title;
      posterImg.classList.add("movie-poster");
      posterImg.loading = "lazy"; //lazy load images for performance
      movieEl.appendChild(posterImg);
    }

    //create movie info container
    const infoEl = document.createElement("div");
    infoEl.classList.add("movie-info");

    //add title with year
    const titleEl = document.createElement("div");
    titleEl.classList.add("movie-title");
    titleEl.textContent = `${title}${year}`;

    //add genres if available
    const metaEl = document.createElement("div");
    metaEl.classList.add("movie-meta");
    if (genres) {
      metaEl.textContent = genres;
    }

    infoEl.appendChild(titleEl);
    if (genres) {
      infoEl.appendChild(metaEl);
    }

    //add rating display if available
    if (rating !== null && !Number.isNaN(Number(rating))) {
      const ratingEl = document.createElement("div");
      ratingEl.classList.add("movie-rating");

      //different display for recommendations vs user ratings
      if (isRecs) {
        ratingEl.textContent = `Predicted: ${Number(rating).toFixed(1)}`;
      } else {
        //user's actual rating
        ratingEl.textContent = `★ ${Number(rating).toFixed(1)}`;
        ratingEl.style.color = "var(--accent)"; //blue for user ratings
      }

      infoEl.appendChild(ratingEl);
    }

    //append info and add to output
    movieEl.appendChild(infoEl);
    outputDiv.appendChild(movieEl);
  });
}
