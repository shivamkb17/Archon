/**
 * Agent Model Panel Component
 *
 * Displays the current model configuration summary for an agent
 */

import React from "react";
import { Zap, Sliders, Activity, AlertCircle } from "lucide-react";
import type { AgentConfig } from "../../../../types/agent";

interface AgentModelPanelProps {
  agent: AgentConfig;
  selectedModel: string;
  currentConfig?: {
    model_string: string;
    temperature?: number;
    max_tokens?: number;
  };
  isModelAvailable: boolean;
}

export const AgentModelPanel: React.FC<AgentModelPanelProps> = ({
  agent,
  selectedModel,
  currentConfig,
  isModelAvailable,
}) => {
  return (
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
      </div>

      {!isModelAvailable && selectedModel && (
        <p
          className="mt-2 text-xs text-yellow-500 flex items-center gap-1"
          role="alert"
          aria-live="polite"
        >
          <AlertCircle className="w-3 h-3" aria-hidden="true" />
          This model requires an API key to be configured. Please check your
          provider settings.
        </p>
      )}
    </div>
  );
};
