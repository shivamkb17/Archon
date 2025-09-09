/**
 * No Models Warning Component
 * 
 * Extracted from AgentsPage to reduce complexity
 * Shows warning when no models are configured
 */

import React from "react";
import { AlertCircle } from "lucide-react";
import { GradientCard } from "../common";

export interface NoModelsWarningProps {
  isVisible: boolean;
  className?: string;
}

export const NoModelsWarning: React.FC<NoModelsWarningProps> = ({
  isVisible,
  className = "",
}) => {
  if (!isVisible) return null;

  return (
    <div className={className}>
      <GradientCard theme="warning" isHoverable={false}>
        <div className="p-4">
          <div className="flex gap-3">
            <AlertCircle className="w-5 h-5 text-yellow-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-yellow-400 font-medium text-sm">
                Configuration Required
              </p>
              <p className="text-yellow-400/70 text-xs mt-1">
                Click "API Key Configuration" above to add provider credentials
                and enable AI agents
              </p>
            </div>
          </div>
        </div>
      </GradientCard>
    </div>
  );
};