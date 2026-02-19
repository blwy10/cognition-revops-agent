export type Severity = 'None' | 'Low' | 'Medium' | 'High';

export interface Rep {
  id: number;
  name: string;
  homeState: string;
  region: string;
  quota: number;
  territoryId: number;
}

export interface Account {
  id: number;
  name: string;
  annualRevenue: number;
  numDevelopers: number;
  state: string;
  industry: string;
  isCustomer: boolean;
  inPipeline: boolean;
  repId: number;
  territoryId: number;
  owner?: string;
}

export interface Opportunity {
  id: number;
  name: string;
  amount: number;
  stage: string;
  created_date: string;
  closeDate: string | null;
  repId: number;
  accountId: number;
  owner?: string;
  account_name?: string;
}

export interface OpportunityHistory {
  id: number;
  opportunity_id: number;
  field_name: string;
  old_value: string | null;
  new_value: string | null;
  change_date: string;
}

export interface Territory { id: number; name: string }

export interface Issue {
  severity: Exclude<Severity, 'None'>;
  name: string;
  account_name: string;
  opportunity_name: string;
  category: string;
  owner: string;
  fields: string[];
  metric_name: string;
  metric_value: unknown;
  formatted_metric_value: string;
  explanation: string;
  resolution: string;
  status: 'Open' | 'Acknowledged' | 'Snoozed' | 'Resolved';
  timestamp: string;
  is_unread: boolean;
  snoozed_until: string | null;
}

export interface Run {
  run_id: number;
  datetime: string;
  issues_count: number;
  issues: Issue[];
}

export interface Dataset {
  generated_at: string;
  reps: Rep[];
  accounts: Account[];
  opportunities: Opportunity[];
  territories: Territory[];
  opportunity_history: OpportunityHistory[];
}
