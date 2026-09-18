/**
 * Runtime configuration and base-URL resolution.
 *
 * Single source of truth for every external origin the app talks to. Nothing
 * else in the codebase should hardcode a URL. `PUBLIC_*` vars are inlined at
 * build time by Astro, which is why the Dockerfile takes them as build args.
 */

function trim(value: string): string {
  return value.replace(/\/+$/, '');
}

/** FastAPI backend origin (no trailing slash). */
export function getApiUrl(): string {
  const fromEnv = import.meta.env?.PUBLIC_API_URL as string | undefined;
  if (fromEnv) return trim(fromEnv);
  return 'http://localhost:8000';
}

/** This site's own origin. Prefers the live origin so previews work. */
export function getSiteUrl(): string {
  if (typeof window !== 'undefined' && window.location?.origin) {
    return window.location.origin;
  }
  const fromEnv = import.meta.env?.PUBLIC_SITE_URL as string | undefined;
  if (fromEnv) return trim(fromEnv);
  return 'http://localhost:4321';
}

/** PocketBase origin, used directly for the OAuth2 handshake. */
export function getPbUrl(): string {
  const fromEnv = import.meta.env?.PUBLIC_PB_URL as string | undefined;
  if (fromEnv) return trim(fromEnv);
  return 'http://localhost:8090';
}

/** Versioned API root, e.g. `http://localhost:8000/api/v1`. */
export function getApiBase(): string {
  return `${getApiUrl()}/api/v1`;
}

export const STORAGE_KEYS = {
  /** PocketBase auth token. Signed by PocketBase; the backend verifies it. */
  token: 'polls-lab_auth_token',
  /** Cached user id, so the navbar can render without a round trip. */
  userId: 'polls-lab_user_id',
  /** PKCE verifier, held only between redirect and callback. */
  codeVerifier: 'polls-lab_pkce_verifier',
  /** Where to return after sign-in. */
  returnTo: 'polls-lab_return_to',
  /** Anonymous voter token, mirrored from the httpOnly cookie. */
  deviceToken: 'polls-lab_device_token',
} as const;
