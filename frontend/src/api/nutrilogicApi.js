/**
 * nutrilogicApi.js
 * ----------------
 * Thin wrapper around the NutriLogic Django REST API.
 *
 * All functions return a Promise that resolves to the parsed JSON body.
 * On HTTP errors the Promise is rejected with an Error containing the
 * status code and the server message.
 */

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

/**
 * Generic fetch helper with error handling.
 * @param {string} endpoint  - Path relative to BASE_URL (e.g. "/foods/")
 * @param {RequestInit} [options] - fetch options
 * @returns {Promise<any>}
 */
async function apiFetch(endpoint, options = {}) {
  const url = `${BASE_URL}${endpoint}`;
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });

  if (!response.ok) {
    let message = `HTTP ${response.status}`;
    try {
      const data = await response.json();
      message = data.detail || JSON.stringify(data);
    } catch (_) {
      // ignore parse error; use status message
    }
    throw new Error(message);
  }

  return response.json();
}

// ---------------------------------------------------------------------------
// Food endpoints
// ---------------------------------------------------------------------------

/**
 * Fetch all Kenyan foods from the knowledge base.
 * @returns {Promise<Array>}
 */
export function getFoods() {
  return apiFetch("/foods/");
}

/**
 * Fetch foods belonging to a specific food group.
 * @param {string} group - e.g. "vegetables", "legumes", "fish"
 * @returns {Promise<Array>}
 */
export function getFoodsByGroup(group) {
  return apiFetch(`/foods/${encodeURIComponent(group)}/`);
}

/**
 * Fetch micronutrient profile for a specific food.
 * @param {string} foodName - Prolog atom, e.g. "managu"
 * @returns {Promise<Object>}
 */
export function getFoodMicronutrients(foodName) {
  return apiFetch(`/foods/${encodeURIComponent(foodName)}/micronutrients/`);
}

// ---------------------------------------------------------------------------
// Recommendation endpoints
// ---------------------------------------------------------------------------

/**
 * Get meal recommendations for a known health condition.
 * @param {string} condition - e.g. "hypertension", "type2_diabetes", "anaemia"
 * @returns {Promise<{condition: string, recommendations: Array}>}
 */
export function recommendByCondition(condition) {
  return apiFetch("/recommend/condition/", {
    method: "POST",
    body: JSON.stringify({ condition }),
  });
}

/**
 * Get meal recommendations derived from reported symptoms.
 * @param {string[]} symptoms - e.g. ["fatigue", "pale_skin"]
 * @returns {Promise<{symptoms: string[], recommendations: Array}>}
 */
export function recommendBySymptoms(symptoms) {
  return apiFetch("/recommend/symptoms/", {
    method: "POST",
    body: JSON.stringify({ symptoms }),
  });
}
