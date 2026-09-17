/**
 * Application configuration & base URL resolution.
 * Centralizes environment variables and fallback origin resolution across SSR and client components.
 */

export function getApiUrl(): string {
  if (typeof import.meta !== 'undefined' && import.meta.env?.PUBLIC_API_URL) {
    return (import.meta.env.PUBLIC_API_URL as string).replace(/\/+$/, '');
  }
  return 'http://localhost:8000';
}

export function getSiteUrl(): string {
  if (typeof window !== 'undefined' && window.location?.origin) {
    return window.location.origin;
  }
  if (typeof import.meta !== 'undefined' && import.meta.env?.PUBLIC_SITE_URL) {
    return (import.meta.env.PUBLIC_SITE_URL as string).replace(/\/+$/, '');
  }
  return 'http://localhost:4321';
}

export function getPbUrl(): string {
  if (typeof import.meta !== 'undefined' && import.meta.env?.PUBLIC_PB_URL) {
    return (import.meta.env.PUBLIC_PB_URL as string).replace(/\/+$/, '');
  }
  return 'http://localhost:8090';
}
