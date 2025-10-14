const outputDiv = document.getElementById("output");

document.querySelectorAll("button").forEach((button) => {
  button.addEventListener("click", async () => {
    outputDiv.textContent = "Loading...";

    try {
      const res = await fetch("/api/button-click", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ button: button.id }),
      });

      const data = await res.json();

      // Clear output
      outputDiv.innerHTML = "";

      // api.py returns { ratings: [...], source: "profile" | "recs" }
      const movies = Array.isArray(data) ? data : (data && data.ratings) || [];
      const isRecs = data && data.source === "recs";

      if (!movies.length) {
        outputDiv.textContent = "No movies to display";
        return;
      }

      movies.forEach((m) => {
        const title = m.title ?? "Untitled";
        const rating = m.rating ?? null;

        const movieEl = document.createElement("div");
        movieEl.classList.add("movie");

        const titleEl = document.createElement("span");
        titleEl.classList.add("movie-title");
        titleEl.textContent = title;

        const ratingEl = document.createElement("span");
        ratingEl.classList.add("movie-rating");

        if (
          rating !== null &&
          rating !== undefined &&
          !Number.isNaN(Number(rating))
        ) {
          if (isRecs) {
            ratingEl.textContent = ` (projected: ${Number(rating).toFixed(2)})`;
          } else {
            // profile ratings show as integers (no many decimals, no label)
            ratingEl.textContent = ` (${Number(rating).toFixed(0)})`;
          }
        } else {
          ratingEl.textContent = "";
        }

        movieEl.appendChild(titleEl);
        movieEl.appendChild(ratingEl);
        outputDiv.appendChild(movieEl);
      });
    } catch (err) {
      outputDiv.textContent = "Error contacting backend";
      console.error(err);
    }
  });
});
