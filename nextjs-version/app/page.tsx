'use client';

// `use client` marks this file as a Client Component in Next.js App Router.
// That is required because this page uses React hooks (`useState`, `useEffect`, `useMemo`),
// browser-only APIs (`localStorage`), and click handlers.

import { generateDataset } from '@/lib/generator/generate';
import { runRules } from '@/lib/rules/runRules';
import { defaultRuleSettings } from '@/lib/rules/settings';
import { Dataset, Run } from '@/lib/types/models';
import {
  Box,
  Button,
  Checkbox,
  FormControlLabel,
  Paper,
  Slider,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Tabs,
  Typography,
} from '@mui/material';
import { useEffect, useMemo, useState } from 'react';

export default function Page() {
  // `tab` drives which section of the UI is currently visible.
  // Material UI Tabs are zero-indexed, so 0 => Data Generator, 1 => Settings, etc.
  const [tab, setTab] = useState(0);

  // Core app state used across tabs.
  // `dataset` starts as null until user generates or uploads data.
  const [dataset, setDataset] = useState<Dataset | null>(null);

  // Rule settings are a dictionary of numeric thresholds and boolean toggles.
  // We seed the state with defaults imported from shared rule config.
  const [settings, setSettings] = useState<Record<string, number | boolean>>(defaultRuleSettings);

  // Each run stores a snapshot of issues produced by analyzing the dataset.
  // New runs are prepended so latest appears first.
  const [runs, setRuns] = useState<Run[]>([]);

  // Which run is selected in "Previous Runs" / "Inbox" views.
  const [selectedRunId, setSelectedRunId] = useState<number | null>(null);

  // Which issue row is selected inside the Inbox panel.
  const [selectedIssue, setSelectedIssue] = useState<number | null>(null);

  useEffect(() => {
    // This effect runs once on first client render.
    // We hydrate persisted app state from localStorage so refreshing the browser
    // does not lose generated data, configured settings, or run history.
    const raw = localStorage.getItem('revops-next-state');
    if (!raw) return;

    const parsed = JSON.parse(raw) as {
      dataset: Dataset | null;
      settings: Record<string, number | boolean>;
      runs: Run[];
      selectedRunId: number | null;
    };

    setDataset(parsed.dataset);
    setSettings(parsed.settings);
    setRuns(parsed.runs);
    setSelectedRunId(parsed.selectedRunId);
  }, []);

  useEffect(() => {
    // Persist whenever any core state changes.
    // Dependency array ensures this only runs when one of these values updates.
    localStorage.setItem(
      'revops-next-state',
      JSON.stringify({ dataset, settings, runs, selectedRunId }),
    );
  }, [dataset, settings, runs, selectedRunId]);

  // `useMemo` caches computed values between renders.
  // Here we avoid re-finding the selected run unless `runs` or `selectedRunId` changed.
  const selectedRun = useMemo(
    () => runs.find((run) => run.run_id === selectedRunId) ?? null,
    [runs, selectedRunId],
  );

  // Optional chaining: when no run is selected, fallback to empty issue list.
  const issues = selectedRun?.issues ?? [];

  const runAnalysis = () => {
    // Guard clause: analysis only makes sense if a dataset exists.
    if (!dataset) return;

    // Run domain rules and collect issues for this snapshot.
    const newIssues = runRules(dataset, settings);

    // New run metadata. We increment from the latest run id when present.
    const run: Run = {
      run_id: (runs[0]?.run_id ?? 0) + 1,
      datetime: new Date().toISOString(),
      issues_count: newIssues.length,
      issues: newIssues,
    };

    // Functional update (`prev => ...`) is recommended when new state depends on old state.
    setRuns((prev) => [run, ...prev]);

    // Jump user straight to the Inbox after running analysis.
    setSelectedRunId(run.run_id);
    setTab(4);
  };

  return (
    // `Box` is Material UI's utility wrapper with style props (`p`, `mt`, etc.).
    <Box p={2}>
      <Typography variant="h4" mb={2}>
        RevOps Tool (Next.js Replica)
      </Typography>

      {/* Material UI Tabs control the active view through `value` + `onChange`. */}
      <Tabs value={tab} onChange={(_, value) => setTab(value)}>
        <Tab label="Data Generator" />
        <Tab label="Settings" />
        <Tab label="Run" />
        <Tab label="Previous Runs" />
        <Tab label="Inbox" />
      </Tabs>

      {/* Tab 0: data generation and JSON upload. */}
      {tab === 0 && (
        <Paper sx={{ p: 2, mt: 2 }}>
          <Button
            variant="contained"
            onClick={async () => {
              setDataset(await generateDataset());
            }}
          >
            Generate data
          </Button>

          {/* `component="label"` lets button proxy clicks to hidden file input. */}
          <Button sx={{ ml: 2 }} component="label">
            Load Existing JSON
            <input
              hidden
              type="file"
              accept="application/json"
              onChange={async (event) => {
                const file = event.target.files?.[0];
                if (!file) return;
                setDataset(JSON.parse(await file.text()));
              }}
            />
          </Button>

          <Typography mt={2}>
            {dataset
              ? `Loaded: ${dataset.accounts.length} accounts, ${dataset.opportunities.length} opportunities`
              : 'No dataset loaded.'}
          </Typography>
        </Paper>
      )}

      {/* Tab 1: sliders for numeric settings and checkboxes for boolean settings. */}
      {tab === 1 && (
        <Paper sx={{ p: 2, mt: 2 }}>
          <Typography variant="h6">Rule Settings</Typography>

          {Object.entries(settings)
            .filter(([, value]) => typeof value === 'number')
            .slice(0, 24)
            .map(([key, value]) => (
              <Box key={key} my={2}>
                <Typography>
                  {key}: {String(value)}
                </Typography>

                <Slider
                  value={Number(value)}
                  min={0}
                  // Simple heuristic range based on key naming.
                  max={key.includes('ratio') ? 5 : key.includes('pct') ? 100 : 1_000_000}
                  step={key.includes('ratio') ? 0.05 : 1}
                  onChange={(_, sliderValue) => {
                    setSettings((current) => ({
                      ...current,
                      [key]: Number(sliderValue),
                    }));
                  }}
                />
              </Box>
            ))}

          {Object.entries(settings)
            .filter(([, value]) => typeof value === 'boolean')
            .map(([key, value]) => (
              <FormControlLabel
                key={key}
                control={
                  <Checkbox
                    checked={Boolean(value)}
                    onChange={(event) => {
                      setSettings((current) => ({
                        ...current,
                        [key]: event.target.checked,
                      }));
                    }}
                  />
                }
                label={key}
              />
            ))}
        </Paper>
      )}

      {/* Tab 2: run analysis action. Disabled until data exists. */}
      {tab === 2 && (
        <Paper sx={{ p: 2, mt: 2 }}>
          <Button variant="contained" onClick={runAnalysis} disabled={!dataset}>
            Run Analysis
          </Button>
        </Paper>
      )}

      {/* Tab 3: list historical runs. Clicking a row opens Inbox tab for that run. */}
      {tab === 3 && (
        <Paper sx={{ p: 2, mt: 2 }}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>ID</TableCell>
                <TableCell>Datetime</TableCell>
                <TableCell>Issues</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {runs.map((run) => (
                <TableRow
                  key={run.run_id}
                  hover
                  selected={run.run_id === selectedRunId}
                  onClick={() => {
                    setSelectedRunId(run.run_id);
                    setTab(4);
                  }}
                >
                  <TableCell>{run.run_id}</TableCell>
                  <TableCell>{new Date(run.datetime).toLocaleString()}</TableCell>
                  <TableCell>{run.issues_count}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Paper>
      )}

      {/* Tab 4: inbox split view (left issue list, right issue details). */}
      {tab === 4 && (
        <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2, mt: 2 }}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6">Issues ({issues.length})</Typography>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Severity</TableCell>
                  <TableCell>Name</TableCell>
                  <TableCell>Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {issues.map((issue, index) => (
                  <TableRow
                    key={index}
                    hover
                    selected={selectedIssue === index}
                    onClick={() => {
                      setSelectedIssue(index);

                      // Mimic inbox behavior: opening an unread issue acknowledges it.
                      if (issue.status === 'Open') issue.status = 'Acknowledged';
                      issue.is_unread = false;

                      // Force re-render after mutating nested object.
                      // In production apps, immutable updates are generally preferred.
                      setRuns([...runs]);
                    }}
                  >
                    <TableCell>{issue.severity}</TableCell>
                    <TableCell>{issue.name}</TableCell>
                    <TableCell>{issue.status}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Paper>

          <Paper sx={{ p: 2 }}>
            {selectedIssue === null
              ? 'Select an issue'
              : (() => {
                  const issue = issues[selectedIssue];
                  if (!issue) return 'Select an issue';

                  return (
                    <Box>
                      <Typography variant="h6">{issue.name}</Typography>
                      <Typography>{issue.explanation}</Typography>
                      <Typography>Owner: {issue.owner}</Typography>
                      <Typography>
                        Metric: {issue.metric_name} = {issue.formatted_metric_value}
                      </Typography>
                      <Typography>Status: {issue.status}</Typography>

                      <Box mt={2}>
                        <Button
                          onClick={() => {
                            issue.status = 'Snoozed';
                            issue.snoozed_until = new Date(Date.now() + 86_400_000).toISOString();
                            setRuns([...runs]);
                          }}
                        >
                          Snooze
                        </Button>

                        <Button
                          onClick={() => {
                            issue.status = 'Resolved';
                            issue.snoozed_until = null;
                            setRuns([...runs]);
                          }}
                        >
                          Resolve
                        </Button>

                        <Button
                          onClick={() => {
                            issue.status = 'Open';
                            issue.snoozed_until = null;
                            issue.is_unread = true;
                            setRuns([...runs]);
                          }}
                        >
                          Reopen
                        </Button>
                      </Box>
                    </Box>
                  );
                })()}
          </Paper>
        </Box>
      )}
    </Box>
  );
}
