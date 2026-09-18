/**
 * GitHub sign-in via PocketBase OAuth2.
 *
 * The token this module stores is issued and signed by PocketBase. The backend
 * verifies it against PocketBase on every authenticated request, so a token
 * this client invents is worthless. Nothing here may fabricate an identity.
 *
 * Flow:
 *   1. `startSignIn` asks PocketBase which providers are configured, builds a
 *      PKCE verifier, and redirects to GitHub.
 *   2. GitHub redirects back to /auth/callback with a code.
 *   3. `completeSignIn` exchanges that code with PocketBase for a real token.
 */

import { getPbUrl, getSiteUrl, STORAGE_KEYS } from './config';

export interface AuthMethodProvider {
  name: string;
  displayName: string;
  state: string;
  authURL: string;
  codeVerifier: string;
  codeChallenge: string;
  codeChallengeMethod: string;
}

export const REDIRECT_PATH = '/auth/callback';

function safeGet(key: string): string | null {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

function safeSet(key: string, value: string): void {
  try {
    localStorage.setItem(key, value);
  } catch {
    // Storage blocked. Sign-in cannot persist; surfaced by the caller.
  }
}

function safeRemove(key: string): void {
  try {
    localStorage.removeItem(key);
  } catch {
    /* no-op */
  }
}

/** The stored PocketBase token, or null when signed out. */
export function readToken(): string | null {
  if (typeof window === 'undefined') return null;
  return safeGet(STORAGE_KEYS.token);
}

/** Cached user id. Display only; never trusted for authorization. */
export function readUserId(): string | null {
  if (typeof window === 'undefined') return null;
  return safeGet(STORAGE_KEYS.userId);
}

export function isSignedIn(): boolean {
  return Boolean(readToken());
}

export function storeSession(token: string, userId: string): void {
  safeSet(STORAGE_KEYS.token, token);
  safeSet(STORAGE_KEYS.userId, userId);
}

/** Drops all session state. Called on sign-out and on any 401. */
export function clearSession(): void {
  safeRemove(STORAGE_KEYS.token);
  safeRemove(STORAGE_KEYS.userId);
  safeRemove(STORAGE_KEYS.codeVerifier);
}

export function signOut(redirectTo = '/'): void {
  clearSession();
  window.location.href = redirectTo;
}

/**
 * Lists the OAuth2 providers PocketBase has configured. An empty list means
 * GitHub OAuth has not been enabled in the PocketBase admin UI yet, which is a
 * setup problem worth reporting precisely rather than failing opaquely.
 */
export async function listAuthProviders(): Promise<AuthMethodProvider[]> {
  const response = await fetch(`${getPbUrl()}/api/collections/users/auth-methods`);
  if (!response.ok) {
    throw new Error(`PocketBase returned ${response.status} for auth-methods.`);
  }
  const payload = await response.json();
  // PocketBase 0.22 returns authProviders; newer builds nest under oauth2.
  const providers = payload?.oauth2?.providers ?? payload?.authProviders ?? [];
  return providers as AuthMethodProvider[];
}

/**
 * Begins sign-in by redirecting to GitHub. Throws with an actionable message
 * when the provider is not configured, so the UI can say what to fix.
 */
export async function startSignIn(returnTo?: string): Promise<void> {
  const providers = await listAuthProviders();
  const github = providers.find((p) => p.name === 'github');

  if (!github) {
    const names = providers.map((p) => p.name).join(', ') || 'none';
    throw new Error(
      `GitHub OAuth is not enabled in PocketBase. Configured providers: ${names}. ` +
        `Enable it under Settings, Auth providers in the PocketBase admin UI.`
    );
  }

  // The verifier must survive the redirect to be exchanged on return.
  safeSet(STORAGE_KEYS.codeVerifier, github.codeVerifier);
  safeSet(STORAGE_KEYS.returnTo, returnTo ?? window.location.pathname);

  const redirectUri = `${getSiteUrl()}${REDIRECT_PATH}`;
  // PocketBase pre-builds authURL with state and challenge; append our redirect.
  window.location.href = `${github.authURL}${encodeURIComponent(redirectUri)}`;
}

export interface CompletedSignIn {
  userId: string;
  returnTo: string;
}

/**
 * Exchanges the OAuth code for a real PocketBase token. Called only by the
 * callback page.
 */
export async function completeSignIn(params: URLSearchParams): Promise<CompletedSignIn> {
  const code = params.get('code');
  const state = params.get('state');
  const oauthError = params.get('error');

  if (oauthError) {
    throw new Error(`GitHub declined the sign-in request (${oauthError}).`);
  }
  if (!code || !state) {
    throw new Error('The sign-in link is missing its code. Start again from Sign in.');
  }

  const codeVerifier = safeGet(STORAGE_KEYS.codeVerifier);
  if (!codeVerifier) {
    throw new Error(
      'This sign-in could not be verified, which happens when the link is reused or opened ' +
        'in a different browser. Start again from Sign in.'
    );
  }

  const response = await fetch(`${getPbUrl()}/api/collections/users/auth-with-oauth2`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      provider: 'github',
      code,
      codeVerifier,
      redirectUrl: `${getSiteUrl()}${REDIRECT_PATH}`,
    }),
  });

  // Single-use: clear the verifier whether or not the exchange succeeded.
  safeRemove(STORAGE_KEYS.codeVerifier);

  if (!response.ok) {
    let detail = '';
    try {
      const payload = await response.json();
      detail = payload?.message ? ` ${payload.message}` : '';
    } catch {
      /* non-JSON body */
    }
    throw new Error(`PocketBase rejected the sign-in (${response.status}).${detail}`);
  }

  const payload = await response.json();
  const token: string | undefined = payload?.token;
  const userId: string | undefined = payload?.record?.id;

  if (!token || !userId) {
    throw new Error('PocketBase returned an incomplete session. Try signing in again.');
  }

  storeSession(token, userId);

  const returnTo = safeGet(STORAGE_KEYS.returnTo) || '/dashboard';
  safeRemove(STORAGE_KEYS.returnTo);

  return { userId, returnTo };
}
