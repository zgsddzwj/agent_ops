"use client";

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchApi } from './api';

// ─── Project hooks ───

export interface Project {
  id: string;
  name: string;
  root_path?: string | null;
  entrypoint?: string | null;
}

export function useProjects(apiKey?: string) {
  return useQuery({
    queryKey: ['projects', apiKey],
    queryFn: () => fetchApi<Project[]>('/v1/projects', {}, apiKey),
  });
}

// ─── Metrics hooks ───

export interface MetricsSummary {
  total_runs: number;
  error_rate: number;
  total_cost_usd: number;
  total_tokens: number;
  avg_latency_ms: number | null;
  p50_latency_ms: number | null;
  p95_latency_ms: number | null;
  p50_ttft_ms: number | null;
  p95_ttft_ms: number | null;
}

export interface TimeseriesPoint {
  bucket: string;
  run_count: number;
  total_cost_usd: number;
  avg_latency_ms: number | null;
  p95_latency_ms: number | null;
  model_provider: string | null;
  model_name: string | null;
}

export function useMetricsSummary(apiKey?: string, hours: number = 24) {
  return useQuery({
    queryKey: ['metrics-summary', apiKey, hours],
    queryFn: () => fetchApi<MetricsSummary>('/v1/metrics/summary?hours=' + hours, {}, apiKey),
    enabled: !!apiKey,
    refetchInterval: 30000, // Refresh every 30 seconds
  });
}

export function useMetricsTimeseries(apiKey?: string, days: number = 7) {
  return useQuery({
    queryKey: ['metrics-timeseries', apiKey, days],
    queryFn: () => fetchApi<TimeseriesPoint[]>('/v1/metrics/timeseries?days=' + days, {}, apiKey),
    enabled: !!apiKey,
    refetchInterval: 60000, // Refresh every minute
  });
}

// ─── Traces hooks ───

export interface Run {
  id: string;
  name: string | null;
  status: string;
  model_provider: string | null;
  model_name: string | null;
  latency_ms: number | null;
  ttft_ms: number | null;
  total_tokens: number | null;
  cost_usd: number | null;
  created_at: string;
  finished_at: string | null;
}

export interface Span {
  id: string;
  run_id: string;
  span_type: string;
  name: string | null;
  model: string | null;
  provider: string | null;
  tokens_in: number | null;
  tokens_out: number | null;
  latency_ms: number | null;
  ttft_ms: number | null;
  cost_usd: number | null;
  status: string;
  started_at: string | null;
  ended_at: string | null;
}

export function useTraces(apiKey?: string, limit: number = 50) {
  return useQuery({
    queryKey: ['traces', apiKey, limit],
    queryFn: () => fetchApi<Run[]>('/v1/runs?limit=' + limit, {}, apiKey),
    enabled: !!apiKey,
    refetchInterval: 10000, // Refresh every 10 seconds
  });
}

export function useRunDetail(runId: string | null, apiKey?: string) {
  return useQuery({
    queryKey: ['run', runId, apiKey],
    queryFn: () => fetchApi<Run>('/v1/runs/' + runId, {}, apiKey),
    enabled: !!apiKey && !!runId,
  });
}

export function useRunSpans(runId: string | null, apiKey?: string) {
  return useQuery({
    queryKey: ['run-spans', runId, apiKey],
    queryFn: () => fetchApi<Span[]>('/v1/runs/' + runId + '/spans', {}, apiKey),
    enabled: !!apiKey && !!runId,
  });
}

// ─── Eval hooks ───

export interface EvalRun {
  id: string;
  suite_name: string;
  status: string;
  created_at: string;
  finished_at: string | null;
}

export function useEvalRuns(apiKey?: string) {
  return useQuery({
    queryKey: ['eval-runs', apiKey],
    queryFn: () => fetchApi<EvalRun[]>('/v1/eval/runs', {}, apiKey),
    enabled: !!apiKey,
  });
}

// ─── Benchmark hooks ───

export interface Benchmark {
  id: string;
  status: string;
  created_at: string;
  finished_at: string | null;
}

export function useBenchmarks(apiKey?: string) {
  return useQuery({
    queryKey: ['benchmarks', apiKey],
    queryFn: () => fetchApi<Benchmark[]>('/v1/benchmarks', {}, apiKey),
    enabled: !!apiKey,
  });
}

// ─── Security hooks ───

export interface SecurityScan {
  id: string;
  suite_name: string;
  status: string;
  pass_rate: number | null;
  created_at: string;
}

export function useSecurityScans(apiKey?: string) {
  return useQuery({
    queryKey: ['security-scans', apiKey],
    queryFn: () => fetchApi<SecurityScan[]>('/v1/security/scans', {}, apiKey),
    enabled: !!apiKey,
  });
}

// ─── Alert hooks ───

export interface AlertRule {
  id: string;
  name: string;
  rule_type: string;
  threshold: number;
  window_minutes: number;
  enabled: boolean;
}

export interface AlertEvent {
  id: string;
  rule_id: string;
  message: string;
  value: number | null;
  acknowledged: boolean;
  created_at: string;
}

export function useAlertRules(apiKey?: string) {
  return useQuery({
    queryKey: ['alert-rules', apiKey],
    queryFn: () => fetchApi<AlertRule[]>('/v1/alerts/rules', {}, apiKey),
    enabled: !!apiKey,
  });
}

export function useAlertEvents(apiKey?: string) {
  return useQuery({
    queryKey: ['alert-events', apiKey],
    queryFn: () => fetchApi<AlertEvent[]>('/v1/alerts/events', {}, apiKey),
    enabled: !!apiKey,
    refetchInterval: 15000, // Refresh every 15 seconds for real-time alerts
  });
}

// ─── Mutation hooks ───

export function useTriggerEval() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { project_id: string; suite_name: string; api_key: string }) =>
      fetchApi<EvalRun>('/v1/eval/runs', {
        method: 'POST',
        body: JSON.stringify({ project_id: data.project_id, suite_name: data.suite_name }),
      }, data.api_key),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['eval-runs'] });
    },
  });
}

export function useTriggerBenchmark() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { project_id: string; models: Array<{ provider: string; model: string }>; api_key: string }) =>
      fetchApi<Benchmark>('/v1/benchmarks', {
        method: 'POST',
        body: JSON.stringify({ project_id: data.project_id, models: data.models }),
      }, data.api_key),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['benchmarks'] });
    },
  });
}

export function useAcknowledgeAlert() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { event_id: string; api_key: string }) =>
      fetchApi<{ status: string }>('/v1/alerts/events/' + data.event_id + '/acknowledge', {
        method: 'PATCH',
      }, data.api_key),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alert-events'] });
    },
  });
}
