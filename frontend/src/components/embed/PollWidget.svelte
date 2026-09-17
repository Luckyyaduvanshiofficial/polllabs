<script lang="ts">
  interface Option {
    id: string;
    text: string;
    votes: number;
  }

  export let pollId: string = '';
  export let title: string = 'Which tool do you prefer?';
  export let options: Option[] = [
    { id: '1', text: 'FastAPI', votes: 42 },
    { id: '2', text: 'Express', votes: 19 },
    { id: '3', text: 'Go Chi', votes: 28 },
  ];
  export let resultDisplay: 'show_counts' | 'show_percentage' | 'hidden_until_close' = 'show_counts';

  let hasVoted = false;
  let selectedOption: string | null = null;

  $: totalVotes = options.reduce((sum, opt) => sum + opt.votes, 0);

  function vote(optionId: string) {
    if (hasVoted) return;
    selectedOption = optionId;
    hasVoted = true;
    options = options.map((opt) =>
      opt.id === optionId ? { ...opt, votes: opt.votes + 1 } : opt
    );
  }
</script>

<div class="poll-widget p-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 font-sans max-w-md w-full shadow-xs">
  <h3 class="font-semibold text-base mb-3 text-gray-900 dark:text-gray-100">{title}</h3>

  <div class="space-y-2">
    {#each options as opt}
      {#if !hasVoted}
        <button
          class="w-full text-left p-2.5 rounded-lg border border-gray-200 dark:border-gray-700 hover:border-blue-500 hover:bg-blue-50/50 dark:hover:bg-blue-950/20 text-sm font-medium transition cursor-pointer"
          on:click={() => vote(opt.id)}
        >
          {opt.text}
        </button>
      {:else}
        {@const percentage = totalVotes > 0 ? Math.round((opt.votes / totalVotes) * 100) : 0}
        <div class="relative overflow-hidden p-2.5 rounded-lg border border-gray-200 dark:border-gray-700 text-sm">
          <div
            class="absolute top-0 bottom-0 left-0 bg-blue-100 dark:bg-blue-900/40 -z-0 transition-all duration-500"
            style="width: {percentage}%"
          ></div>
          <div class="relative z-10 flex justify-between items-center font-medium">
            <span>{opt.text} {selectedOption === opt.id ? '✓' : ''}</span>
            <span class="text-xs text-gray-500 dark:text-gray-400">
              {#if resultDisplay === 'show_percentage'}
                {percentage}%
              {:else if resultDisplay === 'show_counts'}
                {opt.votes} ({percentage}%)
              {:else}
                —
              {/if}
            </span>
          </div>
        </div>
      {/if}
    {/each}
  </div>

  <div class="mt-3 text-xs text-gray-400 flex justify-between items-center pt-2 border-t border-gray-100 dark:border-gray-700/50">
    <span>{totalVotes} total votes</span>
    <a href="https://github.com/Luckyyaduvanshiofficial/polllabs" target="_blank" class="hover:underline">
      Powered by PollLabs
    </a>
  </div>
</div>
