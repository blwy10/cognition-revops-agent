import { Account, Dataset, Issue, Rep, Severity } from '@/lib/types/models';

type Ctx = { settings: Record<string, number | boolean>; now: Date };
const sev = (s: Severity) => s as Exclude<Severity, 'None'>;
const early = ['Prospecting', 'Qualification', 'Discovery'];
const toDate = (v: string | null | undefined) => (v ? new Date(v) : null);
const daysBetween = (a: Date, b: Date) => Math.floor((a.getTime() - b.getTime()) / 86400000);

function buildIssue(base: Omit<Issue, 'timestamp' | 'status' | 'is_unread' | 'snoozed_until'>): Issue {
  return { ...base, status: 'Open', timestamp: new Date().toISOString(), is_unread: true, snoozed_until: null };
}

export function runRules(dataset: Dataset, settings: Record<string, number | boolean>): Issue[] {
  const ctx: Ctx = { settings, now: new Date() };
  const repMap = new Map<number, Rep>(dataset.reps.map((r) => [r.id, r]));
  const acctMap = new Map<number, Account>(dataset.accounts.map((a) => [a.id, a]));
  const opps = dataset.opportunities.map((o) => ({ ...o, owner: repMap.get(o.repId)?.name ?? '', account_name: acctMap.get(o.accountId)?.name ?? '' }));
  const accounts = dataset.accounts.map((a) => ({ ...a, owner: repMap.get(a.repId)?.name ?? '' }));
  const issues: Issue[] = [];

  const enabled = (id: string) => settings[`rules.enabled.${id}`] !== false;

  if (enabled('stale_opportunity')) {
    for (const opp of opps) {
      const hist = dataset.opportunity_history.filter((h) => h.opportunity_id === opp.id && h.field_name === 'stage');
      const last = hist.sort((a, b) => b.change_date.localeCompare(a.change_date))[0]?.change_date ?? opp.created_date;
      const days = daysBetween(ctx.now, new Date(last));
      const low = Number(settings['stale_opportunity.low_days']);
      const med = Number(settings['stale_opportunity.medium_days']);
      const high = Number(settings['stale_opportunity.high_days']);
      const severity = days > high ? sev('High') : days > med ? sev('Medium') : days > low ? sev('Low') : null;
      if (!severity) continue;
      issues.push(buildIssue({ severity, name: 'Stale Opp', category: 'Pipeline Hygiene', account_name: opp.account_name ?? '', opportunity_name: opp.name, owner: opp.owner ?? '', fields: ['stage'], metric_name: 'Days since last stage change', metric_value: days, formatted_metric_value: `${days} days`, explanation: `Opportunity has not had a stage change in ${days} days.`, resolution: 'Reach out to the sales rep to confirm the opportunity is still active.' }));
    }
  }

  if (enabled('missing_close_date')) {
    for (const opp of opps) {
      if (opp.closeDate) continue;
      const days = daysBetween(ctx.now, new Date(opp.created_date));
      const low = Number(settings['missing_close_date.low_days']);
      const med = Number(settings['missing_close_date.medium_days']);
      const high = Number(settings['missing_close_date.high_days']);
      const severity = days > high ? sev('High') : days > med ? sev('Medium') : days > low ? sev('Low') : null;
      if (!severity) continue;
      issues.push(buildIssue({ severity, name: 'Missing close date', category: 'Pipeline Hygiene', account_name: opp.account_name ?? '', opportunity_name: opp.name, owner: opp.owner ?? '', fields: ['closeDate'], metric_name: 'Days without close date', metric_value: days, formatted_metric_value: `${days} days`, explanation: `Opportunity has no close date and was created ${days} days ago.`, resolution: 'Ask the rep to add a realistic close date.' }));
    }
  }

  return issues;
}
