/**
 * Agent Tab Navigation Component
 * 
 * Extracted from AgentsPage to reduce complexity
 * Handles tab switching between agents and services
 */

import React from "react";
import { getTabClasses, getBadgeClasses, cn } from "../common";
import type { AgentConfig } from "../../../../types/agent";

export interface AgentTabNavigationProps {
  activeTab: "agents" | "services";
  onTabChange: (tab: "agents" | "services") => void;
  agents: AgentConfig[];
  backendServices: AgentConfig[];
  className?: string;
}

export const AgentTabNavigation: React.FC<AgentTabNavigationProps> = ({
  activeTab,
  onTabChange,
  agents,
  backendServices,
  className = "",
}) => {
  return (
    <div className={cn("flex gap-4 mb-6 border-b border-gray-200 dark:border-gray-700", className)}>
      <button
        onClick={() => onTabChange("agents")}
        className={getTabClasses(activeTab === "agents")}
      >
        <div className="flex items-center gap-2">
          <span>AI Agents</span>
          <span className={getBadgeClasses("primary", "sm")}>
            {agents.length}
          </span>
        </div>
      </button>
      
      <button
        onClick={() => onTabChange("services")}
        className={getTabClasses(activeTab === "services")}
      >
        <div className="flex items-center gap-2">
          <span>Backend Services</span>
          <span className={getBadgeClasses("secondary", "sm")}>
            {backendServices.length}
          </span>
        </div>
      </button>
    </div>
  );
};