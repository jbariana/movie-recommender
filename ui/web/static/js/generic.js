const outputDiv = document.getElementById("output");
const addBox = document.getElementById("add-rating-box");

document.querySelectorAll("button").forEach((button) => {
  if (
    [
      "add_rating_button",
      "add_rating_submit",
      "add_rating_cancel",
      "remove_rating_button",
      "login_button",
      "check_session_button",
    ].includes(button.id)
  )
    return;

  button.addEventListener("click", async () => {
    if (addBox.classList.contains("visible")) addBox.classList.remove("visible");
    outputDiv.textContent = "Loading...";

    try {
      const res = await fetch("/api/button-click", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ button: button.id }),
        credentials: "same-origin",
      });
      const data = await res.json();

      outputDiv.innerHTML = "";
      const movies = Array.isArray(data) ? data : data?.ratings || [];
      const isRecs = data?.source === "recs";

      if (!movies.length) {
        outputDiv.textContent = "No movies to display.";
        return;
      }

      movies.forEach((m) => {
        const title = m.title ?? m.movie ?? "Untitled";
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
  });
});
