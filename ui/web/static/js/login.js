/**
 * login.js
 * user authentication and session management
 * handles login/logout functionality and displays current user status
 */

//get references to login form elements
const loginForm = document.getElementById("login_form");
const loginInput = document.getElementById("username");
const loginStatus = document.getElementById("login_status");

//keep a copy of logged-out markup so we can restore it
const LOGGED_OUT_HTML = loginForm ? loginForm.innerHTML : "";

//render logged in state with username and logout button
function renderLoggedIn(username) {
  if (!loginForm) return;

  //replace login form with user info and logout button
  loginForm.innerHTML = `
    <span class="nav-username" id="nav_username">${username}</span>
    <button id="logout_button" type="button">Logout</button>
    <small id="login_status" class="login-status" aria-live="polite">Logged in</small>
  `;
  document.body.classList.add("logged-in");

  //attach logout handler
  document
    .getElementById("logout_button")
    .addEventListener("click", async () => {
      try {
        //send logout request to backend
        const res = await fetch("/logout", {
          method: "POST",
          credentials: "same-origin",
        });
        await res.json().catch(() => {});

        //restore logged out UI
        renderLoggedOut();

        //redirect to home if on browse page
        if (window.location.pathname === "/browse") {
          window.location.href = "/";
        }
      } catch (err) {
        const s = document.getElementById("login_status");
        if (s) s.textContent = "Logout failed.";
        console.error(err);
      }
    });
}

//render logged out state with login form
function renderLoggedOut() {
  if (!loginForm) return;

  //restore original login form HTML
  loginForm.innerHTML = LOGGED_OUT_HTML;
  document.body.classList.remove("logged-in");

  //reattach login handlers
  initLoginHandlers();
}

//show status message below login form
function showStatus(msg, isError = false) {
  const s = document.getElementById("login_status");
  if (!s) return;
  s.textContent = msg;
  s.style.color = isError ? "#ff8b8b" : "";
}

//attach event handlers to login button and input
function initLoginHandlers() {
  const btn = document.getElementById("login_button");
  const input = document.getElementById("username");
  if (!btn || !input) return;

  //handle login button click
  btn.onclick = async () => {
    const username = input.value.trim();

    //validate username input
    if (!username) {
      showStatus("Enter a username.", true);
      return;
    }

    showStatus("Logging in...");

    try {
      //send login request to backend
      const res = await fetch("/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username }),
        credentials: "same-origin",
      });

      //parse response (handle both JSON and plain text)
      const text = await res.text();
      let data;
      try {
        data = JSON.parse(text);
      } catch {
        data = { message: text };
      }

      //handle successful login
      if (res.ok) {
        renderLoggedIn(username);

        //auto-load recommendations if on browse page
        if (window.location.pathname === "/browse") {
          const { handleActionButton } = await import("./actionHandler.js");
          handleActionButton("get_rec_button");
        }
      } else {
        //show error message
        const errMsg =
          data?.error || data?.message || res.statusText || "Login failed";
        showStatus(`Error logging in: ${errMsg}`, true);
        console.error("Login failed:", res.status, text);
      }
    } catch (err) {
      showStatus("Error logging in (network).", true);
      console.error(err);
    }
  };
}

//check if user is already logged in on page load
async function checkSessionOnLoad() {
  try {
    //query backend for current session
    const res = await fetch("/session", { credentials: "same-origin" });
    if (!res.ok) return;

    const data = await res.json();

    //render logged in state if session exists
    if (data?.username) renderLoggedIn(data.username);
  } catch (e) {
    console.error("Session check failed:", e);
  }
}

//initialize login handlers and check session
initLoginHandlers();
checkSessionOnLoad();
