/**
 * Typed client for the Polls Lab API.
 *
 * Every network call in the app goes through here so that auth headers, error
 * shape and result handling are consistent. Results are returned as a tagged
 * union rather than thrown, because every caller in this app renders an error
 * state instead of crashing.
 */

import { getApiBase, STORAGE_KEYS } from './config';
import { readToken, clearSession } from './auth';

export type ResultDisplay = 'show_counts' | 'show_percentage' | 'hidden_until_close';
export type Visibility = 'public' | 'private';

export interface PollOption {
  id: string;
  text: string;
  icon_or_image?: string | null;
  /** Null when the backend masked it for this viewer. */
  vote_count?: number | null;
  percentage?: number | null;
  is_correct?: boolean | null;
  voters?: string[] | null;
}

export interface Poll {
  id: string;
  title: string;
  description?: string | null;
  options: PollOption[];
  visibility: Visibility;
  result_display: ResultDisplay;
  owner: string;
  total_votes?: number | null;
  created: string;
  updated: string;
  close_at?: string | null;
  appearance?: PollAppearance | null;
  max_selections: number;
  is_quiz: boolean;
  show_voters: boolean;
}

export interface PollAppearance {
  theme?: string | null;
  bg?: string | null;
  accent?: string | null;
  ink?: string | null;
  radius?: string | null;
  font?: string | null;
  effect?: string | null;
  layout?: string | null;
}

export interface PollList {
  items: Poll[];
  page: number;
  per_page: number;
  total_items: number;
  total_pages: number;
}

export interface Analytics {
  poll_id: string;
  title: string;
  total_votes: number;
  options_breakdown: Record<string, number>;
  referrers_breakdown: Record<string, number>;
  votes_over_time: Record<string, number>;
}

export interface MostVotedOption {
  poll_id: string;
  poll_title: string;
  option_id: string;
  option_text: string;
  vote_count: number;
}

export interface CurrentUser {
  user_id: string;
  provider: string;
  deletion_status: string;
  deletion_scheduled_for?: string | null;
}

export interface VoteResult {
  success: boolean;
  message: string;
  poll_id: string;
  device_token: string;
  total_votes?: number | null;
  options: PollOption[];
  selected_options?: string[] | null;
}

export type ApiResult<T> =
  | { ok: true; data: T }
  | { ok: false; error: string; status: number };

