export interface DemoPollOption {
  id: string;
  text: string;
  icon_or_image?: string | null;
  vote_count?: number;
  percentage?: number;
}

export interface DemoPollAppearance {
  theme?: string;
  bg?: string;
  accent?: string;
  ink?: string;
  radius?: string;
  font?: string;
  effect?: string;
  layout?: string;
}

export interface DemoPoll {
  id: string;
  title: string;
  description?: string;
  visibility: 'public' | 'private';
  result_display: 'show_counts' | 'show_percentage' | 'hidden_until_close';
  owner: string;
  total_votes: number;
  options: DemoPollOption[];
  /** Optional per-poll appearance, used by the theme reference page. */
  appearance?: DemoPollAppearance;
}

export const DEMO_FRAMEWORKS_POLL: DemoPoll = {
  id: 'demo-frameworks',
  title: 'Which web framework is your team prioritizing in 2026?',
  description: 'Vote live below to test instant voting, result percentages, and embed generation.',
  visibility: 'public',
  result_display: 'show_counts',
  owner: 'polls-lab-team',
  total_votes: 1420,
  options: [
    { id: '1', text: 'Svelte 5 (Runes & Snippets)', icon_or_image: '🔥', vote_count: 654, percentage: 46.1 },
    { id: '2', text: 'React 19 (Server Actions)', icon_or_image: '⚛️', vote_count: 483, percentage: 34.0 },
    { id: '3', text: 'Astro (Islands Architecture)', icon_or_image: '🚀', vote_count: 283, percentage: 19.9 },
  ],
};
