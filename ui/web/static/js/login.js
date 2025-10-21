// get references to important HTML elements used for login and session display
const loginForm = document.getElementById("login_form");
const loginInput = document.getElementById("username"); //<input> field where user types their username
const loginButton = document.getElementById("login_button"); //button that triggers login
const loginStatus = document.getElementById("login_status"); //element to show login result message (success/error)
const checkSessionButton = document.getElementById("check_session_button"); //optional button to check current session
const sessionStatus = document.getElementById("session_status"); //element to display session info

// keep original logged-out markup so we can restore it on logout
const LOGGED_OUT_HTML = loginForm ? loginForm.innerHTML : "";

// render logged-in UI (username + logout)
function renderLoggedIn(username) {
  if (!loginForm) return;
  loginForm.innerHTML = `
    <span class="nav-username" id="nav_username">${username}</span>
    <button id="logout_button" type="button">Logout</button>
    <small id="login_status" class="login-status" aria-live="polite"></small>
  `;
  // mark page as logged-in so nav styling can adjust
  document.body.classList.add("logged-in");

  const logoutButton = document.getElementById("logout_button");
  const newLoginStatus = document.getElementById("login_status");
  if (newLoginStatus) newLoginStatus.textContent = `Logged in as ${username}`;
  logoutButton?.addEventListener("click", async () => {
    try {
      const res = await fetch("/logout", {
        method: "POST",
        credentials: "same-origin",
      });
      await res.json();
      renderLoggedOut();
    } catch (err) {
      newLoginStatus.textContent = "Logout failed.";
      console.error(err);
    }
  });
}

// restore logged-out form
function renderLoggedOut() {
  if (!loginForm) return;
  loginForm.innerHTML = LOGGED_OUT_HTML;
  // remove logged-in marker so nav reverts
  document.body.classList.remove("logged-in");
  // re-wire the original handlers (re-initialize this module)
  initLoginHandlers();
}

// initialize login handlers (callable to re-wire after DOM replace)
function initLoginHandlers() {
  const input = document.getElementById("username");
  const btn = document.getElementById("login_button");
  const status = document.getElementById("login_status");
  if (!btn || !input) return;

  btn.addEventListener("click", async () => {
    const username = input.value.trim();
    if (!username) {
      status && (status.textContent = "Enter a username.");
      return;
    }
    try {
      const res = await fetch("/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username }),
        credentials: "same-origin",
      });
      const data = await res.json();
      if (res.ok) {
        // show username and logout button
        renderLoggedIn(username);
      } else {
        status &&
          (status.textContent = data.error || data.message || "Login failed.");
      }
    } catch (err) {
      status && (status.textContent = "Error logging in.");
      console.error(err);
    }
  });
}

// optional session check on load to show logged-in user if session exists
async function checkSessionOnLoad() {
  try {
    const res = await fetch("/session", { credentials: "same-origin" });
    if (!res.ok) return;
    const data = await res.json();
    const username = data?.username;
    if (username) renderLoggedIn(username);
  } catch (err) {
    // ignore
  }
}

// wire up check-session button (if present)
if (checkSessionButton) {
  checkSessionButton.addEventListener("click", async () => {
    try {
      const res = await fetch("/session", { credentials: "same-origin" });
      const data = await res.json();
      sessionStatus.textContent = JSON.stringify(data);
    } catch (err) {
      sessionStatus.textContent = "Error checking session.";
      console.error(err);
    }
  });
}

// bootstrap
initLoginHandlers();
checkSessionOnLoad();
