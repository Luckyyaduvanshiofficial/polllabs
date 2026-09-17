# Poll & Leaderboard Platform — Product Requirements Document

**Status:** Final v1
**Owner:** Lucky Yaduvanshi / RankLLMs
**License:** Apache 2.0

---

## 1. Overview

An open-source, lightweight platform for polls and leaderboards, built for:

- **Embeddable polls** on GitHub READMEs and static sites — no backend maintenance required for the site embedding it.
- **A dashboard** for authenticated users to create polls, track votes/interactions, and view analytics.
- **Public leaderboards** surfacing top/trending polls across the platform.

### Core Principle
Voting is anonymous and frictionless. Poll creation requires GitHub sign-in — no exceptions. Every poll has a clear owner from creation, which keeps moderation, analytics, and leaderboard rules simple.

---

## 2. Accounts & Authentication

- **Sign-in method: GitHub OAuth only.** No email/password, no other providers at launch.
  - Fits the target audience (developers embedding polls in READMEs) and removes password-storage/reset complexity entirely.
- Signing in is required to:
  - Create a poll
  - View analytics for owned polls
  - Edit or delete owned polls
- Voting never requires sign-in, for anyone, on any poll.

---

## 3. Poll Visibility & Result Display

Two independent settings, set by the poll owner at creation and editable anytime.

### 3.1 Poll Visibility
| Setting | Meaning |
|---|---|
| `public` | Discoverable; eligible for leaderboards/trending if it meets engagement thresholds |
| `private` | Accessible only via direct link or embed; never listed publicly or on leaderboards |

### 3.2 Result Display
| Setting | Behavior |
|---|---|
| `show_counts` | Raw vote numbers shown to everyone after they vote |
| `show_percentage` | Only percentages shown, no raw counts |
| `hidden_until_close` | No results shown to voters until the poll's close time; owner always sees full results in the dashboard |

### 3.3 Combinations
Visibility and result display are independent — any combination is valid (e.g., a `private` poll can still `show_counts`). Leaderboard eligibility depends only on visibility (`public`) plus engagement thresholds, not on result-display setting.

---

## 4. Functional Requirements

### 4.1 Poll Creation
- Requires GitHub sign-in.
- Supports text, images, emoji, or mixed-format options.
- Poll types at launch: single-choice.
- Owner sets: visibility (§3.1), result display (§3.2), optional close date.
- Owner can edit or delete their poll at any time.

### 4.2 Voting
- No sign-in required.
- One-vote-per-voter enforcement (see §4.6 for the full mechanism — summary: cookie/device-token based, tuned to avoid false-positives on embeds).
- Results update immediately after voting, respecting the result-display setting.

### 4.3 Leaderboard & Analytics
- Public leaderboard: top polls / most-voted options / trending, filtered to `public` visibility.
- Dashboard analytics (owner, own polls only):
  - Vote counts over time
  - Option-level breakdown
  - Embed-source / referrer breakdown (which site the votes came from)
  - CSV/JSON export of raw results

### 4.4 Embeds
Two deliverables, both in MVP scope:

1. **Static badge (SVG/PNG)** — for GitHub READMEs and any markdown context that strips `<script>` tags. Shows current results as a rendered image (like a shields.io badge), regenerated on each request or cached with a short TTL. Links out to the live interactive poll on the main site.
2. **Interactive iframe embed** — for static sites/blogs that allow iframes. Full voting UI, live results, respects the poll's visibility and result-display settings.

Both are read/vote-only surfaces; poll creation never happens from an embed.

### 4.5 Documentation
- Hosted on the main site via Astro static pages, SEO-indexable.
- Includes: versioned API reference, embed integration guide (badge + iframe), self-hosting guide.

### 4.6 Vote Abuse Prevention
Tuned specifically to avoid breaking legitimate embed traffic (shared office/college/ISP IPs are common and must not cause false blocks):

