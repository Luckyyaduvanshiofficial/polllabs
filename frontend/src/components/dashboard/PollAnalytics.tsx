/**
 * Owner analytics for one poll.
 *
 * All network calls go through lib/api, which sends the verified PocketBase
 * bearer token. The previous version fell back to a literal `dev-user-local`
 * token and an `x-dev-user-id` header, both of which the API now rejects.
 */
import React, { useCallback, useEffect, useState } from 'react';
import { downloadExport, getAnalytics, type Analytics } from '../../lib/api';
import { isSignedIn, startSignIn } from '../../lib/auth';

interface Props {
  pollId: string;
}

type Status = 'loading' | 'ready' | 'error' | 'unauthenticated';

export default function PollAnalytics({ pollId }: Props) {
  const [data, setData] = useState<Analytics | null>(null);
  const [status, setStatus] = useState<Status>('loading');
  const [error, setError] = useState<string | null>(null);
  const [exporting, setExporting] = useState<'csv' | 'json' | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!isSignedIn()) {
      setStatus('unauthenticated');
      return;
    }

    setStatus('loading');
    setError(null);

    const result = await getAnalytics(pollId);
    if (!result.ok) {
      if (result.status === 401) {
        setStatus('unauthenticated');
        return;
      }
      setError(result.error);
      setStatus('error');
      return;
    }

    setData(result.data);
    setStatus('ready');
  }, [pollId]);

  useEffect(() => {
    load();
  }, [load]);

  const onExport = async (format: 'csv' | 'json') => {
    setExporting(format);
    setExportError(null);

    const result = await downloadExport(pollId, format);
    if (!result.ok) {
      setExportError(result.error);
      setExporting(null);
      return;
    }

    const url = URL.createObjectURL(result.data);
    const link = document.createElement('a');
    link.href = url;
    link.download = `poll_${pollId}_votes.${format}`;
    document.body.append(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
    setExporting(null);
  };

  if (status === 'unauthenticated') {
    return (
      <div className="an__state">
        <p className="an__state-msg">Sign in to view analytics for this poll.</p>
        <p className="an__state-hint">
          Analytics are owner only. The API checks the poll's owner against your signed-in account.
        </p>
        <button type="button" className="btn btn--primary" onClick={() => startSignIn()}>
          Sign in with GitHub
        </button>
      </div>
    );
  }

  if (status === 'loading') {
    return (
      <div className="an" aria-busy="true">
        <div className="skeleton" style={{ height: '1.5rem', width: '40%' }} />
        <div className="an__kpis">
          {[0, 1, 2].map((i) => (
            <div key={i} className="skeleton" style={{ height: '4rem' }} />
          ))}
        </div>
        <div className="skeleton" style={{ height: '11rem' }} />
      </div>
    );
  }

  if (status === 'error') {
    return (
      <div className="an__state an__state--error">
        <p className="an__state-msg">Could not load analytics.</p>
        <p className="an__state-hint">{error}</p>
        <div className="an__state-actions">
          <button type="button" className="btn btn--ghost" onClick={load}>
            Try again
          </button>
          <a href="/dashboard" className="btn btn--quiet">
            Back to dashboard
          </a>
        </div>
      </div>
    );
  }

  if (!data) return null;

  const timeline = Object.entries(data.votes_over_time).sort(([a], [b]) => a.localeCompare(b));
  const options = Object.entries(data.options_breakdown).sort((a, b) => b[1] - a[1]);
  const referrers = Object.entries(data.referrers_breakdown).sort((a, b) => b[1] - a[1]);
  const peak = Math.max(...Object.values(data.votes_over_time), 1);

  const hasVotes = data.total_votes > 0;

  return (
    <div className="an">
      <header className="an__head">
        <div className="an__ident">
          <p className="field-label">poll {data.poll_id}</p>
          <h2 className="an__title">{data.title}</h2>
        </div>

        <div className="an__exports">
          <button
            type="button"
            className="btn btn--ghost"
            disabled={exporting !== null || !hasVotes}
            onClick={() => onExport('csv')}
          >
            {exporting === 'csv' ? 'exporting' : 'export csv'}
          </button>
          <button
            type="button"
            className="btn btn--ghost"
            disabled={exporting !== null || !hasVotes}
            onClick={() => onExport('json')}
          >
            {exporting === 'json' ? 'exporting' : 'export json'}
          </button>
        </div>
      </header>

      {exportError && (
        <p className="an__inline-error" role="alert">
          {exportError}
        </p>
      )}

      {!hasVotes ? (
        <div className="an__state">
          <p className="an__state-msg">No votes recorded yet.</p>
          <p className="an__state-hint">
            Share the poll's badge or embed to start collecting responses. Analytics fill in as votes
            arrive.
          </p>
          <a href={`/polls?id=${encodeURIComponent(data.poll_id)}`} className="btn btn--ghost">
            View the poll
          </a>
        </div>
      ) : (
        <>
          <dl className="an__kpis">
            <div className="an__kpi">
              <dt className="field-label">Total votes</dt>
              <dd className="an__kpi-num tnum">{data.total_votes.toLocaleString()}</dd>
              <dd className="an__kpi-note">One per device, deduplicated server-side.</dd>
            </div>
            <div className="an__kpi">
              <dt className="field-label">Referrer sources</dt>
              <dd className="an__kpi-num tnum">{referrers.length}</dd>
              <dd className="an__kpi-note">Distinct pages that sent a vote.</dd>
            </div>
            <div className="an__kpi">
              <dt className="field-label">Days with votes</dt>
              <dd className="an__kpi-num tnum">{timeline.length}</dd>
              <dd className="an__kpi-note">Days where at least one vote landed.</dd>
            </div>
          </dl>

          <section className="an__panel" aria-labelledby="timeline-title">
            <div className="an__panel-head">
              <h3 id="timeline-title" className="an__panel-title">
                Votes per day
              </h3>
              <span className="an__panel-meta tnum">peak {peak}</span>
            </div>

            <div className="an__chart" role="img" aria-label={describeTimeline(timeline)}>
              {timeline.map(([date, count]) => (
                <div key={date} className="an__bar-col">
                  <span className="an__bar-val tnum">{count}</span>
                  <div
                    className="an__bar"
                    style={{ height: `${Math.max((count / peak) * 100, 4)}%` }}
                  />
                  <span className="an__bar-date">{date.slice(5)}</span>
                </div>
              ))}
            </div>
          </section>

          <div className="an__split">
            <section className="an__panel" aria-labelledby="options-title">
              <h3 id="options-title" className="an__panel-title">
                By option
              </h3>
              <ul className="an__list">
                {options.map(([label, count], i) => {
                  const pct = (count / data.total_votes) * 100;
                  return (
                    <li key={label} className="an__list-row">
                      <div className="an__list-line">
                        <span className="an__list-label">{label}</span>
                        <span className="an__list-val tnum">
                          {count} ({pct.toFixed(1)}%)
                        </span>
                      </div>
                      <div className="meter">
                        <div
                          className={i === 0 ? 'meter__fill meter__fill--lead' : 'meter__fill'}
                          style={{ width: `${Math.max(pct, 1)}%` }}
                        />
                      </div>
                    </li>
                  );
                })}
              </ul>
            </section>

            <section className="an__panel" aria-labelledby="referrers-title">
              <h3 id="referrers-title" className="an__panel-title">
                By referrer
              </h3>
              <ul className="an__list an__list--flat">
                {referrers.map(([ref, count]) => (
                  <li key={ref} className="an__ref-row">
                    <span className="an__ref-name" title={ref}>
                      {ref}
                    </span>
                    <span className="an__list-val tnum">{count}</span>
                  </li>
                ))}
              </ul>
            </section>
          </div>
        </>
      )}

      <style>{`
        .an { display: grid; gap: var(--space-xl); }

        .an__head {
          display: flex; align-items: flex-end; justify-content: space-between;
          gap: var(--space-md); flex-wrap: wrap;
          padding-bottom: var(--space-md);
          border-bottom: var(--rule-hair) solid var(--color-rule);
        }
        .an__title { font-size: var(--text-xl); margin-top: var(--space-2xs); }
        .an__exports { display: flex; gap: var(--space-xs); }

        .an__inline-error {
          padding: var(--space-xs) var(--space-sm);
          background: var(--color-danger-wash);
          border-left: 2px solid var(--color-danger);
          color: var(--color-ink); font-size: var(--text-xs);
        }

        .an__kpis {
          display: grid; grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: var(--space-lg); margin: 0;
        }
        .an__kpi { border-top: 2px solid var(--color-accent-dim); padding-top: var(--space-sm); }
        .an__kpi-num {
          margin: var(--space-2xs) 0 0;
          font-size: var(--text-2xl); color: var(--color-ink); font-weight: 600;
        }
        .an__kpi-note { margin: var(--space-2xs) 0 0; font-size: var(--text-2xs); color: var(--color-ink-4); }

        .an__panel { display: grid; gap: var(--space-md); min-width: 0; }
        .an__panel-head { display: flex; align-items: baseline; justify-content: space-between; gap: var(--space-md); }
        .an__panel-title { font-size: var(--text-sm); color: var(--color-ink); }
        .an__panel-meta { font-size: var(--text-xs); color: var(--color-ink-4); }

        .an__chart {
          display: flex; align-items: flex-end; gap: var(--space-2xs);
          height: 11rem; padding-top: var(--space-md);
          border-bottom: var(--rule-hair) solid var(--color-rule);
          overflow-x: auto;
        }
        .an__bar-col {
          flex: 1 1 0; min-width: 1.75rem;
          display: flex; flex-direction: column; align-items: center; gap: var(--space-2xs);
          height: 100%; justify-content: flex-end;
        }
        .an__bar {
          width: 100%; max-width: 2.5rem;
          background: var(--color-accent-dim);
          border-radius: var(--radius-sm) var(--radius-sm) 0 0;
          transition: background-color var(--dur-fast) var(--ease-out);
        }
        .an__bar-col:hover .an__bar { background: var(--color-accent); }
        .an__bar-val { font-size: var(--text-2xs); color: var(--color-ink-3); }
        .an__bar-date { font-size: var(--text-2xs); color: var(--color-ink-4); white-space: nowrap; }

        .an__split { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--space-2xl); }

        .an__list { list-style: none; margin: 0; padding: 0; display: grid; gap: var(--space-md); }
        .an__list--flat { gap: 0; border-top: var(--rule-hair) solid var(--color-rule); }
        .an__list-row { display: grid; gap: var(--space-2xs); }
        .an__list-line { display: flex; justify-content: space-between; gap: var(--space-md); font-size: var(--text-sm); }
        .an__list-label { color: var(--color-ink); min-width: 0; overflow-wrap: anywhere; }
        .an__list-val { color: var(--color-ink-2); white-space: nowrap; }

        .an__ref-row {
          display: flex; justify-content: space-between; gap: var(--space-md);
          padding-block: var(--space-sm);
          border-bottom: var(--rule-hair) solid var(--color-rule);
          font-size: var(--text-xs);
        }
        .an__ref-name {
          color: var(--color-ink-2); min-width: 0;
          overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
        }

        .an__state {
          display: grid; gap: var(--space-sm); justify-items: start;
          padding-block: var(--space-2xl);
        }
        .an__state-msg { font-size: var(--text-base); color: var(--color-ink); }
        .an__state--error .an__state-msg { color: var(--color-danger); }
        .an__state-hint { font-size: var(--text-xs); color: var(--color-ink-3); max-width: 54ch; line-height: 1.7; }
        .an__state-actions { display: flex; gap: var(--space-xs); flex-wrap: wrap; }

        @media (max-width: 60rem) {
          .an__kpis, .an__split { grid-template-columns: minmax(0, 1fr); }
          .an__split { gap: var(--space-xl); }
        }
      `}</style>
    </div>
  );
}

/** Text alternative for the bar chart, so the data is not image-only. */
function describeTimeline(entries: [string, number][]): string {
  if (entries.length === 0) return 'No votes recorded.';
  const total = entries.reduce((sum, [, n]) => sum + n, 0);
  const [peakDate, peakCount] = entries.reduce((best, cur) => (cur[1] > best[1] ? cur : best));
  return `Daily votes from ${entries[0][0]} to ${entries[entries.length - 1][0]}. ${total} votes total. Busiest day ${peakDate} with ${peakCount}.`;
}
