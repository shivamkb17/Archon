/**
 * Agent Settings Dropdown Component
 *
 * Button to open model selection modal for agent configuration
 */

import React from "react";
import { Edit3, Clock } from "lucide-react";
import { Button } from "../../../../components/ui/Button";
import type { AgentConfig } from "../../../../types/agent";

interface AgentSettingsDropdownProps {
  agent: AgentConfig;
  isSaving: boolean;
  onConfigure: () => void;
}

export const AgentSettingsDropdown: React.FC<AgentSettingsDropdownProps> = ({
  agent,
  isSaving,
  onConfigure,
}) => {
  return (
    <Button
      onClick={onConfigure}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onConfigure();
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
          <Clock className="w-3 h-3 animate-spin" aria-hidden="true" />
          <span id="saving-status">Saving...</span>
        </>
      ) : (
        <>
          <Edit3 className="w-3 h-3" aria-hidden="true" />
          Configure
        </>
      )}
    </Button>
  );
};
