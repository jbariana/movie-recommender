document.querySelectorAll("button").forEach((button) => {
  button.addEventListener("click", () => {
    fetch("/api/button-click", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ button: button.id }),
    })
      .then(res => res.json())
      .then(data => alert(`Backend says: ${data.button}`))
      .catch(() => alert("Error contacting backend"));
  });
});
