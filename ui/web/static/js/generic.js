//get references to key DOM elements used for displaying content
const outputDiv = document.getElementById("output"); //movie info/results
const addBox = document.getElementById("add-rating-box"); //UI box for adding a rating

// Select all <button> elements on the page and attach a click event handler to them,
// except for a few buttons that are handled elsewhere
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
    return; // If the button is in the above list, skip adding this click listener

  // Add an asynchronous click listener to all other buttons
  button.addEventListener("click", async () => {
    //if the "Add Rating" box is visible hide it when another button is clicked.
    if (addBox.classList.contains("visible"))
      addBox.classList.remove("visible");

    //display loading message while waiting for the backend response
    outputDiv.textContent = "Loading...";

    try {
      // Send a POST request to the Flask backend endpoint /api/button-click
      // The body contains JSON with the clicked button's ID
      // 'credentials: "same-origin"' ensures session cookies are sent along
      const res = await fetch("/api/button-click", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ button: button.id }),
        credentials: "same-origin",
      });

      //parse JSON response from the server
      const data = await res.json();

      //clear out previous results before displaying new ones
      outputDiv.innerHTML = "";

      // The response could be:
      // - An array of movies directly
      // - Or an object with a 'ratings' field containing an array
      // Fallback ensures flexibility with different API return shapes
      const movies = Array.isArray(data) ? data : data?.ratings || [];

      //check if the response came from a recommendations source
      const isRecs = data?.source === "recs";

      //if there are no movies to display, show a simple message
      if (!movies.length) {
        outputDiv.textContent = "No movies to display.";
        return;
      }

      //loop through each movie and dynamically build HTML elements to display them
      movies.forEach((m) => {
        //extract title and rating safely with fallback defaults
        const title = m.title ?? m.movie ?? "Untitled";
        const rating = m.rating ?? null;

        //create a parent <div> for the movie
        const movieEl = document.createElement("div");
        movieEl.classList.add("movie"); // Apply a CSS class for styling

        //create a <span> for the movie title
        const titleEl = document.createElement("span");
        titleEl.classList.add("movie-title");
        titleEl.textContent = title;

        //create a <span> for the rating
        const ratingEl = document.createElement("span");
        ratingEl.classList.add("movie-rating");

        //if a numeric rating exists, format and display it
        //"isRecs" means these are predicted (projected) ratings instead of actual user ratings
        if (rating !== null && !Number.isNaN(Number(rating))) {
          ratingEl.textContent = isRecs
            ? ` (projected: ${Number(rating).toFixed(2)})`
            : ` (${Number(rating).toFixed(0)})`; 
        }

        //append the title and rating spans into the movie div
        movieEl.append(titleEl, ratingEl);

        //add the movie element to the output container in the DOM
        outputDiv.appendChild(movieEl);
      });
    } catch (err) {
      //if something goes wrong show an error message
      outputDiv.textContent = "Error contacting backend.";

      //log the actual error to the browser console for debugging
      console.error(err);
    }
  });
});
