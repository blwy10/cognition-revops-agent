'use client';

import { generateDataset } from '@/lib/generator/generate';
import { defaultRuleSettings } from '@/lib/rules/settings';
import { runRules } from '@/lib/rules/runRules';
import { Dataset, Issue, Run } from '@/lib/types/models';
import { Box, Button, Checkbox, FormControlLabel, Paper, Slider, Tab, Tabs, Table, TableBody, TableCell, TableHead, TableRow, TextField, Typography } from '@mui/material';
import { useEffect, useMemo, useState } from 'react';

export default function Page() {
  const [tab, setTab] = useState(0);
  const [dataset, setDataset] = useState<Dataset | null>(null);
  const [settings, setSettings] = useState<Record<string, number | boolean>>(defaultRuleSettings);
  const [runs, setRuns] = useState<Run[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<number | null>(null);
  const [selectedIssue, setSelectedIssue] = useState<number | null>(null);

  useEffect(() => {
    const raw = localStorage.getItem('revops-next-state');
    if (!raw) return;
    const parsed = JSON.parse(raw) as { dataset: Dataset | null; settings: Record<string, number | boolean>; runs: Run[]; selectedRunId: number | null };
    setDataset(parsed.dataset); setSettings(parsed.settings); setRuns(parsed.runs); setSelectedRunId(parsed.selectedRunId);
  }, []);

  useEffect(() => {
    localStorage.setItem('revops-next-state', JSON.stringify({ dataset, settings, runs, selectedRunId }));
  }, [dataset, settings, runs, selectedRunId]);

  const selectedRun = useMemo(() => runs.find((r) => r.run_id === selectedRunId) ?? null, [runs, selectedRunId]);
  const issues = selectedRun?.issues ?? [];

  const runAnalysis = () => {
    if (!dataset) return;
    const newIssues = runRules(dataset, settings);
    const run: Run = { run_id: (runs[0]?.run_id ?? 0) + 1, datetime: new Date().toISOString(), issues_count: newIssues.length, issues: newIssues };
    setRuns((prev) => [run, ...prev]); setSelectedRunId(run.run_id); setTab(4);
  };

  return <Box p={2}>
    <Typography variant="h4" mb={2}>RevOps Tool (Next.js Replica)</Typography>
    <Tabs value={tab} onChange={(_, v) => setTab(v)}><Tab label="Data Generator" /><Tab label="Settings" /><Tab label="Run" /><Tab label="Previous Runs" /><Tab label="Inbox" /></Tabs>

    {tab===0 && <Paper sx={{p:2,mt:2}}><Button variant="contained" onClick={async()=>setDataset(await generateDataset())}>Generate data</Button>
      <Button sx={{ml:2}} component="label">Load Existing JSON<input hidden type="file" accept="application/json" onChange={async (e)=>{ const f=e.target.files?.[0]; if(!f) return; setDataset(JSON.parse(await f.text()));}} /></Button>
      <Typography mt={2}>{dataset ? `Loaded: ${dataset.accounts.length} accounts, ${dataset.opportunities.length} opportunities` : 'No dataset loaded.'}</Typography>
    </Paper>}

    {tab===1 && <Paper sx={{p:2,mt:2}}><Typography variant="h6">Rule Settings</Typography>
      {Object.entries(settings).filter(([k,v])=>typeof v==='number').slice(0,24).map(([key,val])=><Box key={key} my={2}><Typography>{key}: {String(val)}</Typography><Slider value={Number(val)} min={0} max={key.includes('ratio')?5: key.includes('pct')?100: 1000000} step={key.includes('ratio')?0.05:1} onChange={(_,v)=>setSettings((s)=>({...s,[key]:Number(v)}))} /></Box>)}
      {Object.entries(settings).filter(([,v])=>typeof v==='boolean').map(([k,v]) => <FormControlLabel key={k} control={<Checkbox checked={Boolean(v)} onChange={(e)=>setSettings((s)=>({...s,[k]:e.target.checked}))} />} label={k} />)}
    </Paper>}

    {tab===2 && <Paper sx={{p:2,mt:2}}><Button variant="contained" onClick={runAnalysis} disabled={!dataset}>Run Analysis</Button></Paper>}

    {tab===3 && <Paper sx={{p:2,mt:2}}><Table><TableHead><TableRow><TableCell>ID</TableCell><TableCell>Datetime</TableCell><TableCell>Issues</TableCell></TableRow></TableHead><TableBody>{runs.map((r)=><TableRow key={r.run_id} hover selected={r.run_id===selectedRunId} onClick={()=>{setSelectedRunId(r.run_id); setTab(4);}}><TableCell>{r.run_id}</TableCell><TableCell>{new Date(r.datetime).toLocaleString()}</TableCell><TableCell>{r.issues_count}</TableCell></TableRow>)}</TableBody></Table></Paper>}

    {tab===4 && <Box sx={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:2,mt:2}}>
      <Paper sx={{p:2}}><Typography variant="h6">Issues ({issues.length})</Typography><Table size="small"><TableHead><TableRow><TableCell>Severity</TableCell><TableCell>Name</TableCell><TableCell>Status</TableCell></TableRow></TableHead><TableBody>{issues.map((i,idx)=><TableRow key={idx} hover selected={selectedIssue===idx} onClick={()=>{setSelectedIssue(idx); if(i.status==='Open') i.status='Acknowledged'; i.is_unread=false; setRuns([...runs]);}}><TableCell>{i.severity}</TableCell><TableCell>{i.name}</TableCell><TableCell>{i.status}</TableCell></TableRow>)}</TableBody></Table></Paper>
      <Paper sx={{p:2}}>{selectedIssue===null? 'Select an issue' : (()=>{ const issue=issues[selectedIssue]; if(!issue) return 'Select an issue'; return <Box><Typography variant="h6">{issue.name}</Typography><Typography>{issue.explanation}</Typography><Typography>Owner: {issue.owner}</Typography><Typography>Metric: {issue.metric_name} = {issue.formatted_metric_value}</Typography><Typography>Status: {issue.status}</Typography><Box mt={2}><Button onClick={()=>{issue.status='Snoozed'; issue.snoozed_until=new Date(Date.now()+86400000).toISOString(); setRuns([...runs]);}}>Snooze</Button><Button onClick={()=>{issue.status='Resolved'; issue.snoozed_until=null; setRuns([...runs]);}}>Resolve</Button><Button onClick={()=>{issue.status='Open'; issue.snoozed_until=null; issue.is_unread=true; setRuns([...runs]);}}>Reopen</Button></Box></Box>; })()}</Paper>
    </Box>}
  </Box>;
}
