/**
 * TanStack Query mutations for agent operations
 */

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useToast } from "../../../contexts/ToastContext";
import { agentApi } from "../services/agentService";
import type { AgentConfigUpdate, ProviderOperation, ModelConfig } from "../types";
import { agentKeys, modelKeys, providerKeys } from "../utils/queryKeys";

/**
 * Hook for updating agent model configuration with optimistic updates
 */
export const useUpdateAgentConfig = () => {
  const queryClient = useQueryClient();
  const { showToast } = useToast();

  return useMutation({
    mutationFn: async ({ serviceId, config }: AgentConfigUpdate) => {
      return agentApi.updateAgentConfig(serviceId, config);
    },
    onMutate: async ({ serviceId, config }) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: agentKeys.configs() });

      // Snapshot the previous value
      const previousConfigs = queryClient.getQueryData(agentKeys.configs());

      // Optimistically update the cache
      queryClient.setQueryData(agentKeys.configs(), (old: Record<string, ModelConfig> | undefined) => ({
        ...old,
        [serviceId]: config,
      }));

      return { previousConfigs };
    },
    onError: (err, variables, context) => {
      // Rollback on error
      if (context?.previousConfigs) {
        queryClient.setQueryData(agentKeys.configs(), context.previousConfigs);
      }
      showToast(`Failed to update ${variables.serviceId} configuration`, "error");
    },
    onSuccess: (data, variables) => {
      showToast(`${variables.serviceId} configuration updated successfully`, "success");
    },
    onSettled: () => {
      // Always refetch to ensure consistency
      queryClient.invalidateQueries({ queryKey: agentKeys.configs() });
    },
  });
};

/**
 * Hook for adding a provider (API key + models)
 */
export const useAddProvider = () => {
  const queryClient = useQueryClient();
  const { showToast } = useToast();

  return useMutation({
    mutationFn: async ({ provider, apiKey, baseUrl }: ProviderOperation) => {
      if (!apiKey) throw new Error("API key is required");
      return agentApi.setApiKey(provider, apiKey, baseUrl);
    },
    onSuccess: (data, variables) => {
      showToast(`${variables.provider} added successfully`, "success");

      // Invalidate related queries to trigger refetch
      queryClient.invalidateQueries({ queryKey: providerKeys.apiKeys() });
      queryClient.invalidateQueries({ queryKey: modelKeys.available() });
      queryClient.invalidateQueries({ queryKey: providerKeys.metadata() });
    },
    onError: (err, variables) => {
      showToast(`Failed to add ${variables.provider}`, "error");
    },
  });
};

/**
 * Hook for removing a provider
 */
export const useRemoveProvider = () => {
  const queryClient = useQueryClient();
  const { showToast } = useToast();

  return useMutation({
    mutationFn: async ({ provider }: ProviderOperation) => {
      return agentApi.removeApiKey(provider);
    },
    onMutate: async ({ provider }) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: providerKeys.apiKeys() });

      // Snapshot the previous value
      const previousProviders = queryClient.getQueryData(providerKeys.apiKeys());

      // Optimistically remove from cache
      queryClient.setQueryData(providerKeys.apiKeys(), (old: string[] | undefined) =>
        old ? old.filter((p) => p !== provider) : [],
      );

      return { previousProviders };
    },
    onError: (err, variables, context) => {
      // Rollback on error
      if (context?.previousProviders) {
        queryClient.setQueryData(providerKeys.apiKeys(), context.previousProviders);
      }
      showToast(`Failed to remove ${variables.provider}`, "error");
    },
    onSuccess: (data, variables) => {
      showToast(`${variables.provider} removed successfully`, "success");

      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: modelKeys.available() });
      queryClient.invalidateQueries({ queryKey: providerKeys.metadata() });
    },
  });
};

/**
 * Hook for testing provider API key
 */
export const useTestProvider = () => {
  const { showToast } = useToast();

  return useMutation({
    mutationFn: async ({ provider }: ProviderOperation) => {
      return agentApi.testApiKey(provider);
    },
    onSuccess: (data, variables) => {
      if (data.configured && data.status === "active") {
        showToast(`${variables.provider} connection successful`, "success");
      } else {
        showToast(`${variables.provider} connection failed`, "error");
      }
    },
    onError: (err, variables) => {
      showToast(`Failed to test ${variables.provider}`, "error");
    },
  });
};
