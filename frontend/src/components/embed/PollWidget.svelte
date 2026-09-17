<script lang="ts">
  interface PollOption {
    id: string;
    text: string;
    icon_or_image?: string | null;
    vote_count?: number | null;
    percentage?: number | null;
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

  let localPoll = $state<PollData | null>(null);
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
    if (!targetId && typeof window !== 'undefined') {
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

    if (targetId && targetId !== 'demo') {
      loadPoll(targetId);
    } else if (!localPoll && !initialPoll) {
      // Demo poll fallback
      localPoll = {
        id: 'demo',
        title: 'Which tool or framework do you prefer?',
        description: 'Vote for your favorite technology stack for building modern APIs and embeds.',
        visibility: 'public',
        result_display: 'show_counts',
        owner: 'demo-user',
        total_votes: 89,
        options: [
          { id: '1', text: 'FastAPI (Python)', icon_or_image: '⚡', vote_count: 42, percentage: 47.2 },
          { id: '2', text: 'Svelte 5 (Frontend)', icon_or_image: '🔥', vote_count: 28, percentage: 31.5 },
          { id: '3', text: 'PocketBase (Database)', icon_or_image: '📦', vote_count: 19, percentage: 21.3 },
        ],
      };
    }
  });
</script>

<div class="poll-widget-container font-sans text-gray-900 dark:text-gray-100 max-w-md w-full mx-auto p-4 rounded-2xl border border-gray-200/80 dark:border-gray-800 bg-white/95 dark:bg-gray-900/95 backdrop-blur-xs shadow-xs transition">
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
    <div class="mb-3.5">
      <div class="flex items-start justify-between gap-2">
        <h3 class="font-bold text-base leading-snug text-gray-900 dark:text-white">
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
    <div class="space-y-2.5">
      {#each poll.options as opt (opt.id)}
        {#if !hasVoted && !isClosed}
          <!-- Voting Button -->
          <button
            type="button"
            disabled={isSubmitting}
            onclick={() => submitVote(opt.id)}
            class="w-full group text-left px-3.5 py-2.5 rounded-xl border border-gray-200 dark:border-gray-800 hover:border-blue-500/80 dark:hover:border-blue-400 hover:bg-blue-50/40 dark:hover:bg-blue-950/30 text-sm font-medium transition duration-150 flex items-center gap-3 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {#if opt.icon_or_image}
              {#if opt.icon_or_image.startsWith('http') || opt.icon_or_image.startsWith('data:')}
                <img
                  src={opt.icon_or_image}
                  alt={opt.text}
                  class="w-6 h-6 rounded object-cover flex-shrink-0"
                  loading="lazy"
                />
              {:else}
                <span class="text-base leading-none flex-shrink-0" aria-hidden="true">{opt.icon_or_image}</span>
              {/if}
            {/if}
            <span class="flex-1 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
              {opt.text}
            </span>
            <span class="w-4 h-4 rounded-full border border-gray-300 dark:border-gray-600 group-hover:border-blue-500 flex items-center justify-center flex-shrink-0 transition-colors">
              <span class="w-2 h-2 rounded-full bg-blue-500 opacity-0 group-hover:opacity-100 transition-opacity"></span>
            </span>
          </button>
        {:else}
          <!-- Results View -->
          {@const pct = opt.percentage ?? 0}
          <div class="relative overflow-hidden px-3.5 py-2.5 rounded-xl border border-gray-200 dark:border-gray-800 bg-gray-50/60 dark:bg-gray-800/40 text-sm">
            <!-- Animated Progress Bar -->
            {#if !isHiddenResults}
              <div
                class="absolute inset-y-0 left-0 bg-blue-100/80 dark:bg-blue-900/40 transition-all duration-700 ease-out"
                style="width: {pct}%"
              ></div>
            {/if}

            <div class="relative z-10 flex justify-between items-center gap-3">
              <div class="flex items-center gap-2.5 min-w-0">
                {#if opt.icon_or_image}
                  {#if opt.icon_or_image.startsWith('http') || opt.icon_or_image.startsWith('data:')}
                    <img
                      src={opt.icon_or_image}
                      alt={opt.text}
                      class="w-5 h-5 rounded object-cover flex-shrink-0"
                      loading="lazy"
                    />
                  {:else}
                    <span class="text-sm leading-none flex-shrink-0" aria-hidden="true">{opt.icon_or_image}</span>
                  {/if}
                {/if}
                <span class="truncate font-medium text-gray-900 dark:text-gray-100">
                  {opt.text}
                </span>
                {#if selectedOptionId === opt.id}
                  <span class="inline-flex items-center text-xs font-bold text-blue-600 dark:text-blue-400 ml-1" title="Your vote">
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
    <div class="mt-4 pt-3 border-t border-gray-100 dark:border-gray-800/80 flex items-center justify-between text-[11px] text-gray-500 dark:text-gray-400">
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
