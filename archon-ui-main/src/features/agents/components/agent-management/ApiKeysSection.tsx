/**
 * API Keys Section Component
 * 
 * Extracted from AgentsPage to reduce complexity
 * Handles the collapsible API key configuration section
 */

import React from "react";
import { Key } from "lucide-react";
import { CollapsibleSection } from "../common";
import { ProviderSettings } from "../provider-management/ProviderSettings";
import type { AvailableModel } from "../../../../types/cleanProvider";

export interface ApiKeysSectionProps {
  availableModels: AvailableModel[];
  hasModels: boolean;
  showApiKeys: boolean;
  isLoading: boolean;
  onToggleApiKeys: (show: boolean) => void;
  onProviderAdded: () => void;
}

export const ApiKeysSection: React.FC<ApiKeysSectionProps> = ({
  availableModels,
  hasModels,
  showApiKeys,
  isLoading,
  onToggleApiKeys,
  onProviderAdded,
}) => {
  // Auto-expand if no models are available and not loading
  const shouldAutoExpand = !hasModels && !isLoading;

  // Generate subtitle based on current state
  const getSubtitle = () => {
    if (hasModels) {
      const providerCount = new Set(availableModels.map((m) => m.provider)).size;
      return (
        <>
          <span className="text-emerald-400">{providerCount}</span>
          {" providers active • "}
          <span className="text-blue-400">{availableModels.length}</span>
          {" models available"}
        </>
      );
    }
    
    return (
      <span className="text-yellow-400">
        ⚠️ No providers configured - add API keys to get started
      </span>
    );
  };

  // Setup Required badge for when no models are configured
  const badge = !showApiKeys && !hasModels ? (
    <span className="px-2 py-0.5 text-xs rounded bg-yellow-500/10 text-yellow-400 border border-yellow-500/20 animate-pulse">
      Setup Required
    </span>
  ) : null;

  return (
    <CollapsibleSection
      title="API Key Configuration"
      subtitle={<span className="text-xs text-gray-500 mt-0.5">{getSubtitle()}</span>}
      icon={<Key className="w-5 h-5" />}
      isExpanded={showApiKeys || shouldAutoExpand}
      onToggle={() => onToggleApiKeys(!showApiKeys)}
      badge={badge}
      autoExpandOnEmpty={shouldAutoExpand}
      maxContentHeight="600px"
      theme={hasModels ? "active" : "inactive"}
    >
      <ProviderSettings onProviderAdded={onProviderAdded} />
    </CollapsibleSection>
  );
};