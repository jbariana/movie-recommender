/**
 * utils.js
 * Utility functions used across the application.
 * Currently contains session management helpers.
 */

// Helper: check session on server
export async function isLoggedIn() {
  try {
    const res = await fetch("/session", { credentials: "same-origin" });
    if (!res.ok) return false;
    const data = await res.json();
    return Boolean(data && data.username);
  } catch (e) {
    return false;
  }
}
