'use client';

import { useState, useEffect, useCallback } from 'react';
import api from '@/lib/api';

interface UseApiState<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
}

interface UseApiOptions {
  immediate?: boolean;
}

export function useApi<T>(
  fetcher: () => Promise<T>,
  deps: unknown[] = [],
  options: UseApiOptions = { immediate: true }
) {
  const [state, setState] = useState<UseApiState<T>>({
    data: null,
    loading: options.immediate ?? true,
    error: null,
  });

  const execute = useCallback(async () => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const data = await fetcher();
      setState({ data, loading: false, error: null });
      return data;
    } catch (error) {
      setState({ data: null, loading: false, error: error as Error });
      throw error;
    }
  }, [fetcher]);

  useEffect(() => {
    if (options.immediate) {
      execute();
    }
  }, deps);

  return { ...state, refetch: execute };
}

// Specific hooks for common data fetching patterns

export function useEntities(params?: Parameters<typeof api.getEntities>[0]) {
  return useApi(
    () => api.getEntities(params),
    [JSON.stringify(params)]
  );
}

export function useEntity(id: string) {
  return useApi(
    () => api.getEntity(id),
    [id]
  );
}

export function useEntityRelationships(id: string, depth = 2) {
  return useApi(
    () => api.getEntityRelationships(id, depth),
    [id, depth]
  );
}

export function useTransactions(params?: Parameters<typeof api.getTransactions>[0]) {
  return useApi(
    () => api.getTransactions(params),
    [JSON.stringify(params)]
  );
}

export function useTransactionStats(days = 30) {
  return useApi(
    () => api.getTransactionStats(days),
    [days]
  );
}

export function useAlerts(params?: Parameters<typeof api.getAlerts>[0]) {
  return useApi(
    () => api.getAlerts(params),
    [JSON.stringify(params)]
  );
}

export function useAlertDashboard() {
  return useApi(() => api.getAlertDashboard(), []);
}

export function useCases(params?: Parameters<typeof api.getCases>[0]) {
  return useApi(
    () => api.getCases(params),
    [JSON.stringify(params)]
  );
}

export function useCaseDashboard() {
  return useApi(() => api.getCaseDashboard(), []);
}

export function useRiskDistribution() {
  return useApi(() => api.getRiskDistribution(), []);
}

export function useTransactionTrends(days = 30) {
  return useApi(
    () => api.getTransactionTrends(days),
    [days]
  );
}

export function useHighRiskEntities(limit = 20) {
  return useApi(
    () => api.getHighRiskEntities(limit),
    [limit]
  );
}

export function useEntityNetwork(entityId: string, depth = 2) {
  return useApi(
    () => api.getEntityNetwork(entityId, depth),
    [entityId, depth]
  );
}

export function useGlobalSearch(query: string, enabled = true) {
  return useApi(
    () => api.searchGlobal(query),
    [query],
    { immediate: enabled && query.length >= 2 }
  );
}

