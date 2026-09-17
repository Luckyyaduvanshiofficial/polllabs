import { getApiUrl, getSiteUrl } from './config';

/**
 * Returns the direct URL to the live SVG or PNG badge for a poll.
 */
export function getBadgeUrl(pollId: string, format: 'svg' | 'png' = 'svg'): string {
  return `${getApiUrl()}/api/v1/badges/${pollId}.${format}`;
}

/**
 * Returns the direct URL to the interactive poll page on the main platform.
 */
export function getPollUrl(pollId: string): string {
  return `${getSiteUrl()}/polls/${pollId}`;
}

/**
 * Returns the isolated embed URL used inside iframes.
 */
export function getEmbedUrl(pollId: string): string {
  return `${getSiteUrl()}/embed?id=${pollId}`;
}

/**
 * Generates the GitHub/GitLab/Dev.to Markdown snippet for a live badge.
 * Compliant with PRD §4.4: Clickable badge image links to the interactive poll on the platform.
 */
export function getMarkdownBadgeSnippet(
  title: string,
  pollId: string,
  format: 'svg' | 'png' = 'svg'
): string {
  const badgeUrl = getBadgeUrl(pollId, format);
  const pollUrl = getPollUrl(pollId);
  const cleanTitle = title.replace(/[\[\]]/g, '');
  return `[![${cleanTitle}](${badgeUrl})](${pollUrl})`;
}

/**
 * Generates an isolated responsive iframe embed snippet.
 */
export function getIframeSnippet(pollId: string, height: number = 380): string {
  const embedUrl = getEmbedUrl(pollId);
  return `<iframe src="${embedUrl}" width="100%" height="${height}" frameborder="0" scrolling="no" style="border-radius:12px;overflow:hidden;" loading="lazy"></iframe>`;
}

/**
 * Robust clipboard copy helper with modern navigator.clipboard and fallback.
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  if (typeof window === 'undefined') return false;

  try {
    if (navigator?.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      return true;
    }
  } catch {
    // Fall back to execCommand if navigator.clipboard is unavailable/blocked
  }

  try {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    const successful = document.execCommand('copy');
    textArea.remove();
    return successful;
  } catch (err) {
    console.error('Failed to copy to clipboard:', err);
    return false;
  }
}
