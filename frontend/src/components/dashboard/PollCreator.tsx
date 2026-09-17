import React, { useState, useTransition } from 'react';
import { getApiUrl } from '../../lib/config';
import { getMarkdownBadgeSnippet, getIframeSnippet, copyToClipboard } from '../../lib/embed';

interface PollOptionItem {
  id: string;
  text: string;
  icon_or_image: string;
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

  const [isPending, startTransition] = useTransition();
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [createdPoll, setCreatedPoll] = useState<{ id: string; title: string } | null>(null);
  const [copiedType, setCopiedType] = useState<string | null>(null);

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

    startTransition(async () => {
      try {
        const token = typeof window !== 'undefined' ? localStorage.getItem('polllabs_auth_token') || 'dev-user-local' : 'dev-user-local';
        const res = await fetch(`${getApiUrl()}/api/v1/polls`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
            'x-dev-user-id': token,
          },
          body: JSON.stringify({
            title: title.trim(),
            description: description.trim() || undefined,
            options: validOptions,
            visibility,
            result_display: resultDisplay,
            close_at: closeAt ? new Date(closeAt).toISOString() : undefined,
          }),
        });

        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData.detail || `Server returned error (${res.status})`);
        }

        const data = await res.json();
        setCreatedPoll({ id: data.id, title: data.title });
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
      <div className="lg:col-span-7 bg-[#111827] border border-[#1e293b] rounded-2xl p-6 sm:p-8 shadow-xl space-y-6">
        <div>
          <span className="text-xs font-mono text-blue-400 uppercase tracking-wider">Studio</span>
          <h2 className="text-2xl font-bold text-white mt-1">Configure Your Poll</h2>
          <p className="text-xs text-[#94a3b8] mt-1">
            Build single-choice polls with live preview and instant embed generation.
          </p>
        </div>

        {errorMessage && (
          <div className="p-3.5 rounded-lg bg-red-950/40 border border-red-800/60 text-red-300 text-xs flex items-center justify-between">
            <span>{errorMessage}</span>
            <button
              type="button"
              onClick={() => setErrorMessage(null)}
              className="text-red-400 hover:text-red-200 ml-2 font-bold"
            >
              ✕
            </button>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Question / Title */}
          <div>
            <div className="flex justify-between items-center mb-1.5">
              <label htmlFor="poll-title" className="text-xs font-medium text-white">
                Poll Question / Headline <span className="text-rose-400">*</span>
              </label>
              <span className="text-[11px] font-mono text-[#64748b]">
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
              className="w-full px-3.5 py-2.5 bg-[#0b0f19] border border-[#1e293b] focus:border-blue-500 rounded-xl text-sm text-white placeholder-[#64748b] focus:outline-hidden transition"
            />
          </div>

          {/* Description (Optional) */}
          <div>
            <label htmlFor="poll-description" className="block text-xs font-medium text-white mb-1.5">
              Context or Description <span className="text-[#64748b] font-normal">(optional)</span>
            </label>
            <textarea
              id="poll-description"
              rows={2}
              maxLength={500}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Provide background context or guidelines for voters..."
              className="w-full px-3.5 py-2.5 bg-[#0b0f19] border border-[#1e293b] focus:border-blue-500 rounded-xl text-sm text-white placeholder-[#64748b] focus:outline-hidden transition resize-none"
            />
          </div>

          {/* Options List */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-xs font-medium text-white">
                Poll Options <span className="text-rose-400">*</span> (min 2, max 10)
              </label>
              <span className="text-[11px] font-mono text-[#64748b]">
                {options.length}/10 options
              </span>
            </div>

            <div className="space-y-2.5">
              {options.map((opt, idx) => (
                <div key={opt.id} className="flex gap-2 items-center">
                  <span className="w-6 h-6 rounded-md bg-[#0b0f19] border border-[#1e293b] text-[#94a3b8] font-mono text-xs flex items-center justify-center flex-shrink-0">
                    {idx + 1}
                  </span>
                  {/* Emoji or Image Icon */}
                  <input
                    type="text"
                    placeholder="Emoji or Icon URL"
                    value={opt.icon_or_image}
                    onChange={(e) => handleOptionChange(idx, 'icon_or_image', e.target.value)}
                    className="w-28 px-2.5 py-2 bg-[#0b0f19] border border-[#1e293b] rounded-lg text-xs text-white placeholder-[#64748b] focus:border-blue-500 focus:outline-hidden transition flex-shrink-0"
                    title="Enter single emoji (e.g. ⚡) or image URL (https://...)"
                  />
                  {/* Option Text */}
                  <input
                    type="text"
                    required
                    placeholder={`Option ${idx + 1} text`}
                    value={opt.text}
                    onChange={(e) => handleOptionChange(idx, 'text', e.target.value)}
                    className="flex-1 px-3 py-2 bg-[#0b0f19] border border-[#1e293b] rounded-lg text-xs text-white placeholder-[#64748b] focus:border-blue-500 focus:outline-hidden transition"
                  />
                  {/* Remove Button */}
                  {options.length > 2 && (
                    <button
                      type="button"
                      onClick={() => handleRemoveOption(idx)}
                      className="p-2 text-[#64748b] hover:text-rose-400 hover:bg-rose-950/20 rounded-lg transition"
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
                className="btn-interactive text-xs font-semibold text-blue-400 hover:text-blue-300 flex items-center gap-1 mt-2"
              >
                <span>+ Add another option</span>
              </button>
            )}
          </div>

          {/* Settings Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-4 border-t border-[#1e293b]">
            <div>
              <label htmlFor="poll-visibility" className="block text-xs font-medium text-white mb-1.5">
                Visibility
              </label>
              <select
                id="poll-visibility"
                value={visibility}
                onChange={(e) => setVisibility(e.target.value as any)}
                className="w-full px-3 py-2 bg-[#0b0f19] border border-[#1e293b] rounded-xl text-xs text-white focus:border-blue-500 focus:outline-hidden"
              >
                <option value="public">Public (Discoverable & on Leaderboards)</option>
                <option value="private">Private (Unlisted, direct link & embed only)</option>
              </select>
              <p className="text-[10px] text-[#64748b] mt-1">
                {visibility === 'public'
                  ? 'Eligible for trending and community leaderboards.'
                  : 'Hidden from search and feeds; accessible only where embedded.'}
              </p>
            </div>

            <div>
              <label htmlFor="poll-results" className="block text-xs font-medium text-white mb-1.5">
                Result Display
              </label>
              <select
                id="poll-results"
                value={resultDisplay}
                onChange={(e) => setResultDisplay(e.target.value as any)}
                className="w-full px-3 py-2 bg-[#0b0f19] border border-[#1e293b] rounded-xl text-xs text-white focus:border-blue-500 focus:outline-hidden"
              >
                <option value="show_counts">Show raw counts & percentages</option>
                <option value="show_percentage">Show percentages only (counts masked)</option>
                <option value="hidden_until_close">Hidden until poll deadline closes</option>
              </select>
              <p className="text-[10px] text-[#64748b] mt-1">
                {resultDisplay === 'show_counts'
                  ? 'Voters see full vote numbers and percentages.'
                  : resultDisplay === 'show_percentage'
                  ? 'Voters only see percentage shares, preventing bias.'
                  : 'Results remain secret until poll close date.'}
              </p>
            </div>
          </div>

          {/* Optional Close Date */}
          <div className="pt-2">
            <label htmlFor="poll-close-at" className="block text-xs font-medium text-white mb-1.5">
              Close Date & Time <span className="text-[#64748b] font-normal">(optional deadline)</span>
            </label>
            <input
              id="poll-close-at"
              type="datetime-local"
              value={closeAt}
              onChange={(e) => setCloseAt(e.target.value)}
              className="w-full px-3 py-2 bg-[#0b0f19] border border-[#1e293b] rounded-xl text-xs text-white focus:border-blue-500 focus:outline-hidden"
            />
          </div>

          {/* Submit Button (8-state tactile) */}
          <button
            type="submit"
            disabled={isPending || title.trim().length === 0}
            className="btn-interactive w-full py-3 px-4 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:bg-[#1e293b] disabled:text-[#64748b] disabled:cursor-not-allowed text-white font-semibold text-sm shadow-md transition flex items-center justify-center gap-2"
          >
            {isPending ? (
              <>
                <svg className="animate-spin w-4 h-4 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
                </svg>
                <span>Publishing to PollLabs...</span>
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
          <span className="text-xs font-mono text-[#94a3b8] flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-blue-400"></span>
            Simulated Live Preview
          </span>
          <span className="text-[11px] font-mono text-emerald-400">
            {visibility.toUpperCase()}
          </span>
        </div>

        {/* Preview Card */}
        <div className="bg-[#111827] border border-[#1e293b] rounded-2xl p-5 shadow-xl space-y-4">
          <div className="space-y-1.5">
            <h3 className="font-bold text-base text-white leading-snug">
              {title || 'Your poll question will appear here...'}
            </h3>
            {description && (
              <p className="text-xs text-[#94a3b8] leading-relaxed">
                {description}
              </p>
            )}
          </div>

          {/* Preview Options */}
          <div className="space-y-2 pt-2">
            {options.map((opt, i) => (
              <div
                key={opt.id}
                className="w-full text-left px-3.5 py-2.5 rounded-xl border border-[#1e293b] bg-[#0b0f19] text-xs font-medium text-[#f8fafc] flex items-center gap-2.5"
              >
                {opt.icon_or_image && (
                  <span className="text-sm">{opt.icon_or_image}</span>
                )}
                <span className="flex-1 truncate">
                  {opt.text || `Option ${i + 1}`}
                </span>
                <span className="text-[11px] font-mono text-[#64748b]">0%</span>
              </div>
            ))}
          </div>

          <div className="pt-3 border-t border-[#1e293b] flex justify-between items-center text-[11px] text-[#64748b] font-mono">
            <span>Mode: {resultDisplay}</span>
            <span>Powered by PollLabs</span>
          </div>
        </div>

        {/* Tip Box */}
        <div className="p-4 rounded-xl bg-[#0b0f19] border border-[#1e293b] text-xs text-[#94a3b8] space-y-1.5">
          <strong className="text-white block font-medium">Developer Tip:</strong>
          Once published, you will receive an embed code suitable for GitHub READMEs, Astro sites, and blogs with zero iframe overhead.
        </div>
      </div>

      {/* Success Modal */}
      {createdPoll && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-xs">
          <div className="bg-[#111827] border border-[#1e293b] rounded-2xl max-w-lg w-full p-6 space-y-5 shadow-2xl">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-full bg-emerald-950 border border-emerald-700/50 text-emerald-400 flex items-center justify-center text-sm font-bold">
                  ✓
                </div>
                <h3 className="font-bold text-white text-base">Poll Published Successfully!</h3>
              </div>
              <button
                type="button"
                onClick={() => setCreatedPoll(null)}
                className="text-[#94a3b8] hover:text-white text-sm"
              >
                ✕
              </button>
            </div>

            <p className="text-xs text-[#94a3b8]">
              Your poll <strong className="text-white">"{createdPoll.title}"</strong> is now live. Grab the embed code below to display it anywhere:
            </p>

            <div className="space-y-3 text-xs">
              <div>
                <label className="block font-medium text-[#94a3b8] mb-1">GitHub README Badge (Markdown)</label>
                <div className="flex gap-2">
                  <input
                    readOnly
                    value={getMarkdownBadgeSnippet(createdPoll.title, createdPoll.id)}
                    className="flex-1 px-2.5 py-1.5 bg-[#0b0f19] border border-[#1e293b] rounded-lg font-mono text-[11px] text-emerald-300"
                  />
                  <button
                    type="button"
                    onClick={() => copySnippet(getMarkdownBadgeSnippet(createdPoll.title, createdPoll.id), 'badge')}
                    className="px-3 py-1.5 rounded-lg bg-[#1e293b] hover:bg-[#334155] text-white text-xs font-medium transition"
                  >
                    {copiedType === 'badge' ? '✓ Copied' : 'Copy'}
                  </button>
                </div>
              </div>

              <div>
                <label className="block font-medium text-[#94a3b8] mb-1">Interactive Iframe (HTML)</label>
                <div className="flex gap-2">
                  <input
                    readOnly
                    value={getIframeSnippet(createdPoll.id, 340)}
                    className="flex-1 px-2.5 py-1.5 bg-[#0b0f19] border border-[#1e293b] rounded-lg font-mono text-[11px] text-cyan-300"
                  />
                  <button
                    type="button"
                    onClick={() => copySnippet(getIframeSnippet(createdPoll.id, 340), 'iframe')}
                    className="px-3 py-1.5 rounded-lg bg-[#1e293b] hover:bg-[#334155] text-white text-xs font-medium transition"
                  >
                    {copiedType === 'iframe' ? '✓ Copied' : 'Copy'}
                  </button>
                </div>
              </div>
            </div>

            <div className="pt-3 border-t border-[#1e293b] flex justify-end gap-2">
              <a
                href="/dashboard"
                className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-xs"
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

