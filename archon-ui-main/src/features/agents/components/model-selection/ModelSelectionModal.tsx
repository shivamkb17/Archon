/**
 * Model Selection Modal Component
 *
 * Modal for selecting AI models with rich filtering and search capabilities
 */

import React, { useState, useMemo, useEffect, useRef } from "react";
import { Search, X, Brain, Sparkles, Zap, Filter } from "lucide-react";
import { Modal } from "../../../../components/ui/Modal";
import { Button } from "../../../../components/ui/Button";
import type { AvailableModel } from "../../../../types/cleanProvider";
import type { AgentConfig } from "../../../../types/agent";
import {
  getProviderInfo,
  filterAndSortModels,
  groupModelsByProvider,
  getUniqueProviders,
  getUniqueCostTiers,
} from "./modelSelectionUtils";
import { ModelCard } from "./ModelCard";
import { AdvancedSettings } from "./AdvancedSettings";

interface ModelSelectionModalProps {
  isOpen: boolean;
  onClose: () => void;
  models: AvailableModel[];
  currentModel?: string;
  onSelectModel: (
    model: AvailableModel,
    config?: {
      temperature?: number;
      maxTokens?: number;
    }
  ) => void;
  agent?: AgentConfig;
  showAdvancedSettings?: boolean;
}

