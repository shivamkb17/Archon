/**
 * Agents Configuration Page - TanStack Query Version
 *
 * Agent-centric provider configuration using TanStack Query for data management
 * Refactored to use shared components and reduce complexity
 */

import React, { useState } from "react";
import { AgentCard } from "./AgentCard";
import { ApiKeysSection } from "./ApiKeysSection";
import { NoModelsWarning } from "./NoModelsWarning";
import { AgentTabNavigation } from "./AgentTabNavigation";
import { useAgents } from "../../hooks";
import { AgentsPageHeader } from "../common/AgentsPageHeader";
import { AgentsPageError } from "../ui-feedback/AgentsPageError";

export const AgentsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<"agents" | "services">("agents");
  const [showApiKeys, setShowApiKeys] = useState(false);

  const {
    availableModels,
    agentConfigs,
    agents,
    backendServices,
    isLoading,
    hasModels,
    servicesError,
    handleProviderAdded,
  } = useAgents();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 dark:border-white"></div>
      </div>
    );
  }

  // Show error if services failed to load
  if (servicesError) {
    return <AgentsPageError servicesError={servicesError} />;
  }

  // Get current items based on active tab
  const currentItems = activeTab === "agents" ? agents : backendServices;

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      <AgentsPageHeader />

      {/* API Keys Section */}
      <ApiKeysSection
        availableModels={availableModels}
        hasModels={hasModels}
        showApiKeys={showApiKeys}
        isLoading={isLoading}
        onToggleApiKeys={setShowApiKeys}
        onProviderAdded={handleProviderAdded}
      />

      {/* No Models Warning */}
      <NoModelsWarning 
        isVisible={!hasModels && !showApiKeys}
        className="mb-8"
      />

      {/* Tab Navigation */}
      <AgentTabNavigation
        activeTab={activeTab}
        onTabChange={setActiveTab}
        agents={agents}
        backendServices={backendServices}
      />

      {/* Agent/Service Cards */}
      <div className="space-y-4 mb-8">
        {currentItems.map((agent) => (
          <AgentCard
            key={agent.id}
            agent={agent}
            availableModels={availableModels}
            currentConfig={agentConfigs[agent.id]}
          />
        ))}
      </div>
    </div>
  );
};