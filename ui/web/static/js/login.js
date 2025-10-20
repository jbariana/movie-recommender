const loginInput = document.getElementById("username");
const loginButton = document.getElementById("login_button");
const loginStatus = document.getElementById("login_status");
const checkSessionButton = document.getElementById("check_session_button");
const sessionStatus = document.getElementById("session_status");

loginButton.addEventListener("click", async () => {
  const username = loginInput.value.trim();
  if (!username) return alert("Enter a username");

  try {
    const res = await fetch("/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username }),
      credentials: "same-origin",
    });
    const data = await res.json();
    loginStatus.textContent = data.message;
  } catch (err) {
    loginStatus.textContent = "Error logging in.";
    console.error(err);
  }
});

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
