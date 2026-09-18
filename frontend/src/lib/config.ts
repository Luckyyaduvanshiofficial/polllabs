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

/**
 * Origins written by the container entrypoint into runtime-config.js, loaded
 * before this module runs.
 *
 * Astro inlines `PUBLIC_*` at build time, so an image built without those build
 * args ships localhost origins and every request from a deployed site goes to
 * the viewer's own machine. Reading them at runtime means ordinary environment
 * variables work and one image serves any environment. Runtime wins over the
 * build-time value; build-time still covers `pnpm dev` and plain static hosting.
 */
interface RuntimeConfig {
  apiUrl?: string;
  siteUrl?: string;
  pbUrl?: string;
}

function runtime(): RuntimeConfig {
  if (typeof window === 'undefined') return {};
  return (window as unknown as { __POLLS_LAB_CONFIG__?: RuntimeConfig }).__POLLS_LAB_CONFIG__ ?? {};
}

/** FastAPI backend origin (no trailing slash). */
export function getApiUrl(): string {
  const fromRuntime = runtime().apiUrl;
  if (fromRuntime) return trim(fromRuntime);
  const fromEnv = import.meta.env?.PUBLIC_API_URL as string | undefined;
  if (fromEnv) return trim(fromEnv);
  return 'http://localhost:8000';
}

/** This site's own origin. Prefers the live origin so previews work. */
export function getSiteUrl(): string {
  if (typeof window !== 'undefined' && window.location?.origin) {
    return window.location.origin;
  }
  const fromRuntime = runtime().siteUrl;
  if (fromRuntime) return trim(fromRuntime);
  const fromEnv = import.meta.env?.PUBLIC_SITE_URL as string | undefined;
  if (fromEnv) return trim(fromEnv);
  return 'http://localhost:4321';
}

/** PocketBase origin, used directly for the OAuth2 handshake. */
export function getPbUrl(): string {
  const fromRuntime = runtime().pbUrl;
  if (fromRuntime) return trim(fromRuntime);
  const fromEnv = import.meta.env?.PUBLIC_PB_URL as string | undefined;
  if (fromEnv) return trim(fromEnv);
  return 'http://localhost:8090';
}

/** Versioned API root, e.g. `http://localhost:8000/api/v1`. */
export function getApiBase(): string {
  return `${getApiUrl()}/api/v1`;
}

/**
 * Detects the failure mode that produces a bare "Failed to fetch" in the
 * browser: a static build deployed to a real domain while PUBLIC_API_URL and
 * PUBLIC_PB_URL still hold their localhost defaults. Those are inlined at build
 * time, so a deploy that forgets the build args silently ships a site whose
 * every request goes to the viewer's own machine.
 *
 * Returns the misconfigured variable names, or an empty array when fine.
 */
export function findMisconfiguredOrigins(): string[] {
  if (typeof window === 'undefined') return [];

  const host = window.location.hostname;
  const servedLocally =
    host === 'localhost' || host === '127.0.0.1' || host === '0.0.0.0' || host.endsWith('.local');
  if (servedLocally) return [];

  const pointsAtLocalhost = (url: string) =>
    url.includes('localhost') || url.includes('127.0.0.1');

  const broken: string[] = [];
  if (pointsAtLocalhost(getApiUrl())) broken.push('PUBLIC_API_URL');
  if (pointsAtLocalhost(getPbUrl())) broken.push('PUBLIC_PB_URL');
  return broken;
}

/** Logs the misconfiguration once, with the fix, so it is visible in devtools. */
export function warnIfMisconfigured(): void {
  const broken = findMisconfiguredOrigins();
  if (broken.length === 0) return;

  console.error(
    `[polls-lab] ${broken.join(' and ')} still ` +
      `${broken.length > 1 ? 'point' : 'points'} at localhost in this build, so requests go to ` +
      `the viewer's own machine and fail. Set them as environment variables on the frontend ` +
      `service and restart it.`
  );
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
