/**
 * Types for agents feature
 */

export type {
  Agent,
  Service,
} from "../../../types/agent";
// Re-export from legacy types for now, will migrate gradually
export type {
  AvailableModel,
  ModelConfig,
  ProviderMetadata,
  ProviderStatus,
  ProviderType,
} from "../../../types/cleanProvider";

// Agent-specific types
export interface AgentConfigUpdate {
  serviceId: string;
  config: ModelConfig;
}

export interface ProviderOperation {
  provider: string;
  apiKey?: string;
  baseUrl?: string;
}

