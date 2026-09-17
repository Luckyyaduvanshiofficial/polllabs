<script lang="ts">
  interface PollOption {
    id: string;
    text: string;
    icon_or_image?: string | null;
    vote_count?: number | null;
    percentage?: number | null;
    is_correct?: boolean | null;
    voters?: string[] | null;
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
    max_selections?: number | null;
    is_quiz?: boolean | null;
    show_voters?: boolean | null;
    appearance?: PollAppearance | null;
  }

  import { getApiUrl } from '../../lib/config';
  import { DEMO_FRAMEWORKS_POLL } from '../../lib/demo-poll';

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

  let apiBase = $derived(apiBaseUrl || getApiUrl());

  // Use $state.raw to eliminate deep proxy overhead for wholesale-reassigned API payloads (Svelte 5 best practices)
  let localPoll = $state.raw<PollData | null>(null);
  let poll = $derived(localPoll ?? initialPoll);

  let loading = $state<boolean>(false);
  let isUnavailable = $state<boolean>(false);
  let errorMsg = $state<string | null>(null);

  let hasVoted = $state<boolean>(false);
  let selectedOptionId = $state<string | null>(null);
  let selectedOptionIds = $state<string[]>([]);
  let submittedOptionIds = $state<string[] | null>(null);
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
  let isMultiSelect = $derived((poll?.max_selections ?? 1) > 1);
  let isQuiz = $derived(poll?.is_quiz === true);
  let showVoters = $derived(poll?.show_voters === true);

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
  // data-effect hook for Phase 6 confetti
  let effect = $derived(poll?.appearance?.effect === 'confetti' ? 'confetti' : 'none');

  // --- Phase 6: canvas confetti (hand-rolled, ~1.5KB) ---
  const CONFETTI_COLORS = ['#3b82f6', '#ef4444', '#f59e0b', '#10b981', '#8b5cf6', '#ec4899'];
  const CONFETTI_COUNT = 60;
  const CONFETTI_DURATION = 2000;

  function fireConfetti() {
    if (effect !== 'confetti') return;
    if (typeof window === 'undefined') return;
    if (window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) return;

    const container = document.querySelector('.poll-widget-container');
    if (!container) return;

    const rect = container.getBoundingClientRect();
    const canvas = document.createElement('canvas');
    canvas.width = rect.width;
    canvas.height = rect.height;
    canvas.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;pointer-events:none;z-index:100';
    container.style.position = 'relative';
    container.appendChild(canvas);

    const ctx = canvas.getContext('2d');
    if (!ctx) { canvas.remove(); return; }

    const particles: {
      x: number; y: number;
      vx: number; vy: number;
      w: number; h: number;
      rot: number; rv: number;
      color: string; life: number;
    }[] = [];

    for (let i = 0; i < CONFETTI_COUNT; i++) {
      particles.push({
        x: rect.width * 0.3 + Math.random() * rect.width * 0.4,
        y: rect.height * 0.3 + Math.random() * rect.height * 0.2,
        vx: (Math.random() - 0.5) * 8,
        vy: -(Math.random() * 6 + 2),
        w: Math.random() * 8 + 4,
        h: Math.random() * 4 + 2,
        rot: Math.random() * Math.PI * 2,
        rv: (Math.random() - 0.5) * 0.3,
        color: CONFETTI_COLORS[Math.floor(Math.random() * CONFETTI_COLORS.length)],
        life: 1,
      });
    }

    const start = performance.now();
    let raf: number;

    function tick(now: number) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / CONFETTI_DURATION, 1);
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      for (const p of particles) {
        p.x += p.vx;
        p.y += p.vy;
        p.vy += 0.15;
        p.rot += p.rv;
        p.life = 1 - progress;

        ctx.save();
        ctx.translate(p.x, p.y);
        ctx.rotate(p.rot);
        ctx.globalAlpha = p.life;
        ctx.fillStyle = p.color;
        ctx.fillRect(-p.w / 2, -p.h / 2, p.w, p.h);
        ctx.restore();
      }

      if (progress < 1) {
        raf = requestAnimationFrame(tick);
      } else {
        canvas.remove();
      }
    }

    raf = requestAnimationFrame(tick);
    // Cleanup on unmount or navigation
    const cleanup = () => { cancelAnimationFrame(raf); canvas.remove(); };
    window.addEventListener('beforeunload', cleanup, { once: true });
  }

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
        if (id === 'demo-frameworks' || id === 'demo') {
          localPoll = DEMO_FRAMEWORKS_POLL;
          return;
        }
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
        const storedVote = localStorage.getItem(`polls-lab_voted_${id}`);
        if (storedVote) {
          hasVoted = true;
          if (storedVote.includes(',')) {
            submittedOptionIds = storedVote.split(',');
          } else {
            selectedOptionId = storedVote;
            submittedOptionIds = [storedVote];
          }
        }
      } catch {}
    } catch (err: any) {
      if (id === 'demo-frameworks' || id === 'demo') {
        localPoll = DEMO_FRAMEWORKS_POLL;
      } else {
        errorMsg = err.message || 'Unable to connect to poll service.';
        isUnavailable = true;
      }
    } finally {
      loading = false;
    }
  }

  function toggleOption(optionId: string) {
    if (hasVoted || isSubmitting || isClosed) return;
    if (!isMultiSelect) {
      selectedOptionId = optionId;
      submitVote(optionId);
      return;
    }
    const idx = selectedOptionIds.indexOf(optionId);
    if (idx >= 0) {
      selectedOptionIds = selectedOptionIds.filter(id => id !== optionId);
    } else {
      const max = poll?.max_selections ?? 3;
      if (selectedOptionIds.length < max) {
        selectedOptionIds = [...selectedOptionIds, optionId];
      }
    }
  }

  async function submitVote(optionId: string | string[]) {
    if (hasVoted || isSubmitting || !effectivePollId || isClosed) return;

    isSubmitting = true;
    errorMsg = null;

    const payload = Array.isArray(optionId) ? optionId : optionId;
    if (Array.isArray(payload)) {
      submittedOptionIds = payload;
    } else {
      selectedOptionId = payload;
    }

    let deviceToken: string | null = null;
    try {
      deviceToken = localStorage.getItem('polls-lab_device_token');
    } catch {}

    try {
      const res = await fetch(`${apiBase}/api/v1/votes/${effectivePollId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(deviceToken ? { 'x-device-token': deviceToken } : {}),
        },
        body: JSON.stringify({
          option_id: payload,
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

      // Update local voted state for multi-select
      if (data.selected_options) {
        submittedOptionIds = data.selected_options;
      }

      if (data.device_token) {
        try {
          localStorage.setItem('polls-lab_device_token', data.device_token);
          const voteKey = Array.isArray(payload) ? payload.join(',') : payload;
          localStorage.setItem(`polls-lab_voted_${effectivePollId}`, voteKey);
        } catch {}
      }

      if (poll) {
        localPoll = {
          ...poll,
          total_votes: data.total_votes,
          options: data.options,
        };
      }

      // Phase 6: fire confetti on success
      if (effect === 'confetti') {
        // Run on next tick so DOM updates to results view first
        requestAnimationFrame(() => fireConfetti());
      }
    } catch (err: any) {
      errorMsg = err.message || 'Error recording vote. Please try again.';
      selectedOptionId = null;
      selectedOptionIds = [];
      submittedOptionIds = null;
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
        href="https://github.com/Luckyyaduvanshiofficial/polls-lab"
        target="_blank"
        rel="noopener noreferrer"
        class="inline-block mt-3 text-xs text-blue-600 dark:text-blue-400 hover:underline font-medium"
      >
        Create your own poll with Polls Lab →
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
          {@const isSelected = isMultiSelect
            ? selectedOptionIds.includes(opt.id)
            : selectedOptionId === opt.id}
          <button
            type="button"
            disabled={isSubmitting}
            onclick={() => toggleOption(opt.id)}
            class="pw-vote-btn w-full group text-left px-3.5 py-2.5 rounded-xl border border-gray-200 dark:border-gray-800 hover:border-blue-500/80 dark:hover:border-blue-400 hover:bg-blue-50/40 dark:hover:bg-blue-950/30 text-sm font-medium transition duration-150 flex items-center gap-3 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
            class:selected={isSelected}
          >
            {#if isGrid}
              {@render optionMedia(opt, "w-full h-20")}
              <span class="flex items-center justify-between gap-2 w-full">
                <span class="pw-label flex-1 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                  {opt.text}
                </span>
                {#if isMultiSelect}
                  <span class="pw-checkbox w-4 h-4 rounded border border-gray-300 dark:border-gray-600 group-hover:border-blue-500 flex items-center justify-center flex-shrink-0 transition-colors"
                        class:checked={isSelected}>
                    {#if isSelected}<span class="text-[10px] text-white font-bold leading-none">✓</span>{/if}
                  </span>
                {:else}
                  <span class="pw-radio w-4 h-4 rounded-full border border-gray-300 dark:border-gray-600 group-hover:border-blue-500 flex items-center justify-center flex-shrink-0 transition-colors">
                    <span class="w-2 h-2 rounded-full bg-blue-500 opacity-0 group-hover:opacity-100 transition-opacity"></span>
                  </span>
                {/if}
              </span>
            {:else}
              {@render optionMedia(opt, "w-6 h-6")}
              <span class="pw-label flex-1 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                {opt.text}
              </span>
              {#if isMultiSelect}
                <span class="pw-checkbox w-4 h-4 rounded border border-gray-300 dark:border-gray-600 group-hover:border-blue-500 flex items-center justify-center flex-shrink-0 transition-colors"
                      class:checked={isSelected}>
                  {#if isSelected}<span class="text-[10px] text-white font-bold leading-none">✓</span>{/if}
                </span>
              {:else}
                <span class="pw-radio w-4 h-4 rounded-full border border-gray-300 dark:border-gray-600 group-hover:border-blue-500 flex items-center justify-center flex-shrink-0 transition-colors">
                  <span class="w-2 h-2 rounded-full bg-blue-500 opacity-0 group-hover:opacity-100 transition-opacity"></span>
                </span>
              {/if}
            {/if}
          </button>
        {:else}
          <!-- Results View -->
          {@const pct = opt.percentage ?? 0}
          {@const isMyVote = isMultiSelect
            ? (submittedOptionIds ?? []).includes(opt.id)
            : selectedOptionId === opt.id}
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
                <!-- Quiz mode: correct / incorrect indicator -->
                {#if isQuiz && hasVoted && !isHiddenResults && opt.is_correct !== undefined && opt.is_correct !== null}
                  {#if opt.is_correct}
                    <span class="pw-quiz-badge pw-quiz-correct inline-flex items-center text-xs font-bold ml-1" title="Correct answer">✓</span>
                  {:else if isMyVote}
                    <span class="pw-quiz-badge pw-quiz-wrong inline-flex items-center text-xs font-bold ml-1" title="Your answer was incorrect">✕</span>
                  {/if}
                {/if}
                {#if isMyVote}
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

            <!-- Voter badges -->
            {#if showVoters && !isHiddenResults && opt.voters && opt.voters.length > 0}
              <div class="pw-voters relative z-10 mt-1.5 flex flex-wrap gap-1">
                {#each opt.voters as voter}
                  <span class="inline-flex items-center px-1.5 py-0.5 rounded-full text-[9px] font-medium bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400">
                    {voter}
                  </span>
                {/each}
              </div>
            {/if}
          </div>
        {/if}
      {/each}
    </div>

    <!-- Multi-select submit button -->
    {#if !hasVoted && !isClosed && isMultiSelect}
      <button
        type="button"
        disabled={selectedOptionIds.length === 0 || isSubmitting}
        onclick={() => submitVote(selectedOptionIds)}
        class="pw-submit-btn mt-3 w-full py-2.5 rounded-xl text-sm font-semibold transition duration-150 cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed bg-blue-600 hover:bg-blue-700 text-white dark:bg-blue-500 dark:hover:bg-blue-600"
      >
        {#if isSubmitting}
          Submitting...
        {:else}
          Submit ({selectedOptionIds.length}/{poll?.max_selections ?? 3})
        {/if}
      </button>
    {/if}

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
        href="https://github.com/Luckyyaduvanshiofficial/polls-lab"
        target="_blank"
        rel="noopener noreferrer"
        class="hover:text-blue-600 dark:hover:text-blue-400 transition-colors font-medium flex items-center gap-1"
      >
        <span>Polls Lab</span>
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

  /* Phase 5: multi-select checkbox */
  .pw-checkbox {
    transition: background-color 0.15s, border-color 0.15s;
  }
  .pw-checkbox.checked {
    background-color: var(--pw-accent, #3b82f6);
    border-color: var(--pw-accent, #3b82f6);
  }

  /* Phase 5: selected vote button highlight */
  .pw-vote-btn.selected {
    border-color: var(--pw-accent, #3b82f6);
    background-color: var(--pw-accent-soft, #dbeafe);
  }
  .pw-vote-btn.selected .pw-checkbox {
    background-color: var(--pw-accent, #3b82f6);
    border-color: var(--pw-accent, #3b82f6);
  }
  .pw-vote-btn.selected .pw-radio {
    border-color: var(--pw-accent, #3b82f6);
  }
  .pw-vote-btn.selected .pw-radio > span {
    opacity: 1;
    background-color: var(--pw-accent, #3b82f6);
  }

  /* Phase 5: submit button */
  .pw-submit-btn {
    background-color: var(--pw-accent, #3b82f6);
  }
  .pw-submit-btn:hover:not(:disabled) {
    filter: brightness(0.9);
  }

  /* Phase 5: quiz badges */
  .pw-quiz-correct {
    color: #16a34a;
  }
  .pw-quiz-wrong {
    color: #dc2626;
  }

  /* Phase 5: voter badges row */
  .pw-voters {
    border-top: 1px solid var(--pw-line, #e5e7eb);
    padding-top: 0.375rem;
  }
</style>
