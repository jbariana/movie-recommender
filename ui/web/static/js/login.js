/**
 * login.js
 * User authentication and session management.
 * Handles login/logout functionality and displays current user status.
 */

// get references to important HTML elements used for login and session display
const loginForm = document.getElementById("login_form");
const loginInput = document.getElementById("username");
const loginStatus = document.getElementById("login_status");

// Keep a copy of logged-out markup so we can restore it
const LOGGED_OUT_HTML = loginForm ? loginForm.innerHTML : "";

function renderLoggedIn(username) {
  if (!loginForm) return;
  loginForm.innerHTML = `
    <span class="nav-username" id="nav_username">${username}</span>
    <button id="logout_button" type="button">Logout</button>
    <small id="login_status" class="login-status" aria-live="polite">Logged in</small>
  `;
  document.body.classList.add("logged-in");

  document
    .getElementById("logout_button")
    .addEventListener("click", async () => {
      try {
        const res = await fetch("/logout", {
          method: "POST",
          credentials: "same-origin",
        });
        await res.json().catch(() => {});
        renderLoggedOut();
      } catch (err) {
        const s = document.getElementById("login_status");
        if (s) s.textContent = "Logout failed.";
        console.error(err);
      }
    });
}

function renderLoggedOut() {
  if (!loginForm) return;
  loginForm.innerHTML = LOGGED_OUT_HTML;
  document.body.classList.remove("logged-in");
  initLoginHandlers();
}

function showStatus(msg, isError = false) {
  const s = document.getElementById("login_status");
  if (!s) return;
  s.textContent = msg;
  s.style.color = isError ? "#ff8b8b" : "";
}

function initLoginHandlers() {
  const btn = document.getElementById("login_button");
  const input = document.getElementById("username");
  if (!btn || !input) return;

  btn.onclick = async () => {
    const username = input.value.trim();
    if (!username) {
      showStatus("Enter a username.", true);
      return;
    }
    showStatus("Logging in...");
    try {
      const res = await fetch("/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username }),
        credentials: "same-origin",
      });

      const text = await res.text();
      let data;
      try {
        data = JSON.parse(text);
      } catch {
        data = { message: text };
      }

      if (res.ok) {
        renderLoggedIn(username);
      } else {
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

// Check session on load and render if set
async function checkSessionOnLoad() {
  try {
    const res = await fetch("/session", { credentials: "same-origin" });
    if (!res.ok) return;
    const data = await res.json();
    if (data?.username) renderLoggedIn(data.username);
  } catch (e) {}
}

initLoginHandlers();
checkSessionOnLoad();
