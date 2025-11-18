/**
 * recsCache.js
 * Background recommendation preloading and caching
 */

let cachedRecs = null;
let isLoading = false;
let loadPromise = null;

/**
 * Preload recommendations in the background
 * Can be called multiple times safely - only loads once
 */
export async function preloadRecommendations() {
  // If already cached, return immediately
  if (cachedRecs) {
    return cachedRecs;
  }

  // If already loading, return the existing promise
  if (isLoading && loadPromise) {
    return loadPromise;
  }

  isLoading = true;
  loadPromise = (async () => {
    try {
      console.log("Preloading recommendations in background...");
      const startTime = performance.now();

      const response = await fetch(`/api/recommendations/content?k=100`, {
        credentials: "same-origin",
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      const endTime = performance.now();

      if (data.error) {
        console.error("Preload error:", data.error);
        return null;
      }

      cachedRecs = data.items || [];
      console.log(
        `✅ Preloaded ${cachedRecs.length} recommendations in ${Math.round(
          endTime - startTime
        )}ms`
      );

      return cachedRecs;
    } catch (error) {
      console.error("Failed to preload recommendations:", error);
      return null;
    } finally {
      isLoading = false;
      loadPromise = null;
    }
  })();

  return loadPromise;
}

/**
 * Get cached recommendations (instant)
 * Returns null if not yet loaded
 */
export function getCachedRecommendations() {
  return cachedRecs;
}

/**
 * Get recommendations (waits if still loading)
 */
export async function getRecommendations() {
  if (cachedRecs) {
    return cachedRecs;
  }

  if (isLoading && loadPromise) {
    return loadPromise;
  }

  return preloadRecommendations();
}

/**
 * Invalidate cache (call after user rates a movie)
 */
export function invalidateCache() {
  console.log("♻️ Invalidating recommendation cache");
  cachedRecs = null;
  isLoading = false;
  loadPromise = null;
}

/**
 * Check if recommendations are ready
 */
export function isReady() {
  return cachedRecs !== null;
}
