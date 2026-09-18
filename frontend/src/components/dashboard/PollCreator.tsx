import React, { useEffect, useState, useTransition } from 'react';
import { getSiteUrl } from '../../lib/config';
import { getMarkdownBadgeSnippet, getIframeSnippet, copyToClipboard } from '../../lib/embed';
import { createPoll, uploadPollImage } from '../../lib/api';
import { isSignedIn, startSignIn } from '../../lib/auth';

interface PollOptionItem {
  id: string;
  text: string;
  icon_or_image: string;
}

type ThemeId = 'minimal' | 'whatsapp' | 'telegram' | 'story' | 'youtube-grid';
type RadiusId = 'pill' | 'rounded' | 'sharp';
type AppearanceFont = 'system' | 'serif' | 'mono' | 'condensed';

interface ThemePreset {
  id: ThemeId;
  name: string;
  blurb: string;
  swatches: [string, string, string];
  layout: 'list' | 'grid';
}

const THEME_PRESETS: ThemePreset[] = [
  { id: 'minimal', name: 'Minimal', blurb: 'Clean default', swatches: ['#ffffff', '#b47a0a', '#1a1612'], layout: 'list' },
  { id: 'whatsapp', name: 'WhatsApp', blurb: 'Chat bubble', swatches: ['#dcf8c6', '#00a884', '#111b21'], layout: 'list' },
  { id: 'telegram', name: 'Telegram', blurb: 'Classic blue', swatches: ['#ffffff', '#3390ec', '#000000'], layout: 'list' },
  { id: 'story', name: 'Story', blurb: 'Sticker card', swatches: ['#ffffff', '#b47a0a', '#1a1612'], layout: 'list' },
  { id: 'youtube-grid', name: 'Thumbnail grid', blurb: 'Image tiles', swatches: ['#ffffff', '#ff0033', '#0f0f0f'], layout: 'grid' },
];

const RADIUS_PX: Record<RadiusId, string> = { pill: '999px', rounded: '12px', sharp: '4px' };
const FONT_STACK: Record<AppearanceFont, string> = {
  system: 'inherit',
  serif: 'Georgia, serif',
  mono: 'ui-monospace, monospace',
  condensed: "'Arial Narrow', sans-serif",
};

function isHexColor(value: string): boolean {
  return value === '' || /^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/.test(value);
}

