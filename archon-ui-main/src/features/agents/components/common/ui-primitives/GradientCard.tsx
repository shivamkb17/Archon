/**
 * GradientCard Component
 * 
 * Reusable card component with Tron-inspired gradient backgrounds and borders
 * Replaces repeated gradient styling patterns throughout the app
 */

import type React from "react";
import { getCardStyle, getBorderStyle, getStatusBarStyle, type CardGradients } from "../styles/gradientStyles";
import { cn, getCardClasses } from "../utils/classNameHelpers";

export interface GradientCardProps {
  children: React.ReactNode;
  theme?: keyof CardGradients;
  className?: string;
  isActive?: boolean;
  isHoverable?: boolean;
  hasStatusBar?: boolean;
  statusBarType?: "saving" | "active" | "success" | "error";
  onClick?: () => void;
  size?: "sm" | "md" | "lg";
  role?: string;
  "aria-labelledby"?: string;
  "aria-describedby"?: string;
}

export const GradientCard: React.FC<GradientCardProps> = ({
  children,
  theme = "inactive",
  className = "",
  isActive = false,
  isHoverable = true,
  hasStatusBar = false,
  statusBarType = "active",
  onClick,
  size = "md",
  role,
  "aria-labelledby": ariaLabelledby,
  "aria-describedby": ariaDescribedby,
}) => {
  // Auto-determine theme based on active state if not explicitly provided
  const effectiveTheme = isActive && theme === "inactive" ? "active" : theme;
  
  return (
    <div
      className={cn(getCardClasses(isActive, isHoverable, size), className)}
      style={getCardStyle(effectiveTheme)}
      onClick={onClick}
      role={role}
      aria-labelledby={ariaLabelledby}
      aria-describedby={ariaDescribedby}
    >
      {/* Status Bar */}
      {hasStatusBar && (isActive || statusBarType === "saving") && (
        <div
          className="absolute top-0 left-0 right-0 h-[3px] animate-shimmer transition-all duration-500 z-10"
          style={getStatusBarStyle(statusBarType, true)}
        />
      )}

      {/* Gradient Border */}
      <div
        className="absolute inset-0 rounded-xl p-[1px] transition-all duration-300 pointer-events-none"
        style={getBorderStyle(effectiveTheme)}
      >
        <div
          className="w-full h-full rounded-xl"
          style={getCardStyle(effectiveTheme)}
        />
      </div>

      {/* Content */}
      <div className="relative">
        {children}
      </div>
    </div>
  );
};