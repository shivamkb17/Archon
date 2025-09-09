/**
 * Agent Service API Layer
 * Clean interface for agent-related operations using TanStack Query
 */

import type { ModelConfig } from "../types";

// For now, re-export from legacy service - will migrate gradually
export { cleanProviderService as agentService } from "../../../services/cleanProviderService";

// Specific API functions that will be used by TanStack Query
export const agentApi = {
  // Models
  getAvailableModels: () => cleanProviderService.getAvailableModels(),

  // Agent configs
  getAllAgentConfigs: () => cleanProviderService.getAllAgentConfigs(),
  getAgentConfig: (serviceId: string) => cleanProviderService.getModelConfig(serviceId),
  updateAgentConfig: (serviceId: string, config: ModelConfig) => 
    cleanProviderService.updateAgentConfig(
      serviceId, 
      config.model_string, 
      { 
        temperature: config.temperature, 
        max_tokens: config.max_tokens 
      }
    ),

  // Providers
  getActiveProviders: () => cleanProviderService.getActiveProviders(),
  getProvidersMetadata: () => cleanProviderService.getProvidersMetadata(),
  getAllProviders: () => cleanProviderService.getAllProviders(),

  // API Keys
  setApiKey: (provider: string, apiKey: string, baseUrl?: string) =>
    cleanProviderService.setApiKey(provider, apiKey, baseUrl),
  removeApiKey: (provider: string) => cleanProviderService.deactivateApiKey(provider),
  testApiKey: (provider: string) => cleanProviderService.testApiKey(provider),
};

// Import the service for backward compatibility
import { cleanProviderService } from "../../../services/cleanProviderService";
