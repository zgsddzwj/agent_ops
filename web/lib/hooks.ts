"use client";

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchApi } from './api';

// ─── Project hooks ───

export function useProjects(apiKey?: string) {
  return useQuery({
    queryKey: ['projects', apiKey],
    queryFn: () => fetchApi<Array<{ id: string; name: string }>>('/v1/projects', {}, apiKey),
  });
}

// ─── Metrics hooks ───

export function useMetricsSummary(apiKey?: string, hours: number = 24) {
  return useQuery({
    queryKey: ['metrics-summary', apiKey, hours],
    queryFn: () => fetchApi('/v1/metrics/summary?hours=' + hours, {}, apiKey),
    enabled: !!apiKey,
    refetchInterval: 30000, // Refresh every 30 seconds
  });
}

export function useMetricsTimeseries(apiKey?: string, days: number = 7) {
  return useQuery({
    queryKey: ['metrics-timeseries', apiKey, days],
    queryFn: () => fetchApi('/v1/metrics/timeseries?days=' + days, {}, apiKey),
    enabled: !!apiKey,
    refetchInterval: 60000, // Refresh every minute
  });
}

// ─── Traces hooks ───

export function useTraces(apiKey?: string, limit: number = 50) {
  return useQuery({
    queryKey: ['traces', apiKey, limit],
    queryFn: () => fetchApi('/v1/runs?limit=' + limit, {}, apiKey),
    enabled: !!apiKey,
    refetchInterval: 10000, // Refresh every 10 seconds
  });
}

export function useRunDetail(runId: string | null, apiKey?: string) {
  return useQuery({
    queryKey: ['run', runId, apiKey],
    queryFn: () => fetchApi('/v1/runs/' + runId, {}, apiKey),
    enabled: !!apiKey && !!runId,
  });
}

export function useRunSpans(runId: string | null, apiKey?: string) {
  return useQuery({
    queryKey: ['run-spans', runId, apiKey],
    queryFn: () => fetchApi('/v1/runs/' + runId + '/spans', {}, apiKey),
    enabled: !!apiKey && !!runId,
  });
}

// ─── Eval hooks ───

export function useEvalRuns(apiKey?: string) {
  return useQuery({
    queryKey: ['eval-runs', apiKey],
    queryFn: () => fetchApi('/v1/eval/runs', {}, apiKey),
    enabled: !!apiKey,
  });
}

// ─── Benchmark hooks ───

export function useBenchmarks(apiKey?: string) {
  return useQuery({
    queryKey: ['benchmarks', apiKey],
    queryFn: () => fetchApi('/v1/benchmarks', {}, apiKey),
    enabled: !!apiKey,
  });
}

// ─── Security hooks ───

export function useSecurityScans(apiKey?: string) {
  return useQuery({
    queryKey: ['security-scans', apiKey],
    queryFn: () => fetchApi('/v1/security/scans', {}, apiKey),
    enabled: !!apiKey,
  });
}

// ─── Alert hooks ───

export function useAlertRules(apiKey?: string) {
  return useQuery({
    queryKey: ['alert-rules', apiKey],
    queryFn: () => fetchApi('/v1/alerts/rules', {}, apiKey),
    enabled: !!apiKey,
  });
}

export function useAlertEvents(apiKey?: string) {
  return useQuery({
    queryKey: ['alert-events', apiKey],
    queryFn: () => fetchApi('/v1/alerts/events', {}, apiKey),
    enabled: !!apiKey,
    refetchInterval: 15000, // Refresh every 15 seconds for real-time alerts
  });
}

// ─── Mutation hooks ───

export function useTriggerEval() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { project_id: string; suite_name: string; api_key: string }) =>
      fetchApi('/v1/eval/runs', {
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
    mutationFn: (data: { project_id: string; models: any[]; api_key: string }) =>
      fetchApi('/v1/benchmarks', {
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
      fetchApi('/v1/alerts/events/' + data.event_id + '/acknowledge', {
        method: 'PATCH',
      }, data.api_key),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alert-events'] });
    },
  });
}
