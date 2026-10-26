/**
 * Application Configuration
 *
 * In production (Vercel), VITE_API_URL should be configured to point to the backend
 * (e.g., https://opsmate-ai.onrender.com).
 * In local development, if VITE_API_URL is unset, it defaults to an empty string (''),
 * allowing Vite's development proxy to forward /api requests to localhost:8000.
 */
const rawApiUrl = import.meta.env.VITE_API_URL || '';

// Strip any trailing slashes to guarantee clean concatenation (e.g. `${API_BASE_URL}/api/...`)
export const API_BASE_URL = rawApiUrl.replace(/\/+$/, '');
