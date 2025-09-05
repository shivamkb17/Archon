/**
 * Query keys factory for agents feature
 * Follows TanStack Query best practices for key organization
 */

export const agentKeys = {
  all: ["agents"] as const,
  lists: () => [...agentKeys.all, "list"] as const,
  configs: () => [...agentKeys.all, "configs"] as const,
  config: (serviceId: string) => [...agentKeys.all, "config", serviceId] as const,
};

export const modelKeys = {
  all: ["models"] as const,
  available: () => [...modelKeys.all, "available"] as const,
};

export const providerKeys = {
  all: ["providers"] as const,
  list: () => [...providerKeys.all, "list"] as const,
  metadata: () => [...providerKeys.all, "metadata"] as const,
  apiKeys: () => [...providerKeys.all, "api-keys"] as const,
};

export const serviceKeys = {
  all: ["services"] as const,
  agents: () => [...serviceKeys.all, "agents"] as const,
  backend: () => [...serviceKeys.all, "backend"] as const,
  registry: () => [...serviceKeys.all, "registry"] as const,
};