export default function PollCreator() {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [options, setOptions] = useState<PollOptionItem[]>([
    { id: '1', text: 'Option 1', icon_or_image: '' },
    { id: '2', text: 'Option 2', icon_or_image: '' },
  ]);
  const [visibility, setVisibility] = useState<'public' | 'private'>('public');
  const [resultDisplay, setResultDisplay] = useState<'show_counts' | 'show_percentage' | 'hidden_until_close'>('show_counts');
  const [closeAt, setCloseAt] = useState('');

  // Phase 7 appearance
  const [theme, setTheme] = useState<ThemeId>('minimal');
  const [bg, setBg] = useState('');
  const [accent, setAccent] = useState('');
  const [ink, setInk] = useState('');
  const [radius, setRadius] = useState<RadiusId>('rounded');
  const [appearanceFont, setAppearanceFont] = useState<AppearanceFont>('system');
  const [effect, setEffect] = useState<'none' | 'confetti'>('none');
  const [layout, setLayout] = useState<'list' | 'grid'>('list');

  // Phase 5: behaviors
  const [maxSelections, setMaxSelections] = useState(1);
  const [isQuiz, setIsQuiz] = useState(false);
  const [correctOptions, setCorrectOptions] = useState<string[]>([]);
  const [showVoters, setShowVoters] = useState(false);

  const preset = THEME_PRESETS.find((p) => p.id === theme) ?? THEME_PRESETS[0];

  const handleThemeSelect = (id: ThemeId) => {
    setTheme(id);
    const next = THEME_PRESETS.find((p) => p.id === id);
    if (next) setLayout(next.layout);
  };

  const buildAppearance = () => {
    const appearance: Record<string, string> = {
      theme,
      radius,
      font: appearanceFont,
      effect,
      layout,
    };
    if (bg.trim()) appearance.bg = bg.trim().toLowerCase();
    if (accent.trim()) appearance.accent = accent.trim().toLowerCase();
    if (ink.trim()) appearance.ink = ink.trim().toLowerCase();
    return appearance;
  };

  const toggleCorrectOption = (optId: string) => {
    setCorrectOptions((prev) =>
      prev.includes(optId) ? prev.filter((id) => id !== optId) : [...prev, optId],
    );
  };

  const [isPending, startTransition] = useTransition();
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [createdPoll, setCreatedPoll] = useState<{ id: string; title: string } | null>(null);
  const [copiedType, setCopiedType] = useState<string | null>(null);
  const [uploadingIdx, setUploadingIdx] = useState<number | null>(null);

  // Options Manipulation
  const handleAddOption = () => {
    if (options.length < 10) {
      setOptions((prev) => [
        ...prev,
        { id: String(Date.now()), text: '', icon_or_image: '' },
      ]);
    }
  };

  const handleRemoveOption = (index: number) => {
    if (options.length > 2) {
      setOptions((prev) => prev.filter((_, i) => i !== index));
    }
  };

  const handleOptionChange = (index: number, field: 'text' | 'icon_or_image', val: string) => {
    setOptions((prev) => {
      const copy = [...prev];
      copy[index] = { ...copy[index], [field]: val };
      return copy;
    });
  };

  // Phase 4: thumbnail upload (staged without poll_id until publish)
  const handleImageUpload = async (index: number, file: File) => {
    setUploadingIdx(index);
    setErrorMessage(null);
    try {
      const result = await uploadPollImage(file);
      if (!result.ok) {
        throw new Error(result.error);
      }
      handleOptionChange(index, 'icon_or_image', result.data.url);
    } catch (err: any) {
      setErrorMessage(err.message || 'Image upload failed. Use JPEG, PNG, GIF or WebP under 2MB.');
    } finally {
      setUploadingIdx(null);
    }
  };

  // Form Submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    const validOptions = options.map((opt) => ({
      text: opt.text.trim(),
      icon_or_image: opt.icon_or_image.trim() || undefined,
    })).filter((opt) => opt.text.length > 0);

    if (validOptions.length < 2) {
      setErrorMessage('Please provide at least 2 non-empty options.');
      return;
    }

    if (!isHexColor(bg.trim()) || !isHexColor(accent.trim()) || !isHexColor(ink.trim())) {
      setErrorMessage('Custom colors must be hex like #fff or #00a884 (or left empty).');
      return;
    }

    startTransition(async () => {
      try {
        const result = await createPoll({
            title: title.trim(),
            description: description.trim() || undefined,
            options: validOptions,
            visibility,
            result_display: resultDisplay,
            close_at: closeAt ? new Date(closeAt).toISOString() : undefined,
            max_selections: maxSelections,
            is_quiz: isQuiz || undefined,
            correct_options: isQuiz && correctOptions.length > 0 ? correctOptions : undefined,
            show_voters: showVoters || undefined,
            appearance: buildAppearance(),
        });

        if (!result.ok) {
          throw new Error(result.error);
        }

        setCreatedPoll({ id: result.data.id, title: result.data.title });
      } catch (err: any) {
        setErrorMessage(err.message || 'Failed to publish poll. Please try again.');
      }
    });
  };

  const copySnippet = async (text: string, type: string) => {
    const success = await copyToClipboard(text);
    if (success) {
      setCopiedType(type);
      setTimeout(() => setCopiedType(null), 2000);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
      {/* Left: Creator Form */}
      <div className="lg:col-span-7 bg-paper-2 border border-rule rounded-2xl p-6 sm:p-8 shadow-xl space-y-6">
        <div>
          <span className="text-xs font-mono text-accent uppercase tracking-wider">Studio</span>
          <h2 className="text-2xl font-bold text-ink mt-1">Configure Your Poll</h2>
          <p className="text-xs text-ink-3 mt-1">
            Build single-choice polls with live preview and instant embed generation.
          </p>
        </div>

        {errorMessage && (
          <div className="p-3.5 rounded-lg bg-danger-soft border border-danger text-danger text-xs flex items-center justify-between">
            <span>{errorMessage}</span>
            <button
              type="button"
              onClick={() => setErrorMessage(null)}
              className="text-danger hover:text-danger ml-2 font-bold"
            >
              ✕
            </button>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Question / Title */}
          <div>
            <div className="flex justify-between items-center mb-1.5">
              <label htmlFor="poll-title" className="text-xs font-medium text-ink">
                Poll Question / Headline <span className="text-rose-400">*</span>
              </label>
              <span className="text-[11px] font-mono text-ink-4">
                {title.length}/150
              </span>
            </div>
            <input
              id="poll-title"
              type="text"
              required
              maxLength={150}
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Which web framework is your team adopting in 2026?"
              className="w-full px-3.5 py-2.5 bg-paper-inset border border-rule focus:border-accent rounded-xl text-sm text-ink placeholder-[#64748b] focus:outline-hidden transition"
            />
          </div>

          {/* Description (Optional) */}
          <div>
            <label htmlFor="poll-description" className="block text-xs font-medium text-ink mb-1.5">
              Context or Description <span className="text-ink-4 font-normal">(optional)</span>
            </label>
            <textarea
              id="poll-description"
              rows={2}
              maxLength={500}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Provide background context or guidelines for voters..."
              className="w-full px-3.5 py-2.5 bg-paper-inset border border-rule focus:border-accent rounded-xl text-sm text-ink placeholder-[#64748b] focus:outline-hidden transition resize-none"
            />
          </div>

          {/* Options List */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-xs font-medium text-ink">
                Poll Options <span className="text-rose-400">*</span> (min 2, max 10)
              </label>
              <span className="text-[11px] font-mono text-ink-4">
                {options.length}/10 options
              </span>
            </div>

            <div className="space-y-2.5">
              {options.map((opt, idx) => (
                <div key={opt.id} className="flex gap-2 items-center">
                  <span className="w-6 h-6 rounded-md bg-paper-inset border border-rule text-ink-3 font-mono text-xs flex items-center justify-center flex-shrink-0">
                    {idx + 1}
                  </span>
                  {/* Emoji, Image URL, or Upload */}
                  <input
                    type="text"
                    placeholder="Emoji or Icon URL"
                    value={opt.icon_or_image}
                    onChange={(e) => handleOptionChange(idx, 'icon_or_image', e.target.value)}
                    className="w-28 px-2.5 py-2 bg-paper-inset border border-rule rounded-lg text-xs text-ink placeholder-[#64748b] focus:border-accent focus:outline-hidden transition flex-shrink-0"
                    title="Enter single emoji (e.g. ⚡), image URL (https://...), or upload a thumbnail"
                  />
                  <label
                    className="p-2 text-ink-4 hover:text-accent hover:bg-blue-950/20 rounded-lg transition cursor-pointer flex-shrink-0"
                    title="Upload thumbnail image (JPEG/PNG/GIF/WebP, max 2MB)"
                  >
                    {uploadingIdx === idx ? '…' : '🖼'}
                    <input
                      type="file"
                      accept="image/jpeg,image/png,image/gif,image/webp"
                      className="hidden"
                      onChange={(e) => {
                        const f = e.target.files?.[0];
                        if (f) handleImageUpload(idx, f);
                        e.target.value = '';
                      }}
                    />
                  </label>
                  {/* Option Text */}
                  <input
                    type="text"
                    required
                    placeholder={`Option ${idx + 1} text`}
                    value={opt.text}
                    onChange={(e) => handleOptionChange(idx, 'text', e.target.value)}
                    className="flex-1 px-3 py-2 bg-paper-inset border border-rule rounded-lg text-xs text-ink placeholder-[#64748b] focus:border-accent focus:outline-hidden transition"
                  />
                  {/* Remove Button */}
                  {options.length > 2 && (
                    <button
                      type="button"
                      onClick={() => handleRemoveOption(idx)}
                      className="p-2 text-ink-4 hover:text-rose-400 hover:bg-rose-950/20 rounded-lg transition"
                      title="Remove option"
                    >
                      ✕
                    </button>
                  )}
                </div>
              ))}
            </div>

            {options.length < 10 && (
              <button
                type="button"
                onClick={handleAddOption}
                className="btn-interactive text-xs font-semibold text-accent hover:text-accent flex items-center gap-1 mt-2"
              >
                <span>+ Add another option</span>
              </button>
            )}
          </div>

          {/* Settings Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-4 border-t border-rule">
            <div>
              <label htmlFor="poll-visibility" className="block text-xs font-medium text-ink mb-1.5">
                Visibility
              </label>
              <select
                id="poll-visibility"
                value={visibility}
                onChange={(e) => setVisibility(e.target.value as any)}
                className="w-full px-3 py-2 bg-paper-inset border border-rule rounded-xl text-xs text-ink focus:border-accent focus:outline-hidden"
              >
                <option value="public">Public (Discoverable & on Leaderboards)</option>
                <option value="private">Private (Unlisted, direct link & embed only)</option>
              </select>
              <p className="text-[10px] text-ink-4 mt-1">
                {visibility === 'public'
                  ? 'Eligible for trending and community leaderboards.'
                  : 'Hidden from search and feeds; accessible only where embedded.'}
              </p>
            </div>

            <div>
              <label htmlFor="poll-results" className="block text-xs font-medium text-ink mb-1.5">
                Result Display
              </label>
              <select
                id="poll-results"
                value={resultDisplay}
                onChange={(e) => setResultDisplay(e.target.value as any)}
                className="w-full px-3 py-2 bg-paper-inset border border-rule rounded-xl text-xs text-ink focus:border-accent focus:outline-hidden"
              >
                <option value="show_counts">Show raw counts & percentages</option>
                <option value="show_percentage">Show percentages only (counts masked)</option>
                <option value="hidden_until_close">Hidden until poll deadline closes</option>
              </select>
              <p className="text-[10px] text-ink-4 mt-1">
                {resultDisplay === 'show_counts'
                  ? 'Voters see full vote numbers and percentages.'
                  : resultDisplay === 'show_percentage'
                  ? 'Voters only see percentage shares, preventing bias.'
                  : 'Results remain secret until poll close date.'}
              </p>
            </div>
          </div>

          {/* Phase 5: Behavior toggles */}
          <div className="pt-4 border-t border-rule space-y-4">
            <div>
              <span className="text-xs font-medium text-ink">Poll Behaviors</span>
              <p className="text-[10px] text-ink-4 mt-0.5">
                Control how voters interact with this poll.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {/* Multi-select */}
              <div>
                <label className="block text-[11px] font-medium text-ink mb-1.5">
                  Max selections
                </label>
                <select
                  value={maxSelections}
                  onChange={(e) => {
                    const val = Number(e.target.value);
                    setMaxSelections(val);
                    if (val === 1) setCorrectOptions([]);
                  }}
                  className="w-full px-2.5 py-2 bg-paper-inset border border-rule rounded-lg text-xs text-ink focus:border-accent focus:outline-hidden"
                >
                  <option value={1}>Single choice</option>
                  <option value={2}>Up to 2</option>
                  <option value={3}>Up to 3</option>
                  <option value={4}>Up to 4</option>
                  <option value={5}>Up to 5</option>
                </select>
                <p className="text-[10px] text-ink-4 mt-1">
                  {maxSelections === 1
                    ? 'Each voter picks exactly one option.'
                    : `Each voter can pick up to ${maxSelections} options.`}
                </p>
              </div>

              {/* Quiz mode */}
              <div>
                <span className="block text-[11px] font-medium text-ink mb-1.5">Quiz mode</span>
                <button
                  type="button"
                  onClick={() => { setIsQuiz(!isQuiz); if (isQuiz) setCorrectOptions([]); }}
                  aria-pressed={isQuiz}
                  className={`w-full px-2.5 py-2 rounded-lg text-xs font-medium border transition ${
                    isQuiz
                      ? 'bg-accent border-accent text-accent-ink'
                      : 'bg-paper-inset border-rule text-ink-3 hover:text-ink'
                  }`}
                >
                  {isQuiz ? 'Quiz on' : 'Quiz off'}
                </button>
                <p className="text-[10px] text-ink-4 mt-1">
                  Reveal correct answers immediately after voting.
                </p>
              </div>

              {/* Show voters */}
              <div>
                <span className="block text-[11px] font-medium text-ink mb-1.5">Visible voters</span>
                <button
                  type="button"
                  onClick={() => setShowVoters(!showVoters)}
                  aria-pressed={showVoters}
                  className={`w-full px-2.5 py-2 rounded-lg text-xs font-medium border transition ${
                    showVoters
                      ? 'bg-accent border-accent text-accent-ink'
                      : 'bg-paper-inset border-rule text-ink-3 hover:text-ink'
                  }`}
                >
                  {showVoters ? 'Voters visible' : 'Voters hidden'}
                </button>
                <p className="text-[10px] text-ink-4 mt-1">
                  Show anonymized voter IDs next to each option.
                </p>
              </div>
            </div>

            {/* Quiz: mark correct answers */}
            {isQuiz && (
              <div className="p-3 rounded-lg bg-accent-soft border border-accent space-y-2">
                <span className="text-[11px] font-medium text-accent">
                  Mark the correct answer{maxSelections > 1 ? 's' : ''}
                </span>
                <div className="space-y-1.5">
                  {options.map((opt, idx) => (
                    <label
                      key={opt.id}
                      className="flex items-center gap-2 px-2.5 py-1.5 rounded-md bg-paper-inset border border-rule hover:border-accent cursor-pointer transition text-xs"
                    >
                      <input
                        type="checkbox"
                        checked={correctOptions.includes(opt.id)}
                        onChange={() => toggleCorrectOption(opt.id)}
                        className="w-3.5 h-3.5 rounded border-rule-strong bg-paper-inset text-accent focus:ring-accent focus:ring-offset-0 cursor-pointer"
                      />
                      <span className="text-ink flex-1 truncate">
                        {opt.text || `Option ${idx + 1}`}
                      </span>
                    </label>
                  ))}
                </div>
                <p className="text-[10px] text-accent">
                  Voters will see ✓/✕ immediately after voting.
                </p>
              </div>
            )}
          </div>

          {/* Appearance: theme presets + customizer */}
          <div className="pt-4 border-t border-rule space-y-4">
            <div>
              <span className="text-xs font-medium text-ink">Poll Theme</span>
              <p className="text-[10px] text-ink-4 mt-0.5">
                Presets restyle the embed widget. Custom colors below override the preset.
              </p>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
              {THEME_PRESETS.map((p) => (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => handleThemeSelect(p.id)}
                  aria-pressed={theme === p.id}
                  className={`rounded-xl border p-2.5 text-left transition ${
                    theme === p.id
                      ? 'border-accent bg-accent-soft'
                      : 'border-rule bg-paper-inset hover:border-rule-strong'
                  }`}
                >
                  <span className="flex gap-1 mb-1.5">
                    {p.swatches.map((c) => (
                      <span
                        key={c}
                        className="w-4 h-4 rounded-full border border-black/30"
                        style={{ background: c }}
                      />
                    ))}
                  </span>
                  <span className="block text-xs font-semibold text-ink">{p.name}</span>
                  <span className="block text-[10px] text-ink-4">{p.blurb}</span>
                </button>
              ))}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {[
                { label: 'Background', value: bg, set: setBg, fallback: preset.swatches[0] },
                { label: 'Accent', value: accent, set: setAccent, fallback: preset.swatches[1] },
                { label: 'Text ink', value: ink, set: setInk, fallback: preset.swatches[2] },
              ].map((f) => (
                <div key={f.label}>
                  <label className="block text-[11px] font-medium text-ink mb-1.5">
                    {f.label} <span className="text-ink-4 font-normal">(optional)</span>
                  </label>
                  <div className="flex gap-2 items-center">
                    <input
                      type="color"
                      value={isHexColor(f.value) && f.value ? f.value : f.fallback}
                      onChange={(e) => f.set(e.target.value)}
                      className="w-9 h-9 rounded-lg bg-transparent cursor-pointer flex-shrink-0"
                      title={`Pick ${f.label.toLowerCase()} color`}
                    />
                    <input
                      type="text"
                      value={f.value}
                      onChange={(e) => f.set(e.target.value)}
                      placeholder={f.fallback}
                      maxLength={7}
                      className="flex-1 min-w-0 px-2.5 py-2 bg-paper-inset border border-rule rounded-lg text-xs font-mono text-ink placeholder-[#64748b] focus:border-accent focus:outline-hidden transition"
                    />
                  </div>
                </div>
              ))}
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div>
                <span className="block text-[11px] font-medium text-ink mb-1.5">Corners</span>
                <div className="flex rounded-lg overflow-hidden border border-rule">
                  {(['pill', 'rounded', 'sharp'] as RadiusId[]).map((r) => (
                    <button
                      key={r}
                      type="button"
                      onClick={() => setRadius(r)}
                      aria-pressed={radius === r}
                      className={`flex-1 px-2 py-2 text-[11px] font-medium capitalize transition ${
                        radius === r ? 'bg-accent text-accent-ink' : 'bg-paper-inset text-ink-3 hover:text-ink'
                      }`}
                    >
                      {r}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label htmlFor="poll-font" className="block text-[11px] font-medium text-ink mb-1.5">
                  Font
                </label>
                <select
                  id="poll-font"
                  value={appearanceFont}
                  onChange={(e) => setAppearanceFont(e.target.value as AppearanceFont)}
                  className="w-full px-2.5 py-2 bg-paper-inset border border-rule rounded-lg text-xs text-ink focus:border-accent focus:outline-hidden"
                >
                  <option value="system">System</option>
                  <option value="serif">Serif</option>
                  <option value="mono">Mono</option>
                  <option value="condensed">Condensed</option>
                </select>
              </div>

              <div>
                <label htmlFor="poll-layout" className="block text-[11px] font-medium text-ink mb-1.5">
                  Layout
                </label>
                <select
                  id="poll-layout"
                  value={layout}
                  onChange={(e) => setLayout(e.target.value as 'list' | 'grid')}
                  className="w-full px-2.5 py-2 bg-paper-inset border border-rule rounded-lg text-xs text-ink focus:border-accent focus:outline-hidden"
                >
                  <option value="list">List</option>
                  <option value="grid">Grid (thumbnails)</option>
                </select>
              </div>

              <div>
                <span className="block text-[11px] font-medium text-ink mb-1.5">On vote</span>
                <button
                  type="button"
                  onClick={() => setEffect(effect === 'confetti' ? 'none' : 'confetti')}
                  aria-pressed={effect === 'confetti'}
                  className={`w-full px-2.5 py-2 rounded-lg text-xs font-medium border transition ${
                    effect === 'confetti'
                      ? 'bg-accent border-accent text-accent-ink'
                      : 'bg-paper-inset border-rule text-ink-3 hover:text-ink'
                  }`}
                >
                  {effect === 'confetti' ? 'Confetti on' : 'Confetti off'}
                </button>
              </div>
            </div>
          </div>

          {/* Optional Close Date */}
          <div className="pt-2">
            <label htmlFor="poll-close-at" className="block text-xs font-medium text-ink mb-1.5">
              Close Date & Time <span className="text-ink-4 font-normal">(optional deadline)</span>
            </label>
            <input
              id="poll-close-at"
              type="datetime-local"
              value={closeAt}
              onChange={(e) => setCloseAt(e.target.value)}
              className="w-full px-3 py-2 bg-paper-inset border border-rule rounded-xl text-xs text-ink focus:border-accent focus:outline-hidden"
            />
          </div>

          {/* Submit Button (8-state tactile) */}
          <button
            type="submit"
            disabled={isPending || title.trim().length === 0}
            className="btn-interactive w-full py-3 px-4 rounded-xl bg-accent hover:bg-accent-strong disabled:bg-paper-3 disabled:text-ink-4 disabled:cursor-not-allowed text-accent-ink font-semibold text-sm shadow-md transition flex items-center justify-center gap-2"
          >
            {isPending ? (
              <>
                <svg className="animate-spin w-4 h-4 text-ink" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
                </svg>
                <span>Publishing to Polls Lab...</span>
              </>
            ) : (
              <span>Publish Poll & Generate Embeds</span>
            )}
          </button>
        </form>
      </div>

      {/* Right: Real-time Live Preview */}
      <div className="lg:col-span-5 space-y-4 lg:sticky lg:top-24">
        <div className="flex items-center justify-between px-1">
          <span className="text-xs font-mono text-ink-3 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-blue-400"></span>
            Simulated Live Preview
          </span>
          <span className="text-[11px] font-mono text-accent">
            {visibility.toUpperCase()}
          </span>
        </div>

        {/* Preview Card (theme-aware simulation) */}
        <div
          className="border rounded-2xl p-5 shadow-xl space-y-4"
          style={{
            background: bg.trim() || (theme === 'minimal' ? '#111827' : preset.swatches[0]),
            borderColor: 'var(--color-rule)',
            fontFamily: FONT_STACK[appearanceFont],
          }}
        >
          <div className="space-y-1.5">
            <h3 className="font-bold text-base text-ink leading-snug">
              {title || 'Your poll question will appear here...'}
            </h3>
            {description && (
              <p className="text-xs text-ink-3 leading-relaxed">
                {description}
              </p>
            )}
          </div>

          {/* Preview Options */}
          <div className="space-y-2 pt-2">
            {options.map((opt, i) => (
              <div
                key={opt.id}
                className="w-full text-left px-3.5 py-2.5 border border-rule bg-paper-inset text-xs font-medium text-ink flex items-center gap-2.5"
                style={{ borderRadius: RADIUS_PX[radius] }}
              >
                {maxSelections > 1 ? (
                  <span className="w-4 h-4 rounded border border-rule-strong flex-shrink-0 flex items-center justify-center">
                  </span>
                ) : (
                  <span className="w-4 h-4 rounded-full border border-rule-strong flex-shrink-0 flex items-center justify-center">
                    <span className="w-2 h-2 rounded-full" style={{ background: 'transparent' }} />
                  </span>
                )}
                {opt.icon_or_image && (
                  opt.icon_or_image.startsWith('http') ? (
                    <img src={opt.icon_or_image} alt="" className="w-6 h-6 rounded object-cover flex-shrink-0" />
                  ) : (
                    <span className="text-sm">{opt.icon_or_image}</span>
                  )
                )}
                <span className="flex-1 truncate">
                  {opt.text || `Option ${i + 1}`}
                </span>
                {isQuiz && correctOptions.includes(opt.id) && (
                  <span className="text-green-400 text-[11px] font-bold">✓</span>
                )}
                <span className="text-[11px] font-mono text-ink-4">0%</span>
              </div>
            ))}
          </div>

          <div className="pt-3 border-t border-rule flex justify-between items-center text-[11px] text-ink-4 font-mono">
            <span>Mode: {resultDisplay}</span>
            <span>
              {maxSelections > 1 ? `${maxSelections}-select` : 'single'}
              {isQuiz ? ' · quiz' : ''}
              {showVoters ? ' · voters' : ''}
            </span>
            <span>Powered by Polls Lab</span>
          </div>
        </div>

        {/* Tip Box */}
        <div className="p-4 rounded-xl bg-paper-inset border border-rule text-xs text-ink-3 space-y-1.5">
          <strong className="text-ink block font-medium">Developer Tip:</strong>
          Once published, you will receive an embed code suitable for GitHub READMEs, Astro sites, and blogs with zero iframe overhead.
        </div>
      </div>

      {/* Success Modal */}
      {createdPoll && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-xs">
          <div className="bg-paper-2 border border-rule rounded-2xl max-w-lg w-full p-6 space-y-5 shadow-2xl">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-full bg-accent-soft border border-accent text-accent flex items-center justify-center text-sm font-bold">
                  ✓
                </div>
                <h3 className="font-bold text-ink text-base">Poll Published Successfully!</h3>
              </div>
              <button
                type="button"
                onClick={() => setCreatedPoll(null)}
                className="text-ink-3 hover:text-ink text-sm"
              >
                ✕
              </button>
            </div>

            <p className="text-xs text-ink-3">
              Your poll <strong className="text-ink">"{createdPoll.title}"</strong> is now live. Grab the embed code below to display it anywhere:
            </p>

            <div className="space-y-3 text-xs">
              <div>
                <label className="block font-medium text-ink-3 mb-1">GitHub README Badge (Markdown)</label>
                <div className="flex gap-2">
                  <input
                    readOnly
                    value={getMarkdownBadgeSnippet(createdPoll.title, createdPoll.id)}
                    className="flex-1 px-2.5 py-1.5 bg-paper-inset border border-rule rounded-lg font-mono text-[11px] text-accent"
                  />
                  <button
                    type="button"
                    onClick={() => copySnippet(getMarkdownBadgeSnippet(createdPoll.title, createdPoll.id), 'badge')}
                    className="px-3 py-1.5 rounded-lg bg-paper-3 hover:bg-paper-3 text-ink text-xs font-medium transition"
                  >
                    {copiedType === 'badge' ? '✓ Copied' : 'Copy'}
                  </button>
                </div>
              </div>

              <div>
                <label className="block font-medium text-ink-3 mb-1">Interactive Iframe (HTML)</label>
                <div className="flex gap-2">
                  <input
                    readOnly
                    value={getIframeSnippet(createdPoll.id, 340)}
                    className="flex-1 px-2.5 py-1.5 bg-paper-inset border border-rule rounded-lg font-mono text-[11px] text-accent"
                  />
                  <button
                    type="button"
                    onClick={() => copySnippet(getIframeSnippet(createdPoll.id, 340), 'iframe')}
                    className="px-3 py-1.5 rounded-lg bg-paper-3 hover:bg-paper-3 text-ink text-xs font-medium transition"
                  >
                    {copiedType === 'iframe' ? '✓ Copied' : 'Copy'}
                  </button>
                </div>
              </div>
            </div>

            <div className="pt-1">
              <label className="block font-medium text-ink-3 mb-1">
                Live preview: the real widget with your {preset.name} theme
              </label>
              <iframe
                src={`${getSiteUrl()}/embed?id=${createdPoll.id}`}
                title={`Live preview of ${createdPoll.title}`}
                className="w-full rounded-xl border border-rule bg-white"
                height={380}
                loading="lazy"
              />
            </div>

            <div className="pt-3 border-t border-rule flex justify-end gap-2">
              <a
                href="/dashboard"
                className="px-4 py-2 rounded-lg bg-accent hover:bg-accent-strong text-accent-ink text-xs font-semibold shadow-xs"
              >
                Go to Dashboard
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