export const ModelSelectionModal: React.FC<ModelSelectionModalProps> = ({
  isOpen,
  onClose,
  models,
  currentModel,
  onSelectModel,
  agent,
  showAdvancedSettings = true,
}) => {
  const [searchQuery, setSearchQuery] = useState("");
  const [filterCostTier, setFilterCostTier] = useState<string>("all");
  const [filterProvider, setFilterProvider] = useState<string>("all");
  const [selectedModel, setSelectedModel] = useState<AvailableModel | null>(
    null
  );
  const [showSettings, setShowSettings] = useState(false);
  const [temperature, setTemperature] = useState(0.7);
  const [maxTokens, setMaxTokens] = useState(2000);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Reset state when modal opens
  useEffect(() => {
    if (isOpen) {
      setSearchQuery("");
      setFilterCostTier("all");
      setFilterProvider("all");
      setSelectedModel(null);
      setShowSettings(false);

      // Find and set current model
      const current = models.find((m) => m.model_string === currentModel);
      if (current) {
        setSelectedModel(current);
      }

      // Focus search input
      setTimeout(() => {
        searchInputRef.current?.focus();
      }, 100);
    }
  }, [isOpen, currentModel, models]);

  // Get unique providers and cost tiers
  const uniqueProviders = useMemo(() => getUniqueProviders(models), [models]);
  const uniqueCostTiers = useMemo(() => getUniqueCostTiers(models), [models]);

  // Filter models using utility function
  const filteredModels = useMemo(
    () =>
      filterAndSortModels(
        models,
        searchQuery,
        filterProvider,
        filterCostTier,
        agent
      ),
    [models, searchQuery, filterProvider, filterCostTier, agent]
  );

  // Group models by provider using utility function
  const groupedModels = useMemo(
    () => groupModelsByProvider(filteredModels),
    [filteredModels]
  );

  // Handle model selection
  const handleSelectModel = () => {
    if (selectedModel) {
      const config =
        showSettings && showAdvancedSettings
          ? {
              temperature: agent?.supportsTemperature ? temperature : undefined,
              maxTokens: agent?.supportsMaxTokens ? maxTokens : undefined,
            }
          : undefined;

      onSelectModel(selectedModel, config);
      onClose();
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={agent ? `Select Model for ${agent.name}` : "Select AI Model"}
      size="xl"
      className="max-h-[90vh]"
    >
      <div className="flex flex-col h-[75vh]">
        {/* Sticky Search and Filters */}
        <div className="sticky top-0 z-10 bg-zinc-900 pb-3 mb-3 border-b border-zinc-700">
          <div className="space-y-3">
            {/* Search Bar */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                ref={searchInputRef}
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search models..."
                className="w-full pl-10 pr-10 py-2 text-sm bg-zinc-800 text-white rounded-lg focus:outline-none focus:ring-1 focus:ring-purple-500"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery("")}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white"
                  aria-label="Clear search query"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>

            {/* Filters */}
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-gray-500" />

              {uniqueProviders.length > 1 && (
                <select
                  value={filterProvider}
                  onChange={(e) => setFilterProvider(e.target.value)}
                  className="px-2 py-1 text-xs bg-zinc-700 text-white rounded border border-zinc-600 focus:outline-none focus:ring-1 focus:ring-purple-500"
                  aria-label="Filter by provider"
                >
                  <option value="all">All Providers</option>
                  {uniqueProviders.map((provider) => (
                    <option key={provider} value={provider}>
                      {getProviderInfo(provider).name}
                    </option>
                  ))}
                </select>
              )}

              {uniqueCostTiers.length > 1 && (
                <select
                  value={filterCostTier}
                  onChange={(e) => setFilterCostTier(e.target.value)}
                  className="px-2 py-1 text-xs bg-zinc-700 text-white rounded border border-zinc-600 focus:outline-none focus:ring-1 focus:ring-purple-500"
                  aria-label="Filter by cost tier"
                >
                  <option value="all">All Costs</option>
                  {uniqueCostTiers.map((tier) => (
                    <option key={tier || "unknown"} value={tier || ""}>
                      {tier || "Unknown"}
                    </option>
                  ))}
                </select>
              )}

              <span className="ml-auto text-xs text-gray-500">
                {filteredModels.length} models available
              </span>
            </div>
          </div>
        </div>

        {/* Models Grid - Scrollable */}
        <div
          className="flex-1 overflow-y-auto pr-2"
          style={{ scrollbarGutter: "stable" }}
        >
          {filteredModels.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {Object.entries(groupedModels).map(
                ([provider, providerModels]) => (
                  <React.Fragment key={provider}>
                    {/* Provider Header */}
                    <div className="col-span-full flex items-center gap-2 mb-2 mt-4 first:mt-0">
                      <span className="text-lg">
                        {getProviderInfo(provider).icon}
                      </span>
                      <span
                        className={`text-sm font-medium ${
                          getProviderInfo(provider).color
                        }`}
                      >
                        {getProviderInfo(provider).name}
                      </span>
                      <div className="flex-1 h-px bg-zinc-800"></div>
                    </div>

                    {/* Provider Models */}
                    {providerModels.map((model) => (
                      <ModelCard
                        key={model.model_string}
                        model={model}
                        isSelected={
                          selectedModel?.model_string === model.model_string
                        }
                        onSelect={setSelectedModel}
                      />
                    ))}
                  </React.Fragment>
                )
              )}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Brain className="w-12 h-12 text-gray-600 mb-3" />
              <p className="text-gray-400 mb-2">No models found</p>
              <button
                onClick={() => {
                  setSearchQuery("");
                  setFilterCostTier("all");
                  setFilterProvider("all");
                }}
                className="text-xs text-purple-400 hover:text-purple-300"
              >
                Clear filters
              </button>
            </div>
          )}
        </div>

        {/* Advanced Settings */}
        {showAdvancedSettings && selectedModel && agent && (
          <AdvancedSettings
            agent={agent}
            temperature={temperature}
            maxTokens={maxTokens}
            onTemperatureChange={setTemperature}
            onMaxTokensChange={setMaxTokens}
            isExpanded={showSettings}
            onToggleExpanded={() => setShowSettings(!showSettings)}
          />
        )}

        {/* Footer Actions */}
        <div className="flex justify-between items-center mt-6 pt-4 border-t border-zinc-700">
          <div className="flex items-center gap-3 text-xs text-gray-500">
            {uniqueCostTiers.includes("free") && (
              <span className="flex items-center gap-1">
                <Sparkles className="w-3 h-3 text-emerald-400" />
                {
                  filteredModels.filter((m) => m.cost_tier === "free").length
                }{" "}
                free
              </span>
            )}
            <span className="flex items-center gap-1">
              <Zap className="w-3 h-3 text-yellow-400" />
              {uniqueProviders.length} providers
            </span>
          </div>

          <div className="flex gap-2">
            <Button onClick={onClose} variant="ghost" size="sm">
              Cancel
            </Button>
            <Button
              onClick={handleSelectModel}
              variant="primary"
              size="sm"
              disabled={
                !selectedModel || (selectedModel && !selectedModel.has_api_key)
              }
            >
              {selectedModel && !selectedModel.has_api_key
                ? "No API Key"
                : "Select Model"}
            </Button>
          </div>
        </div>
      </div>
    </Modal>
  );
};
