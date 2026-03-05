/**
 * nutrilogicApi.js
 * ----------------
 * Thin wrapper around the NutriLogic Django REST API.
 *
 * All functions return a Promise that resolves to the parsed JSON body.
 * On HTTP errors the Promise is rejected with an Error containing the
 * status code and the server message.
 *
 * Pass `accessToken` (string | null) as the last argument to any function
 * that should send a JWT Authorization header.
 */

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

/**
 * Generic fetch helper with error handling.
 * @param {string} endpoint  - Path relative to BASE_URL (e.g. "/foods/")
 * @param {RequestInit} [options] - fetch options
 * @param {string|null} [token] - JWT access token
 * @returns {Promise<any>}
 */
async function apiFetch(endpoint, options = {}, token = null) {
  const url = `${BASE_URL}${endpoint}`;
  const headers = { "Content-Type": "application/json", ...options.headers };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const response = await fetch(url, { ...options, headers });

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
 * @param {string|null} [token] - JWT access token (optional; saves log when provided)
 * @returns {Promise<{condition: string, recommendations: Array}>}
 */
export function recommendByCondition(condition, token = null) {
  return apiFetch("/recommend/condition/", {
    method: "POST",
    body: JSON.stringify({ condition }),
  }, token);
}

/**
 * Get meal recommendations derived from reported symptoms.
 * @param {string[]} symptoms - e.g. ["fatigue", "pale_skin"]
 * @param {string|null} [token] - JWT access token (optional; saves log when provided)
 * @returns {Promise<{symptoms: string[], recommendations: Array}>}
 */
export function recommendBySymptoms(symptoms, token = null) {
  return apiFetch("/recommend/symptoms/", {
    method: "POST",
    body: JSON.stringify({ symptoms }),
  }, token);
}

// ---------------------------------------------------------------------------
// Authentication endpoints
// ---------------------------------------------------------------------------

/**
 * Register a new user account.
 * @param {{username: string, email: string, password: string, password2: string}} data
 * @returns {Promise<{detail: string}>}
 */
export function registerUser(data) {
  return apiFetch("/auth/register/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * Obtain a JWT token pair (login).
 * @param {string} username
 * @param {string} password
 * @returns {Promise<{access: string, refresh: string}>}
 */
export function obtainToken(username, password) {
  return apiFetch("/auth/token/", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
}

/**
 * Refresh the access token using the stored refresh token.
 * @param {string} refresh
 * @returns {Promise<{access: string}>}
 */
export function refreshToken(refresh) {
  return apiFetch("/auth/token/refresh/", {
    method: "POST",
    body: JSON.stringify({ refresh }),
  });
}

// ---------------------------------------------------------------------------
// Profile endpoint (requires auth)
// ---------------------------------------------------------------------------

/**
 * Fetch the authenticated user's profile.
 * @param {string} token - JWT access token
 * @returns {Promise<Object>}
 */
export function getProfile(token) {
  return apiFetch("/profile/", {}, token);
}

/**
 * Partially update the authenticated user's profile.
 * @param {Object} data - Fields to update
 * @param {string} token - JWT access token
 * @returns {Promise<Object>}
 */
export function updateProfile(data, token) {
  return apiFetch("/profile/", {
    method: "PATCH",
    body: JSON.stringify(data),
  }, token);
}

// ---------------------------------------------------------------------------
// Recommendation history endpoint (requires auth)
// ---------------------------------------------------------------------------

/**
 * Fetch the last 20 recommendation logs for the authenticated user.
 * @param {string} token - JWT access token
 * @returns {Promise<Array>}
 */
export function getRecommendationHistory(token) {
  return apiFetch("/history/", {}, token);
}
