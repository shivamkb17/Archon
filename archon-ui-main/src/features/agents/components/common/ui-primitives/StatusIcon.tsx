/**
 * StatusIcon Component
 * 
 * Unified status icon component with consistent styling and animations
 * Replaces scattered status icon logic throughout components
 */

import type React from "react";
import { Clock, CheckCircle, XCircle, AlertCircle } from "lucide-react";
import { cn, getStatusClasses } from "../utils/classNameHelpers";

export type StatusType = "healthy" | "unhealthy" | "checking" | "warning" | "idle" | null;

export interface StatusIconProps {
  status: StatusType;
  className?: string;
  size?: "sm" | "md" | "lg";
  showDot?: boolean;
  ariaLabel?: string;
}

export const StatusIcon: React.FC<StatusIconProps> = ({
  status,
  className = "",
  size = "md",
  showDot = false,
  ariaLabel,
}) => {
  const sizeClasses = {
    sm: "w-3 h-3",
    md: "w-3.5 h-3.5", 
    lg: "w-4 h-4",
  };

  const dotSizeClasses = {
    sm: "w-1.5 h-1.5",
    md: "w-2 h-2",
    lg: "w-2.5 h-2.5",
  };

  // If showing dot instead of icon
  if (showDot) {
    const dotStatusClasses = {
      healthy: "bg-emerald-400 animate-pulse",
      unhealthy: "bg-red-400",
      checking: "bg-yellow-400 animate-pulse",
      warning: "bg-yellow-400",
      idle: "bg-gray-600",
    };

    const dotClass = status && dotStatusClasses[status] ? dotStatusClasses[status] : "bg-gray-600";
    
    return (
      <div
        className={cn(dotSizeClasses[size], "rounded-full", dotClass, className)}
        aria-label={ariaLabel || `Status: ${status || "unknown"}`}
      />
    );
  }

  // Icon-based status display
  const getStatusIcon = () => {
    const baseClasses = cn(sizeClasses[size], className);

    switch (status) {
      case "checking":
        return (
          <Clock
            className={cn(baseClasses, "text-yellow-400 animate-spin")}
            aria-label={ariaLabel || "Checking status"}
          />
        );
      case "healthy":
        return (
          <CheckCircle
            className={cn(baseClasses, "text-emerald-400")}
            aria-label={ariaLabel || "Healthy status"}
          />
        );
      case "unhealthy":
        return (
          <XCircle
            className={cn(baseClasses, "text-red-400")}
            aria-label={ariaLabel || "Unhealthy status"}
          />
        );
      case "warning":
        return (
          <AlertCircle
            className={cn(baseClasses, "text-yellow-400")}
            aria-label={ariaLabel || "Warning status"}
          />
        );
      case "idle":
      default:
        return (
          <div
            className={cn(dotSizeClasses[size], "bg-gray-600 rounded-full", className)}
            aria-label={ariaLabel || "Idle status"}
          />
        );
    }
  };

  return getStatusIcon();
};