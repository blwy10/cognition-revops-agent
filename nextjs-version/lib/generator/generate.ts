import { Account, Dataset, Opportunity, OpportunityHistory, Rep, Territory } from '@/lib/types/models';

const DEFAULT_SEED = 123;

class Rng {
  constructor(private seed: number) {}
  next() { this.seed = (this.seed * 1664525 + 1013904223) % 4294967296; return this.seed / 4294967296; }
  randint(a: number, b: number) { return Math.floor(this.next() * (b - a + 1)) + a; }
  choice<T>(arr: T[]) { return arr[this.randint(0, arr.length - 1)]!; }
}

const randomDate = (rng: Rng, start: string, end: string) => {
  const s = new Date(start).getTime();
  const e = new Date(end).getTime();
  return new Date(s + (e - s) * rng.next()).toISOString().slice(0, 10);
};

async function txt(path: string) {
  return (await fetch(path).then((r) => r.text())).split('\n').map((x) => x.trim()).filter(Boolean);
}

export async function generateDataset(seed = DEFAULT_SEED): Promise<Dataset> {
  const rng = new Rng(seed);
  const [firstNames, lastNames, nouns, suffixes, industries, stages] = await Promise.all([
    txt('/data/first-names.txt'),
    txt('/data/last-names.txt'),
    txt('/data/nouns.txt'),
    txt('/data/company-suffixes.txt'),
    txt('/data/bls-top-level.txt'),
    txt('/data/partial-stages.txt'),
  ]);

  const territories: Territory[] = industries.slice(0, 10).map((name, idx) => ({ id: idx + 1, name: `${name} Territory` }));
  const reps: Rep[] = Array.from({ length: 30 }, (_, i) => ({
    id: i + 1,
    name: `${rng.choice(firstNames)} ${rng.choice(lastNames)}`,
    homeState: 'CA',
    region: 'West',
    quota: 500000,
    territoryId: territories[i % territories.length]!.id,
  }));

  const accounts: Account[] = Array.from({ length: 70 }, (_, i) => {
    const rep = reps[rng.randint(0, reps.length - 1)]!;
    return {
      id: i + 1,
      name: `${rng.choice(nouns)} ${rng.choice(suffixes)}`,
      annualRevenue: rng.randint(1_000_000, 500_000_000),
      numDevelopers: rng.randint(10, 5000),
      state: rep.homeState,
      industry: rng.choice(industries),
      isCustomer: rng.next() < 0.3,
      inPipeline: false,
      repId: rep.id,
      territoryId: rep.territoryId,
    };
  });

  const opportunities: Opportunity[] = [];
  for (let i = 0; i < 100; i++) {
    const account = accounts[rng.randint(0, accounts.length - 1)]!;
    opportunities.push({
      id: i + 1,
      name: `${account.name} ${rng.choice(['Devin', 'Windsurf'])}`,
      amount: rng.randint(5_000, 1_000_000),
      stage: rng.choice(stages),
      created_date: randomDate(rng, '2024-07-01', '2026-02-18'),
      closeDate: rng.next() < 0.05 ? null : randomDate(rng, '2025-10-01', '2026-09-30'),
      repId: account.repId,
      accountId: account.id,
    });
  }

  const inPipelineSet = new Set(opportunities.map((o) => o.accountId));
  accounts.forEach((a) => { a.inPipeline = inPipelineSet.has(a.id); });

  const opportunity_history: OpportunityHistory[] = opportunities.flatMap((opp) => {
    const n = rng.randint(0, 2);
    return Array.from({ length: n }, (_, i) => ({
      id: opp.id * 10 + i,
      opportunity_id: opp.id,
      field_name: 'stage',
      old_value: null,
      new_value: opp.stage,
      change_date: randomDate(rng, '2025-10-01', '2026-02-18'),
    }));
  });

  return { generated_at: new Date().toISOString(), reps, accounts, opportunities, territories, opportunity_history };
}
