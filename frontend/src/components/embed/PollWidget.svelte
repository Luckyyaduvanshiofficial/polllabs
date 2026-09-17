<script lang="ts">
  interface PollOption {
    id: string;
    text: string;
    icon_or_image?: string | null;
    vote_count?: number | null;
    percentage?: number | null;
  }

  interface PollAppearance {
    theme?: string | null;
    bg?: string | null;
    accent?: string | null;
    ink?: string | null;
    radius?: string | null;
    font?: string | null;
    effect?: string | null;
    layout?: string | null;
  }

  interface PollData {
    id: string;
    title: string;
    description?: string | null;
    options: PollOption[];
    visibility: 'public' | 'private';
    result_display: 'show_counts' | 'show_percentage' | 'hidden_until_close';
    owner: string;
    total_votes?: number | null;
    close_at?: string | null;
    appearance?: PollAppearance | null;
  }

  interface Props {
    pollId?: string;
    apiBaseUrl?: string;
    initialPoll?: PollData | null;
  }

  let {
    pollId = '',
    apiBaseUrl = '',
    initialPoll = null,
  }: Props = $props();

  let apiBase = $derived(apiBaseUrl || 'http://localhost:8000');

  // Use $state.raw to eliminate deep proxy overhead for wholesale-reassigned API payloads (Svelte 5 best practices)
  let localPoll = $state.raw<PollData | null>(null);
  let poll = $derived(localPoll ?? initialPoll);

  let loading = $state<boolean>(false);
  let isUnavailable = $state<boolean>(false);
  let errorMsg = $state<string | null>(null);

  let hasVoted = $state<boolean>(false);
  let selectedOptionId = $state<string | null>(null);
  let isSubmitting = $state<boolean>(false);

  let showReportModal = $state<boolean>(false);
  let reportReason = $state<string>('');
  let reportSubmitting = $state<boolean>(false);
  let reportFeedback = $state<string | null>(null);

  function checkIsClosed(closeAt?: string | null): boolean {
    if (!closeAt) return false;
    try {
      const d = new Date(closeAt);
      return Date.now() >= d.getTime();
    } catch {
      return false;
    }
  }

  let effectivePollId = $derived(poll?.id || pollId);
  let isClosed = $derived(checkIsClosed(poll?.close_at));
  let isHiddenResults = $derived(
    poll?.result_display === 'hidden_until_close' && !isClosed
  );

  // --- Phase 7 themes: appearance registry (preset + user overrides) ---
  const KNOWN_THEMES = ['minimal', 'whatsapp', 'telegram', 'story', 'youtube-grid'];
  const KNOWN_RADIUS = ['pill', 'rounded', 'sharp'];
  const KNOWN_FONTS = ['system', 'serif', 'mono', 'condensed'];
  const HEX_RE = /^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/;

  function cleanHex(value: unknown): string | null {
    return typeof value === 'string' && HEX_RE.test(value) ? value.toLowerCase() : null;
  }

  let theme = $derived(
    poll?.appearance?.theme && KNOWN_THEMES.includes(poll.appearance.theme)
      ? poll.appearance.theme
      : 'minimal'
  );
  let layout = $derived(
    poll?.appearance?.layout === 'grid' || poll?.appearance?.layout === 'list'
      ? poll.appearance.layout
      : theme === 'youtube-grid'
        ? 'grid'
        : 'list'
  );
  let isGrid = $derived(layout === 'grid');
  let radius = $derived(
    poll?.appearance?.radius && KNOWN_RADIUS.includes(poll.appearance.radius)
      ? poll.appearance.radius
      : 'rounded'
  );
  let font = $derived(
    poll?.appearance?.font && KNOWN_FONTS.includes(poll.appearance.font)
      ? poll.appearance.font
      : 'system'
  );
  // data-effect hook for Phase 6 confetti (no behavior yet)
  let effect = $derived(poll?.appearance?.effect === 'confetti' ? 'confetti' : 'none');

  let customStyle = $derived.by(() => {
    const parts: string[] = [];
    const bg = cleanHex(poll?.appearance?.bg);
    const accent = cleanHex(poll?.appearance?.accent);
    const ink = cleanHex(poll?.appearance?.ink);
    if (bg) parts.push(`--pw-bg:${bg}`);
    if (accent) parts.push(`--pw-accent:${accent}`);
    if (ink) parts.push(`--pw-ink:${ink}`);
    return parts.length ? parts.join(';') : null;
  });

  async function loadPoll(id: string) {
    loading = true;
    errorMsg = null;
    isUnavailable = false;

    try {
      const res = await fetch(`${apiBase}/api/v1/polls/${id}`, {
        credentials: 'include',
      });
      if (res.status === 404) {
        isUnavailable = true;
        localPoll = null;
        return;
      }
      if (!res.ok) {
        throw new Error('Failed to load poll data');
      }
      const data = await res.json();
      localPoll = data;

      // Check if user has previously voted on this poll in localStorage
      try {
        const storedVote = localStorage.getItem(`polllabs_voted_${id}`);
        if (storedVote) {
          hasVoted = true;
          selectedOptionId = storedVote;
        }
      } catch {}
    } catch (err: any) {
      errorMsg = err.message || 'Unable to connect to poll service.';
      isUnavailable = true;
    } finally {
      loading = false;
    }
  }

  async function submitVote(optionId: string) {
    if (hasVoted || isSubmitting || !effectivePollId || isClosed) return;

    isSubmitting = true;
    errorMsg = null;
    selectedOptionId = optionId;

    let deviceToken: string | null = null;
    try {
      deviceToken = localStorage.getItem('polllabs_device_token');
    } catch {}

    try {
      const res = await fetch(`${apiBase}/api/v1/votes/${effectivePollId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(deviceToken ? { 'x-device-token': deviceToken } : {}),
        },
        body: JSON.stringify({
          option_id: optionId,
          device_token: deviceToken,
          embed_referrer: typeof document !== 'undefined' ? document.referrer : '',
        }),
        credentials: 'include',
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Failed to submit vote');
      }

      const data = await res.json();
      hasVoted = true;

      // Save returned device token in localStorage fallback
      if (data.device_token) {
        try {
          localStorage.setItem('polllabs_device_token', data.device_token);
          localStorage.setItem(`polllabs_voted_${effectivePollId}`, optionId);
        } catch {}
      }

      if (poll) {
        localPoll = {
          ...poll,
          total_votes: data.total_votes,
          options: data.options,
        };
      }
    } catch (err: any) {
      errorMsg = err.message || 'Error recording vote. Please try again.';
      selectedOptionId = null;
    } finally {
      isSubmitting = false;
    }
  }

  async function submitAbuseReport() {
    if (!effectivePollId || !reportReason.trim() || reportSubmitting) return;

    reportSubmitting = true;
    reportFeedback = null;

    try {
      const res = await fetch(`${apiBase}/api/v1/polls/${effectivePollId}/report`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason: reportReason.trim() }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Failed to submit report');
      }

      reportFeedback = 'Report submitted. Our moderators will review this content.';
      reportReason = '';
      setTimeout(() => {
        showReportModal = false;
        reportFeedback = null;
      }, 2500);
    } catch (err: any) {
      reportFeedback = err.message || 'Failed to submit report.';
    } finally {
      reportSubmitting = false;
    }
  }

  $effect(() => {
    let targetId = pollId;
    if (!targetId) {
      const urlParams = new URLSearchParams(window.location.search);
      targetId = urlParams.get('id') || '';
      if (!targetId) {
        const parts = window.location.pathname.split('/').filter(Boolean);
        const last = parts[parts.length - 1];
        if (last && last !== 'embed') {
          targetId = last;
        }
      }
    }

    if (targetId) {
      loadPoll(targetId);
    } else if (!initialPoll) {
      isUnavailable = true;
    }
  });
</script>

{#snippet optionMedia(opt: PollOption, sizeClass: string)}
  {#if opt.icon_or_image}
    {#if opt.icon_or_image.startsWith('http') || opt.icon_or_image.startsWith('data:')}
      <img
        src={opt.icon_or_image}
        alt={opt.text}
        class="{sizeClass} rounded object-cover flex-shrink-0"
        loading="lazy"
      />
    {:else}
      <span class="text-base leading-none flex-shrink-0" aria-hidden="true">{opt.icon_or_image}</span>
    {/if}
  {/if}
{/snippet}

<div
  class="poll-widget-container font-sans text-gray-900 dark:text-gray-100 max-w-md w-full mx-auto p-4 rounded-2xl border border-gray-200/80 dark:border-gray-800 bg-white/95 dark:bg-gray-900/95 backdrop-blur-xs shadow-xs transition"
  data-theme={theme}
  data-layout={layout}
  data-radius={radius}
  data-font={font}
  data-effect={effect}
  style={customStyle}
>
  {#if loading}
    <div class="flex flex-col items-center justify-center py-8 space-y-3">
      <div class="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
      <p class="text-xs text-gray-400">Loading poll...</p>
    </div>
  {:else if isUnavailable}
    <!-- PRD §4.6: Graceful "This poll is no longer available" state -->
    <div class="py-8 text-center space-y-2">
      <div class="text-2xl" aria-hidden="true">🔒</div>
      <h3 class="font-semibold text-sm text-gray-800 dark:text-gray-200">
        This poll is no longer available
      </h3>
      <p class="text-xs text-gray-500 dark:text-gray-400 max-w-xs mx-auto">
        The poll may have been deleted by its owner or reached the end of its active window.
      </p>
      <a
        href="https://github.com/Luckyyaduvanshiofficial/polllabs"
        target="_blank"
        rel="noopener noreferrer"
        class="inline-block mt-3 text-xs text-blue-600 dark:text-blue-400 hover:underline font-medium"
      >
        Create your own poll with PollLabs →
      </a>
    </div>
  {:else if poll}
    <!-- Header -->
    <div class="pw-head mb-3.5">
      <div class="flex items-start justify-between gap-2">
        <h3 class="pw-title font-bold text-base leading-snug text-gray-900 dark:text-white">
          {poll.title}
        </h3>
        {#if isClosed}
          <span class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300">
            Closed
          </span>
        {/if}
      </div>
      {#if poll.description}
        <p class="mt-1 text-xs text-gray-600 dark:text-gray-400 line-clamp-2">
          {poll.description}
        </p>
      {/if}
    </div>

    <!-- Error banner if any -->
    {#if errorMsg}
      <div class="mb-3 px-3 py-2 rounded-lg bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900/50 text-xs text-red-600 dark:text-red-300 flex items-center justify-between">
        <span>{errorMsg}</span>
        <button onclick={() => { errorMsg = null; }} class="text-red-400 hover:text-red-600 font-bold ml-2">×</button>
      </div>
    {/if}

    <!-- Options List -->
    <div class="pw-options space-y-2.5">
      {#each poll.options as opt (opt.id)}
        {#if !hasVoted && !isClosed}
          <!-- Voting Button -->
          <button
            type="button"
            disabled={isSubmitting}
            onclick={() => submitVote(opt.id)}
            class="pw-vote-btn w-full group text-left px-3.5 py-2.5 rounded-xl border border-gray-200 dark:border-gray-800 hover:border-blue-500/80 dark:hover:border-blue-400 hover:bg-blue-50/40 dark:hover:bg-blue-950/30 text-sm font-medium transition duration-150 flex items-center gap-3 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {#if isGrid}
              {@render optionMedia(opt, "w-full h-20")}
              <span class="flex items-center justify-between gap-2 w-full">
                <span class="pw-label flex-1 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                  {opt.text}
                </span>
                <span class="pw-radio w-4 h-4 rounded-full border border-gray-300 dark:border-gray-600 group-hover:border-blue-500 flex items-center justify-center flex-shrink-0 transition-colors">
                  <span class="w-2 h-2 rounded-full bg-blue-500 opacity-0 group-hover:opacity-100 transition-opacity"></span>
                </span>
              </span>
            {:else}
              {@render optionMedia(opt, "w-6 h-6")}
              <span class="pw-label flex-1 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                {opt.text}
              </span>
              <span class="pw-radio w-4 h-4 rounded-full border border-gray-300 dark:border-gray-600 group-hover:border-blue-500 flex items-center justify-center flex-shrink-0 transition-colors">
                <span class="w-2 h-2 rounded-full bg-blue-500 opacity-0 group-hover:opacity-100 transition-opacity"></span>
              </span>
            {/if}
          </button>
        {:else}
          <!-- Results View -->
          {@const pct = opt.percentage ?? 0}
          <div class="pw-result relative overflow-hidden px-3.5 py-2.5 rounded-xl border border-gray-200 dark:border-gray-800 bg-gray-50/60 dark:bg-gray-800/40 text-sm">
            {#if isGrid}
              {@render optionMedia(opt, "w-full h-20 mb-2")}
            {/if}
            <!-- Animated Progress Bar -->
            {#if !isHiddenResults}
              <div
                class="pw-bar absolute inset-y-0 left-0 bg-blue-100/80 dark:bg-blue-900/40 transition-all duration-700 ease-out"
                style="width: {pct}%"
              ></div>
            {/if}

            <div class="relative z-10 flex justify-between items-center gap-3">
              <div class="flex items-center gap-2.5 min-w-0">
                {#if !isGrid}
                  {@render optionMedia(opt, "w-5 h-5")}
                {/if}
                <span class="pw-label truncate font-medium text-gray-900 dark:text-gray-100">
                  {opt.text}
                </span>
                {#if selectedOptionId === opt.id}
                  <span class="pw-check inline-flex items-center text-xs font-bold text-blue-600 dark:text-blue-400 ml-1" title="Your vote">
                    ✓
                  </span>
                {/if}
              </div>

              <!-- Result metric per PRD §3.2 -->
              <span class="text-xs font-semibold text-gray-600 dark:text-gray-300 flex-shrink-0">
                {#if isHiddenResults}
                  <span class="text-gray-400 text-[11px]">Hidden</span>
                {:else if poll.result_display === 'show_percentage'}
                  {pct}%
                {:else if poll.result_display === 'show_counts'}
                  {#if opt.vote_count !== null && opt.vote_count !== undefined}
                    {opt.vote_count} <span class="text-gray-400 font-normal">({pct}%)</span>
                  {:else}
                    {pct}%
                  {/if}
                {:else}
                  {pct}%
                {/if}
              </span>
            </div>
          </div>
        {/if}
      {/each}
    </div>

    <!-- Footer Meta -->
    <div class="pw-footer mt-4 pt-3 border-t border-gray-100 dark:border-gray-800/80 flex items-center justify-between text-[11px] text-gray-500 dark:text-gray-400">
      <div class="flex items-center gap-2">
        {#if poll.total_votes !== null && poll.total_votes !== undefined && !isHiddenResults}
          <span>{poll.total_votes} {poll.total_votes === 1 ? 'vote' : 'votes'}</span>
          <span>•</span>
        {/if}
        <button
          type="button"
          onclick={() => { showReportModal = true; }}
          class="hover:text-red-500 transition-colors underline-offset-2 hover:underline cursor-pointer"
        >
          Report abuse
        </button>
      </div>

      <a
        href="https://github.com/Luckyyaduvanshiofficial/polllabs"
        target="_blank"
        rel="noopener noreferrer"
        class="hover:text-blue-600 dark:hover:text-blue-400 transition-colors font-medium flex items-center gap-1"
      >
        <span>PollLabs</span>
      </a>
    </div>

    <!-- Abuse Reporting Modal -->
    {#if showReportModal}
      <div class="fixed inset-0 z-50 flex items-center justify-center p-3 bg-black/40 backdrop-blur-xs">
        <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-2xl p-4 max-w-xs w-full shadow-lg space-y-3">
          <div class="flex justify-between items-center">
            <h4 class="font-bold text-xs text-gray-900 dark:text-white">Report Inappropriate Content</h4>
            <button
              type="button"
              onclick={() => { showReportModal = false; reportFeedback = null; }}
              class="text-gray-400 hover:text-gray-600 text-sm font-bold"
            >
              ✕
            </button>
          </div>

          {#if reportFeedback}
            <p class="text-xs text-blue-600 dark:text-blue-400 py-2">{reportFeedback}</p>
          {:else}
            <p class="text-[11px] text-gray-500 dark:text-gray-400">
              Please describe why this poll violates safety or community guidelines.
            </p>
            <textarea
              bind:value={reportReason}
              placeholder="e.g. Spam, harassment, illegal content..."
              rows="3"
              class="w-full text-xs p-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-1 focus:ring-blue-500"
            ></textarea>
            <div class="flex justify-end gap-2 pt-1">
              <button
                type="button"
                onclick={() => { showReportModal = false; }}
                class="px-2.5 py-1 text-xs text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={reportSubmitting || reportReason.trim().length < 3}
                onclick={submitAbuseReport}
                class="px-3 py-1 text-xs font-semibold bg-red-600 hover:bg-red-700 text-white rounded-lg disabled:opacity-50 cursor-pointer"
              >
                {reportSubmitting ? 'Sending...' : 'Submit Report'}
              </button>
            </div>
          {/if}
        </div>
      </div>
    {/if}
  {/if}
</div>

<style>
  /* Phase 7 theme registry — var-driven presets + user overrides.
     Unlayered author CSS wins over Tailwind v4 layered utilities.
     `minimal` intentionally has no visual rules: Tailwind carries it. */
  .poll-widget-container {
    --pw-bg: #ffffff;
    --pw-ink: #111827;
    --pw-muted: #6b7280;
    --pw-line: #e5e7eb;
    --pw-accent: #3b82f6;
    --pw-accent-soft: #dbeafe;
  }

  /* Corner shapes (user override, wins over themes — declared last) */
  .poll-widget-container[data-radius='pill'] .pw-vote-btn,
  .poll-widget-container[data-radius='pill'] .pw-result {
    border-radius: 999px;
  }
  .poll-widget-container[data-radius='pill'] {
    border-radius: 1.5rem;
  }
  .poll-widget-container[data-radius='rounded'] .pw-vote-btn,
  .poll-widget-container[data-radius='rounded'] .pw-result {
    border-radius: 0.75rem;
  }
  .poll-widget-container[data-radius='rounded'] {
    border-radius: 1rem;
  }
  .poll-widget-container[data-radius='sharp'] .pw-vote-btn,
  .poll-widget-container[data-radius='sharp'] .pw-result,
  .poll-widget-container[data-radius='sharp'] {
    border-radius: 0.25rem;
  }

  /* Font stacks (system only — iframes can't rely on webfonts) */
  .poll-widget-container[data-font='serif'] {
    font-family: Georgia, 'Times New Roman', serif;
  }
  .poll-widget-container[data-font='mono'] {
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  }
  .poll-widget-container[data-font='condensed'] {
    font-family: 'Arial Narrow', 'Helvetica Neue', sans-serif;
  }

  /* Grid layout (youtube-grid default, or explicit layout:grid) */
  .poll-widget-container[data-layout='grid'] .pw-options {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 0.625rem;
  }
  .poll-widget-container[data-layout='grid'] .pw-options > * {
    margin-top: 0;
  }
  .poll-widget-container[data-layout='grid'] .pw-vote-btn {
    flex-direction: column;
    align-items: stretch;
  }

  /* Shared non-minimal consumption: card surface + text + dividers */
  .poll-widget-container[data-theme='whatsapp'],
  .poll-widget-container[data-theme='telegram'],
  .poll-widget-container[data-theme='story'],
  .poll-widget-container[data-theme='youtube-grid'] {
    background: var(--pw-bg);
    border-color: var(--pw-line);
    color: var(--pw-ink);
  }
  .poll-widget-container[data-theme='whatsapp'] .pw-title,
  .poll-widget-container[data-theme='telegram'] .pw-title,
  .poll-widget-container[data-theme='story'] .pw-title,
  .poll-widget-container[data-theme='youtube-grid'] .pw-title,
  .poll-widget-container[data-theme='whatsapp'] .pw-label,
  .poll-widget-container[data-theme='telegram'] .pw-label,
  .poll-widget-container[data-theme='story'] .pw-label,
  .poll-widget-container[data-theme='youtube-grid'] .pw-label {
    color: var(--pw-ink);
  }
  .poll-widget-container[data-theme='whatsapp'] .pw-footer,
  .poll-widget-container[data-theme='telegram'] .pw-footer,
  .poll-widget-container[data-theme='story'] .pw-footer,
  .poll-widget-container[data-theme='youtube-grid'] .pw-footer {
    border-color: var(--pw-line);
    color: var(--pw-muted);
  }
  .poll-widget-container[data-theme='whatsapp'] .pw-check,
  .poll-widget-container[data-theme='telegram'] .pw-check,
  .poll-widget-container[data-theme='story'] .pw-check,
  .poll-widget-container[data-theme='youtube-grid'] .pw-check {
    color: var(--pw-accent);
  }

  /* WhatsApp: chat bubble card, divider rows, teal bars */
  .poll-widget-container[data-theme='whatsapp'] {
    --pw-bg: #dcf8c6;
    --pw-ink: #111b21;
    --pw-muted: #667781;
    --pw-line: #bfe3b4;
    --pw-accent: #00a884;
    --pw-accent-soft: #c9ecd0;
    border-radius: 0.5rem;
  }
  .poll-widget-container[data-theme='whatsapp'] .pw-vote-btn,
  .poll-widget-container[data-theme='whatsapp'] .pw-result {
    background: transparent;
    border: none;
    border-bottom: 1px solid var(--pw-line);
    border-radius: 0;
  }
  .poll-widget-container[data-theme='whatsapp'] .pw-vote-btn:hover {
    background: var(--pw-accent-soft);
    border-color: var(--pw-accent-soft);
    border-bottom-color: var(--pw-accent);
  }
  .poll-widget-container[data-theme='whatsapp'] .pw-radio {
    border-color: var(--pw-muted);
  }
  .poll-widget-container[data-theme='whatsapp'] .pw-bar {
    background: var(--pw-accent);
  }
  @media (prefers-color-scheme: dark) {
    .poll-widget-container[data-theme='whatsapp'] {
      --pw-bg: #0b141a;
      --pw-ink: #e9edef;
      --pw-muted: #8696a0;
      --pw-line: #222d34;
      --pw-accent: #00a884;
      --pw-accent-soft: #0d3b33;
    }
  }

  /* Telegram: clean rows, classic blue bars */
  .poll-widget-container[data-theme='telegram'] {
    --pw-bg: #ffffff;
    --pw-ink: #000000;
    --pw-muted: #707579;
    --pw-line: #e6e6e6;
    --pw-accent: #3390ec;
    --pw-accent-soft: #d4e9f9;
  }
  .poll-widget-container[data-theme='telegram'] .pw-vote-btn,
  .poll-widget-container[data-theme='telegram'] .pw-result {
    background: transparent;
  }
  .poll-widget-container[data-theme='telegram'] .pw-vote-btn:hover {
    background: var(--pw-accent-soft);
    border-color: var(--pw-accent);
  }
  .poll-widget-container[data-theme='telegram'] .pw-bar {
    background: var(--pw-accent);
  }
  @media (prefers-color-scheme: dark) {
    .poll-widget-container[data-theme='telegram'] {
      --pw-bg: #17212b;
      --pw-ink: #ffffff;
      --pw-muted: #7f91a4;
      --pw-line: #232e3b;
      --pw-accent: #3390ec;
      --pw-accent-soft: #1e3a52;
    }
  }

  /* Story: navy question band + sticker pills */
  .poll-widget-container[data-theme='story'] {
    --pw-bg: #ffffff;
    --pw-ink: #0f172a;
    --pw-muted: #64748b;
    --pw-line: transparent;
    --pw-accent: #3b82f6;
    --pw-accent-soft: #e2e8f0;
    overflow: hidden;
  }
  .poll-widget-container[data-theme='story'] .pw-head {
    background: #1e293b;
    margin: -1rem -1rem 0.875rem;
    padding: 0.875rem 1rem;
  }
  .poll-widget-container[data-theme='story'] .pw-title {
    color: #ffffff;
    text-align: center;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    font-size: 0.95rem;
  }
  .poll-widget-container[data-theme='story'] .pw-vote-btn,
  .poll-widget-container[data-theme='story'] .pw-result {
    background: #f1f5f9;
    border-color: transparent;
    border-radius: 0.8rem;
  }
  .poll-widget-container[data-theme='story'] .pw-bar {
    background: var(--pw-accent);
  }
  @media (prefers-color-scheme: dark) {
    .poll-widget-container[data-theme='story'] {
      --pw-bg: #0f172a;
      --pw-ink: #f8fafc;
      --pw-muted: #94a3b8;
      --pw-accent: #60a5fa;
      --pw-accent-soft: #1e293b;
    }
    .poll-widget-container[data-theme='story'] .pw-head {
      background: #020617;
    }
    .poll-widget-container[data-theme='story'] .pw-vote-btn,
    .poll-widget-container[data-theme='story'] .pw-result {
      background: #1e293b;
    }
  }

  /* YouTube grid: tiles, strong ink, red accent */
  .poll-widget-container[data-theme='youtube-grid'] {
    --pw-bg: #ffffff;
    --pw-ink: #0f0f0f;
    --pw-muted: #606060;
    --pw-line: #e5e5e5;
    --pw-accent: #ff0033;
    --pw-accent-soft: #ffe5ea;
  }
  .poll-widget-container[data-theme='youtube-grid'] .pw-vote-btn:hover {
    border-color: var(--pw-accent);
  }
  .poll-widget-container[data-theme='youtube-grid'] .pw-bar {
    background: var(--pw-accent);
  }
  @media (prefers-color-scheme: dark) {
    .poll-widget-container[data-theme='youtube-grid'] {
      --pw-bg: #0f0f0f;
      --pw-ink: #f1f1f1;
      --pw-muted: #aaaaaa;
      --pw-line: #272727;
      --pw-accent: #ff4e45;
      --pw-accent-soft: #3d1a1d;
    }
  }

  /* Explicit user overrides win over every preset (inline style beats rules) */
  .poll-widget-container[style*='--pw-bg'] {
    background: var(--pw-bg);
  }
  .poll-widget-container[style*='--pw-ink'] .pw-title,
  .poll-widget-container[style*='--pw-ink'] .pw-label {
    color: var(--pw-ink);
  }
  .poll-widget-container[style*='--pw-accent'] .pw-bar {
    background: var(--pw-accent);
  }
  .poll-widget-container[style*='--pw-accent'] .pw-vote-btn:hover {
    border-color: var(--pw-accent);
  }
  .poll-widget-container[style*='--pw-accent'] .pw-check {
    color: var(--pw-accent);
  }

  @media (prefers-reduced-motion: reduce) {
    .poll-widget-container .pw-bar {
      transition: none;
    }
  }
</style>
