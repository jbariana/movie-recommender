// get references to important HTML elements used for login and session display
const loginInput = document.getElementById("username"); //<input> field where user types their username
const loginButton = document.getElementById("login_button"); //button that triggers login
const loginStatus = document.getElementById("login_status"); //element to show login result message (success/error)
const checkSessionButton = document.getElementById("check_session_button"); //optional button to check current session
const sessionStatus = document.getElementById("session_status"); //element to display session info

//when the login button is clicked, attempt to log the user in
loginButton.addEventListener("click", async () => {
  // Get the trimmed username from the input box
  const username = loginInput.value.trim();

  try {
    // Send a POST request to the Flask /login route
    // The request includes the username in JSON format
    // 'credentials: "same-origin"' ensures that cookies (including session cookies) are sent and received
    const res = await fetch("/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username }),
      credentials: "same-origin",
    });

    //wait for the server to respond and parse the JSON result
    const data = await res.json();

    //display the returned message (e.g., "Logged in as <name>") in the UI
    loginStatus.textContent = data.message;
  } catch (err) {
    //if something goes wrong display error message
    loginStatus.textContent = "Error logging in.";

    //log detailed error info in the console for debugging
    console.error(err);
  }
});

//The check session button may not always exist (depends on the page layout)
//Only add a listener if it’s present
if (checkSessionButton) {
  checkSessionButton.addEventListener("click", async () => {
    try {
      //send a GET request to the Flask /session endpoint
      //this endpoint returns the current session info (e.g., username)
      const res = await fetch("/session", { credentials: "same-origin" });

      //parse JSON response
      const data = await res.json();

      //display the session data in the UI
      // JSON.stringify makes sure it's shown as readable text
      sessionStatus.textContent = JSON.stringify(data);
    } catch (err) {
      //if an error occurs show error message
      sessionStatus.textContent = "Error checking session.";

      //log the detailed error to the browser console
      console.error(err);
    }
  });
}
