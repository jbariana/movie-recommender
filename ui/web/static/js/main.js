document.addEventListener("DOMContentLoaded", () => {
  const buttons = document.querySelectorAll("button");

  buttons.forEach((button) => {
    button.addEventListener("click", () => {
      const payload = {
        button: button.id || button.dataset.action || button.textContent,
      };

      fetch("/api/button-click", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })
        .then((response) => {
          if (!response.ok) {
            return response.text().then((txt) => {
              console.error("Request failed:", response.status, txt);
              throw new Error("Request failed");
            });
          }
          const ct = response.headers.get("content-type") || "";
          if (!ct.includes("application/json")) {
            return response.text().then((txt) => ({ raw: txt }));
          }
          return response.json();
        })
        .then((data) => {
          console.log("Backend response:", data);
          const msg =
            (data && data.result) ||
            (data && data.recommendations && Array.isArray(data.recommendations)
              ? data.recommendations.slice(0, 5).join("\n")
              : null) ||
            (data && data.recommendations && String(data.recommendations)) ||
            (data && data.raw) ||
            `Handled: ${payload.button || payload}`;
          alert(String(msg));
        })
        .catch((err) => {
          console.error(err);
          alert("Error contacting backend (see console)");
        });
    });
  });
});