- **Primary signal — device token:** random ID issued via httpOnly cookie + localStorage fallback on first interaction with a poll. This is the actual one-vote-per-voter check. It travels correctly across embed contexts and doesn't penalize multiple genuine voters sharing a network.
- **Secondary signal — IP-based rate limiting only, not blocking:** cap votes per minute from a single IP hash to blunt scripted flooding. This never blocks a specific voter's single vote — it only throttles burst traffic.
- Documented publicly as best-effort abuse mitigation, consistent with how open embeddable poll tools generally work — not presented as unbeatable.
- Basic content moderation (profanity/abuse filter) on poll text at creation; report-abuse action on public polls.
- If a poll is deleted, both embed types show a graceful "This poll is no longer available" state.

### 4.7 API
- Versioned from day one (`/api/v1/...`).
- Public API docs generated from the FastAPI OpenAPI schema, published on the docs site.
- CORS: vote/embed endpoints open to any origin (required for embeds to function anywhere); poll-management endpoints restricted to the platform's own frontend origin(s).

---

## 5. Non-Functional Requirements

- **Performance:** Embed widget bundle < 15KB gzipped; sub-200ms vote submission under normal load. Badge generation cached with short TTL to avoid regenerating on every README view.
- **SEO:** Docs and public poll/leaderboard pages statically rendered via Astro, indexable.
- **Scalability:** Support thousands of concurrent votes on commodity hosting without manual intervention.
- **Persistence:** Votes/polls durably stored, independent of VM disk state; scheduled backups.
- **Privacy:** HTTPS everywhere; IP addresses stored as hashes, never raw, to support rate-limiting without retaining PII. No end-to-end encryption — poll votes are aggregate/public-facing data by design.
- **Open Source:** Apache 2.0 license applied consistently (LICENSE file, SPDX headers in source, NOTICE file for any attribution-requiring dependency); clear CONTRIBUTING.md.

---

## 6. Tech Stack

**Frontend**
- Astro — SEO pages, docs, leaderboard/contest pages
- React — dashboard (poll creation, analytics)
- Svelte — interactive embed widget

**Backend**
- FastAPI — API layer
- **PocketBase** — sole BaaS for local development and production at current scale.
  - Chosen specifically so contributors can run the full stack locally with one binary and an embedded SQLite file — no Docker Compose, no external account/API keys, no network dependency to develop offline.
  - No migration to another BaaS is planned. If PocketBase's SQLite backend ever shows measured write-contention at production scale, that becomes its own scoped evaluation at that time — not a pre-committed roadmap item.

**Hosting**
- Azure Free VM (persistent disk) — primary target.
- Fly.io documented as an alternative deployment path.

---

## 7. Account Deletion

- Account deletion is a **request**, not immediate action.
- On request: account is marked `pending_deletion`, user retains access for 7 days (can cancel the request in this window).
- After 7 days: account and all owned polls/votes are permanently deleted.
- Embeds/badges referencing deleted polls fall back to the "no longer available" state (§4.6).

---

## 8. Data Retention

- Polls retained indefinitely unless the owner deletes them or their account completes deletion (§7).
- Votes are retained with their poll; deleting a poll deletes its votes (no orphaned records).
- Regular backups of the persistence layer, independent of VM disk state.

---

## 9. Licensing

**Apache 2.0.** Provides an explicit patent grant alongside broad permissiveness, while remaining suitable for wide embed adoption. Applied via LICENSE file at repo root, SPDX headers in source files, and a NOTICE file if any bundled dependency requires attribution.

---

## 10. Deliverables

- Backend API (polls, votes, leaderboard) — versioned, OpenAPI-documented
- Frontend dashboard (React, embedded in Astro)
- Embeddable widgets: Svelte iframe widget + static SVG/PNG badge generator
- Docs site (Astro, static, SEO-indexed)
- Deployment guide (Azure VM primary; Fly.io alternative)
- Open source repo (GitHub, Apache 2.0, CONTRIBUTING.md)

---

## 11. Future Enhancements (Prioritized)

**P1**
- Real-time vote updates / live leaderboard streaming

**P2**
- Additional poll types: ranked-choice, multi-select, timed polls
- Customizable poll themes/branding
- Multi-tenant SaaS support for orgs/teams
- Third-party integrations (Slack, Discord, GitHub Actions)
- Voting trend-over-time analytics (replaces "demographic insights" — true demographics aren't available without account-gated voting, which conflicts with the anonymous-voting core principle)