/** Maps a status code to a message a person can act on. */
function messageForStatus(status: number, detail?: string): string {
  if (detail) return detail;
  if (status === 0) return 'Cannot reach the API. Check that the backend is running.';
  if (status === 401) return 'Your session expired. Sign in again to continue.';
  if (status === 403) return 'You do not have access to this.';
  if (status === 404) return 'Not found.';
  if (status === 429) return 'Too many requests. Wait a minute and try again.';
  if (status >= 500) return 'The API failed to respond. Try again shortly.';
  return `Request failed (${status}).`;
}

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PATCH' | 'DELETE';
  body?: unknown;
  /** Attach the bearer token. Required for owner-scoped endpoints. */
  auth?: boolean;
  /** Send cookies, needed so the vote device-token cookie round-trips. */
  credentials?: boolean;
  signal?: AbortSignal;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<ApiResult<T>> {
  const { method = 'GET', body, auth = false, credentials = false, signal } = options;
  const headers: Record<string, string> = {};

  if (body !== undefined) headers['Content-Type'] = 'application/json';

  if (auth) {
    const token = readToken();
    if (!token) {
      return { ok: false, error: 'Sign in to continue.', status: 401 };
    }
    headers.Authorization = `Bearer ${token}`;
  }

  let response: Response;
  try {
    response = await fetch(`${getApiBase()}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      credentials: credentials ? 'include' : 'same-origin',
      signal,
    });
  } catch (err) {
    if ((err as Error)?.name === 'AbortError') {
      return { ok: false, error: 'Request cancelled.', status: 0 };
    }
    return { ok: false, error: messageForStatus(0), status: 0 };
  }

  // A rejected token is dead: drop it so the UI falls back to signed-out
  // rather than looping on a credential the backend will not accept.
  if (response.status === 401 && auth) {
    clearSession();
  }

  if (!response.ok) {
    let detail: string | undefined;
    try {
      const payload = await response.json();
      if (typeof payload?.detail === 'string') {
        detail = payload.detail;
      } else if (Array.isArray(payload?.detail) && payload.detail[0]?.msg) {
        // FastAPI validation errors arrive as a list.
        detail = String(payload.detail[0].msg);
      }
    } catch {
      // Non-JSON error body; fall through to the status message.
    }
    return { ok: false, error: messageForStatus(response.status, detail), status: response.status };
  }

  if (response.status === 204) {
    return { ok: true, data: undefined as T };
  }

  try {
    return { ok: true, data: (await response.json()) as T };
  } catch {
    return { ok: false, error: 'The API returned a malformed response.', status: response.status };
  }
}

/* ---- Polls -------------------------------------------------------------- */

export function listPolls(
  params: { page?: number; perPage?: number; sort?: string } = {},
  signal?: AbortSignal
): Promise<ApiResult<PollList>> {
  const query = new URLSearchParams();
  query.set('page', String(params.page ?? 1));
  query.set('per_page', String(params.perPage ?? 20));
  // Only whitelisted fields are accepted server-side; anything else falls back.
  query.set('sort', params.sort ?? '-created');
  return request<PollList>(`/polls?${query}`, { signal });
}

export function getPoll(pollId: string, signal?: AbortSignal): Promise<ApiResult<Poll>> {
  // Credentials included so the device-token cookie lets the backend decide
  // whether this viewer has already voted (and may see raw counts).
  return request<Poll>(`/polls/${encodeURIComponent(pollId)}`, { credentials: true, signal });
}

export function createPoll(payload: unknown): Promise<ApiResult<Poll>> {
  return request<Poll>('/polls', { method: 'POST', body: payload, auth: true });
}

export function updatePoll(pollId: string, payload: unknown): Promise<ApiResult<Poll>> {
  return request<Poll>(`/polls/${encodeURIComponent(pollId)}`, {
    method: 'PATCH',
    body: payload,
    auth: true,
  });
}

export function deletePoll(pollId: string): Promise<ApiResult<void>> {
  return request<void>(`/polls/${encodeURIComponent(pollId)}`, { method: 'DELETE', auth: true });
}

export function reportPoll(pollId: string, reason: string): Promise<ApiResult<unknown>> {
  return request(`/polls/${encodeURIComponent(pollId)}/report`, {
    method: 'POST',
    body: { reason },
  });
}

/**
 * Uploads an option image. Multipart, so it bypasses the JSON helper above and
 * deliberately sets no Content-Type: the browser must add the boundary.
 */
export async function uploadPollImage(
  file: File,
  pollId?: string
): Promise<ApiResult<{ id: string; url: string }>> {
  const token = readToken();
  if (!token) return { ok: false, error: 'Sign in to upload images.', status: 401 };

  const form = new FormData();
  form.append('file', file);
  if (pollId) form.append('poll_id', pollId);

  try {
    const response = await fetch(`${getApiBase()}/polls/images`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: form,
    });

    if (!response.ok) {
      if (response.status === 401) clearSession();
      let detail: string | undefined;
      try {
        detail = (await response.json())?.detail;
      } catch {
        /* non-JSON body */
      }
      return { ok: false, error: messageForStatus(response.status, detail), status: response.status };
    }

    return { ok: true, data: await response.json() };
  } catch {
    return { ok: false, error: messageForStatus(0), status: 0 };
  }
}

/* ---- Votes -------------------------------------------------------------- */

export function submitVote(
  pollId: string,
  optionIds: string[],
  meta: { referrer?: string } = {}
): Promise<ApiResult<VoteResult>> {
  let deviceToken: string | null = null;
  try {
    deviceToken = localStorage.getItem(STORAGE_KEYS.deviceToken);
  } catch {
    // Storage blocked; the httpOnly cookie is the primary signal anyway.
  }

  return request<VoteResult>(`/votes/${encodeURIComponent(pollId)}`, {
    method: 'POST',
    credentials: true,
    body: {
      // Single-choice polls take a bare string; multi-select takes the list.
      option_id: optionIds.length === 1 ? optionIds[0] : optionIds,
      device_token: deviceToken,
      embed_referrer: meta.referrer ?? null,
    },
  });
}

/* ---- Leaderboard ------------------------------------------------------- */

export function getTrending(limit = 10, signal?: AbortSignal) {
  return request<{ leaderboard: Poll[]; total: number }>(
    `/leaderboard/trending?limit=${limit}`,
    { signal }
  );
}

export function getTop(limit = 10, signal?: AbortSignal) {
  return request<{ leaderboard: Poll[]; total: number }>(`/leaderboard/top?limit=${limit}`, {
    signal,
  });
}

export function getMostVotedOptions(limit = 10, signal?: AbortSignal) {
  return request<{ items: MostVotedOption[]; total: number }>(
    `/leaderboard/most-voted-options?limit=${limit}`,
    { signal }
  );
}

/* ---- Analytics --------------------------------------------------------- */

export function getAnalytics(pollId: string, signal?: AbortSignal): Promise<ApiResult<Analytics>> {
  return request<Analytics>(`/analytics/${encodeURIComponent(pollId)}`, { auth: true, signal });
}

/**
 * Downloads an export. Uses fetch + blob rather than a plain link because the
 * endpoint requires an Authorization header.
 */
export async function downloadExport(
  pollId: string,
  format: 'csv' | 'json'
): Promise<ApiResult<Blob>> {
  const token = readToken();
  if (!token) return { ok: false, error: 'Sign in to export.', status: 401 };

  try {
    const response = await fetch(
      `${getApiBase()}/analytics/${encodeURIComponent(pollId)}/export?format=${format}`,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    if (!response.ok) {
      if (response.status === 401) clearSession();
      return { ok: false, error: messageForStatus(response.status), status: response.status };
    }
    return { ok: true, data: await response.blob() };
  } catch {
    return { ok: false, error: messageForStatus(0), status: 0 };
  }
}

/* ---- Auth -------------------------------------------------------------- */

export function getCurrentUser(signal?: AbortSignal): Promise<ApiResult<CurrentUser>> {
  return request<CurrentUser>('/auth/me', { auth: true, signal });
}

export function requestAccountDeletion(): Promise<ApiResult<unknown>> {
  return request('/auth/delete-account', { method: 'POST', auth: true });
}

export function cancelAccountDeletion(): Promise<ApiResult<unknown>> {
  return request('/auth/cancel-delete-account', { method: 'POST', auth: true });
}

/* ---- Health ------------------------------------------------------------ */

export function getHealth(signal?: AbortSignal) {
  return request<{ status: string; service: string }>('/health', { signal });
}
