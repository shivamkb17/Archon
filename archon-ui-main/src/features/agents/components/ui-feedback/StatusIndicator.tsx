/**
 * Status Indicator Component
 *
 * Reusable component for displaying status with icons and colors
 */

import React from "react";
import { CheckCircle, XCircle, Clock, AlertCircle } from "lucide-react";

export type StatusType = "success" | "error" | "warning" | "info" | "loading";

interface StatusIndicatorProps {
  status: StatusType;
  size?: "sm" | "md" | "lg";
  showText?: boolean;
  customText?: string;
  className?: string;
}

export const StatusIndicator: React.FC<StatusIndicatorProps> = ({
  status,
  size = "md",
  showText = false,
  customText,
  className = "",
}) => {
  const sizeClasses = {
    sm: "w-3 h-3",
    md: "w-4 h-4",
    lg: "w-5 h-5",
  };

  const getStatusConfig = (status: StatusType) => {
    switch (status) {
      case "success":
        return {
          icon: CheckCircle,
          color: "text-emerald-400",
          text: customText || "Success",
        };
      case "error":
        return {
          icon: XCircle,
          color: "text-red-400",
          text: customText || "Error",
        };
      case "warning":
        return {
          icon: AlertCircle,
          color: "text-yellow-400",
          text: customText || "Warning",
        };
      case "info":
        return {
          icon: AlertCircle,
          color: "text-blue-400",
          text: customText || "Info",
        };
      case "loading":
        return {
          icon: Clock,
          color: "text-purple-400",
          text: customText || "Loading",
        };
      default:
        return {
          icon: AlertCircle,
          color: "text-gray-400",
          text: customText || "Unknown",
        };
    }
  };

  const config = getStatusConfig(status);
  const Icon = config.icon;

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <Icon className={`${sizeClasses[size]} ${config.color}`} />
      {showText && (
        <span className={`text-sm ${config.color}`}>{config.text}</span>
      )}
    </div>
  );
};
