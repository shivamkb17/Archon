/**
 * Agent Card Component
 *
 * Displays an agent/service with model configuration options
 * Styled to match the existing EnhancedProviderCard UI patterns
 */

import React, {
  useState,
  useEffect,
  useCallback,
  useRef,
  useMemo,
} from "react";
import {
  Settings2,
  AlertCircle,
  Check,
  ChevronDown,
  Zap,
  DollarSign,
  Activity,
  Clock,
  CheckCircle,
  XCircle,
  MoreVertical,
  Sliders,
  Edit3,
} from "lucide-react";
import { useToast } from "../../../contexts/ToastContext";
import type { AgentConfig } from "../../../types/agent";
import type {
  AvailableModel,
  ModelConfig,
  ServiceType,
} from "../../../types/cleanProvider";
import { Button } from "../../../components/ui/Button";
import { Badge } from "../../../components/ui/Badge";
import { ModelSelectionModal } from "./ModelSelectionModal";
import { useAgents } from "../hooks";

interface AgentCardProps {
  agent: AgentConfig;
  availableModels: AvailableModel[];
  currentConfig?: {
    model_string: string;
    temperature?: number;
    max_tokens?: number;
  };
}

// Valid ServiceType values for validation
const VALID_SERVICE_TYPES: ServiceType[] = [
  "document_agent",
  "rag_agent",
  "task_agent",
  "embeddings",
  "contextual_embedding",
  "source_summary",
  "code_summary",
  "code_analysis",
  "validation",
];

// Utility function to safely cast to ServiceType
const validateServiceType = (id: string): ServiceType => {
  if (VALID_SERVICE_TYPES.includes(id as ServiceType)) {
    return id as ServiceType;
  }
  console.warn(`Invalid service type: ${id}, defaulting to 'document_agent'`);
  return "document_agent";
};

export const AgentCard: React.FC<AgentCardProps> = React.memo(
  ({ agent, availableModels, currentConfig }) => {
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [selectedModel, setSelectedModel] = useState(
      currentConfig?.model_string || agent.defaultModel
    );
    const [temperature, setTemperature] = useState(
      currentConfig?.temperature || 0.7
    );
    const [maxTokens, setMaxTokens] = useState(
      currentConfig?.max_tokens || 2000
    );

    const { showToast } = useToast();
    const [isSaving, setIsSaving] = useState(false);
    const [healthStatus, setHealthStatus] = useState<
      "healthy" | "unhealthy" | "checking" | null
    >(null);

    const { handleConfigUpdate } = useAgents();
    const timeoutRef = useRef<NodeJS.Timeout | null>(null);

    // Sync local state with props when they change
    useEffect(() => {
      if (currentConfig) {
        setSelectedModel(currentConfig.model_string);
        if (currentConfig.temperature !== undefined) {
          setTemperature(currentConfig.temperature);
        }
        if (currentConfig.max_tokens !== undefined) {
          setMaxTokens(currentConfig.max_tokens);
        }
      }
    }, [currentConfig]);

    // Cleanup timeouts on unmount
    useEffect(() => {
      return () => {
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current);
        }
      };
    }, []);

    // Filter models based on type (LLM vs embedding) - memoized for performance
    const compatibleModels = useMemo(() => {
      return availableModels.filter((m) => {
        if (agent.modelType === "embedding") {
          // Use the is_embedding flag if available, otherwise fall back to string check
          return m.is_embedding || m.model_string.includes("embedding");
        }
        // For LLM models, exclude embedding models
        return !m.is_embedding && !m.model_string.includes("embedding");
      });
    }, [availableModels, agent.modelType]);

    const handleModelSelect = async (
      model: AvailableModel,
      config?: { temperature?: number; maxTokens?: number }
    ) => {
      // Close modal immediately for better UX
      setIsModalOpen(false);

      // Store current state for potential rollback
      const previousState = {
        selectedModel,
        temperature,
        maxTokens,
      };

      // Optimistically update the UI
      const newConfig: ModelConfig = {
        service_name: validateServiceType(agent.id),
        model_string: model.model_string,
        temperature: config?.temperature ?? temperature,
        max_tokens: config?.maxTokens ?? maxTokens,
      };

      // Update local state immediately
      setSelectedModel(model.model_string);
      if (config?.temperature !== undefined) setTemperature(config.temperature);
      if (config?.maxTokens !== undefined) setMaxTokens(config.maxTokens);

      // Show saving status
      setIsSaving(true);
      setHealthStatus("checking");

      try {
        // Use the optimistic update hook
        await handleConfigUpdate(validateServiceType(agent.id), newConfig);

        setHealthStatus("healthy");
        showToast(
          `${agent.name} configuration updated successfully`,
          "success"
        );

        // Clear status after success
        timeoutRef.current = setTimeout(() => {
          setHealthStatus(null);
          timeoutRef.current = null;
        }, 1500);
      } catch (error) {
        console.error("Failed to save agent config:", error);
        setHealthStatus("unhealthy");

        // Rollback to previous state
        setSelectedModel(previousState.selectedModel);
        setTemperature(previousState.temperature);
        setMaxTokens(previousState.maxTokens);

        showToast(
          `Failed to update ${agent.name} configuration. Please try again.`,
          "error"
        );

        // Clear error status after delay
        timeoutRef.current = setTimeout(() => {
          setHealthStatus(null);
          timeoutRef.current = null;
        }, 3000);
      } finally {
        setIsSaving(false);
      }
    };

    // Memoize computed values for performance
    const isModelAvailable = useMemo(() => {
      return compatibleModels.some((m) => m.model_string === selectedModel);
    }, [compatibleModels, selectedModel]);

    const isActive = useMemo(() => {
      return currentConfig && isModelAvailable;
    }, [currentConfig, isModelAvailable]);

    // Memoize cost indicator to prevent unnecessary re-renders
    const costIndicator = useMemo(() => {
      const colors = {
        high: "text-red-400",
        medium: "text-yellow-400",
        low: "text-emerald-400",
      };
      const labels = {
        high: "$$$",
        medium: "$$",
        low: "$",
      };
      return (
        <span
          className={`text-xs font-mono ${
            colors[agent.costProfile as keyof typeof colors] || "text-gray-400"
          }`}
        >
          {labels[agent.costProfile as keyof typeof labels] || "$"}
        </span>
      );
    }, [agent.costProfile]);

    // Memoize status icon for better performance and accessibility
    const statusIcon = useMemo(() => {
      if (healthStatus === "checking") {
        return (
          <Clock
            className="w-3.5 h-3.5 text-yellow-400 animate-spin"
            aria-label="Saving configuration"
          />
        );
      }
      if (healthStatus === "healthy") {
        return (
          <CheckCircle
            className="w-3.5 h-3.5 text-emerald-400"
            aria-label="Configuration saved successfully"
          />
        );
      }
      if (healthStatus === "unhealthy") {
        return (
          <XCircle
            className="w-3.5 h-3.5 text-red-400"
            aria-label="Configuration save failed"
          />
        );
      }
      if (isModelAvailable) {
        return (
          <div
            className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"
            aria-label="Model available"
          />
        );
      }
      return (
        <div
          className="w-2 h-2 bg-gray-600 rounded-full"
          aria-label="Model unavailable"
        />
      );
    }, [healthStatus, isModelAvailable]);

    return (
      <div
        className={`relative rounded-xl overflow-hidden transition-all duration-300 hover:scale-[1.02] hover:shadow-2xl ${
          isActive
            ? "ring-1 ring-purple-500/30 shadow-lg shadow-purple-500/10"
            : ""
        }`}
        style={{
          background: isActive
            ? "linear-gradient(135deg, rgba(30, 25, 40, 0.9) 0%, rgba(20, 20, 30, 0.95) 100%)"
            : "linear-gradient(135deg, rgba(20, 20, 30, 0.8) 0%, rgba(15, 15, 25, 0.9) 100%)",
          backdropFilter: "blur(10px)",
          animation: "fadeInUp 0.5s ease-out",
        }}
        role="article"
        aria-labelledby={`agent-${agent.id}-title`}
        aria-describedby={`agent-${agent.id}-description`}
      >
        {/* Gradient border */}
        <div
          className="absolute inset-0 rounded-xl p-[1px] transition-all duration-300 pointer-events-none"
          style={{
            background: isActive
              ? "linear-gradient(180deg, rgba(168, 85, 247, 0.5) 0%, rgba(7, 180, 130, 0.3) 100%)"
              : "linear-gradient(180deg, rgba(168, 85, 247, 0.3) 0%, rgba(7, 180, 130, 0.1) 100%)",
          }}
        >
          <div
            className="w-full h-full rounded-xl"
            style={{
              background: isActive
                ? "linear-gradient(135deg, rgba(30, 25, 40, 0.9) 0%, rgba(20, 20, 30, 0.95) 100%)"
                : "linear-gradient(135deg, rgba(20, 20, 30, 0.8) 0%, rgba(15, 15, 25, 0.9) 100%)",
            }}
          />
        </div>

        {/* Status Bar for Active Agents or Saving */}
        {(isActive || isSaving) && (
          <div
            className="absolute top-0 left-0 right-0 h-[3px] animate-shimmer transition-all duration-500 z-10"
            style={{
              backgroundImage: isSaving
                ? "linear-gradient(90deg, transparent 0%, rgba(251, 191, 36, 1) 25%, rgba(251, 146, 60, 1) 75%, transparent 100%)"
                : "linear-gradient(90deg, transparent 0%, rgba(168, 85, 247, 1) 25%, rgba(7, 180, 130, 1) 75%, transparent 100%)",
              backgroundSize: "200% 100%",
            }}
          />
        )}

        {/* Content */}
        <div className="relative p-4">
          {/* Header */}
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              {/* Agent Icon */}
              <div className="w-10 h-10 rounded-lg bg-zinc-800/50 border border-zinc-700/50 flex items-center justify-center">
                <span className="text-xl">{agent.icon}</span>
              </div>

              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <h3
                    className="text-sm font-light text-white"
                    id={`agent-${agent.id}-title`}
                  >
                    {agent.name}
                  </h3>
                  <Badge
                    variant={
                      agent.category === "agent" ? "primary" : "secondary"
                    }
                    className="text-xs px-1.5 py-0.5"
                  >
                    {agent.category}
                  </Badge>
                  {costIndicator}
                </div>
                <p
                  className="text-xs text-gray-500"
                  id={`agent-${agent.id}-description`}
                >
                  {agent.description}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">{statusIcon}</div>
          </div>

          {/* Current Configuration Summary */}
          <div className="mt-3 pt-3 border-t border-zinc-800/50">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4 text-xs text-gray-500">
                <span className="flex items-center gap-1">
                  <Zap className="w-3 h-3" />
                  {selectedModel
                    ? selectedModel.split(":")[1] || selectedModel
                    : "No model selected"}
                </span>
                {agent.supportsTemperature &&
                  currentConfig?.temperature !== undefined && (
                    <span className="flex items-center gap-1">
                      <Sliders className="w-3 h-3" />
                      {currentConfig.temperature}
                    </span>
                  )}
                {agent.supportsMaxTokens &&
                  currentConfig?.max_tokens !== undefined && (
                    <span className="flex items-center gap-1">
                      <Activity className="w-3 h-3" />
                      {currentConfig.max_tokens}
                    </span>
                  )}
              </div>
              <Button
                onClick={() => setIsModalOpen(true)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    setIsModalOpen(true);
                  }
                }}
                variant="ghost"
                size="sm"
                className="text-xs flex items-center gap-1 focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 focus:ring-offset-zinc-900"
                disabled={isSaving}
                aria-label={
                  isSaving
                    ? `Saving ${agent.name} configuration`
                    : `Configure ${agent.name} settings`
                }
                aria-describedby={isSaving ? "saving-status" : undefined}
              >
                {isSaving ? (
                  <>
                    <Clock
                      className="w-3 h-3 animate-spin"
                      aria-hidden="true"
                    />
                    <span id="saving-status">Saving...</span>
                  </>
                ) : (
                  <>
                    <Edit3 className="w-3 h-3" aria-hidden="true" />
                    Configure
                  </>
                )}
              </Button>
            </div>

            {!isModelAvailable && selectedModel && (
              <p
                className="mt-2 text-xs text-yellow-500 flex items-center gap-1"
                role="alert"
                aria-live="polite"
              >
                <AlertCircle className="w-3 h-3" aria-hidden="true" />
                This model requires an API key to be configured. Please check
                your provider settings.
              </p>
            )}
          </div>

          {/* Model Selection Modal */}
          <ModelSelectionModal
            isOpen={isModalOpen}
            onClose={() => setIsModalOpen(false)}
            models={compatibleModels}
            currentModel={selectedModel}
            onSelectModel={handleModelSelect}
            agent={agent}
            showAdvancedSettings={true}
          />
        </div>
      </div>
    );
  }
);

AgentCard.displayName = "AgentCard";
