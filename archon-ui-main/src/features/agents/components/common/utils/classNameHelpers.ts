/**
 * ClassName Helper Utilities
 * 
 * Utilities for building conditional classNames and reducing template literal complexity
 */

/**
 * Conditionally join classNames, filtering out falsy values
 */
export const cn = (...classes: (string | undefined | null | false)[]): string => {
  return classes.filter(Boolean).join(" ");
};

/**
 * Build conditional className based on state
 */
export const conditionalClass = (
  baseClass: string,
  condition: boolean,
  trueClass: string,
  falseClass?: string
): string => {
  return cn(baseClass, condition ? trueClass : falseClass);
};

/**
 * Status-based className builders
 */
export const getStatusClasses = (status: "healthy" | "unhealthy" | "checking" | null) => {
  const baseClasses = "w-3.5 h-3.5";
  
  switch (status) {
    case "checking":
      return cn(baseClasses, "text-yellow-400 animate-spin");
    case "healthy":
      return cn(baseClasses, "text-emerald-400");
    case "unhealthy":
      return cn(baseClasses, "text-red-400");
    default:
      return cn(baseClasses, "text-gray-600");
  }
};

/**
 * Tab navigation className helper
 */
export const getTabClasses = (isActive: boolean): string => {
  const baseClasses = "pb-3 px-1 border-b-2 transition-colors";
  const activeClasses = "border-blue-600 text-blue-600 dark:border-blue-400 dark:text-blue-400";
  const inactiveClasses = "border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white";
  
  return cn(baseClasses, isActive ? activeClasses : inactiveClasses);
};

/**
 * Button state className helper
 */
export const getButtonStateClasses = (
  isLoading?: boolean,
  isDisabled?: boolean,
  variant: "primary" | "secondary" | "ghost" = "primary"
): string => {
  const baseClasses = "px-4 py-2 rounded-lg transition-colors font-medium text-sm";
  
  const variantClasses = {
    primary: "bg-purple-600 hover:bg-purple-700 text-white",
    secondary: "bg-zinc-700 hover:bg-zinc-600 text-white",
    ghost: "bg-transparent hover:bg-zinc-800 text-gray-300",
  };
  
  const stateClasses = cn(
    isLoading && "opacity-50 cursor-not-allowed",
    isDisabled && "opacity-50 cursor-not-allowed"
  );
  
  return cn(baseClasses, variantClasses[variant], stateClasses);
};

/**
 * Card container className helper
 */
export const getCardClasses = (
  isActive?: boolean,
  isHoverable = true,
  size: "sm" | "md" | "lg" = "md"
): string => {
  const baseClasses = "relative rounded-xl overflow-hidden transition-all duration-300";
  
  const sizeClasses = {
    sm: "p-3",
    md: "p-4",
    lg: "p-6",
  };
  
  const stateClasses = cn(
    isHoverable && "hover:scale-[1.02] hover:shadow-2xl",
    isActive && "ring-1 ring-purple-500/30 shadow-lg shadow-purple-500/10"
  );
  
  return cn(baseClasses, sizeClasses[size], stateClasses);
};

/**
 * Badge variant className helper
 */
export const getBadgeClasses = (
  variant: "primary" | "secondary" | "success" | "warning" | "error" = "primary",
  size: "sm" | "md" = "sm"
): string => {
  const baseClasses = "rounded-full font-medium";
  
  const sizeClasses = {
    sm: "px-2 py-0.5 text-xs",
    md: "px-3 py-1 text-sm",
  };
  
  const variantClasses = {
    primary: "bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400",
    secondary: "bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400",
    success: "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20",
    warning: "bg-yellow-500/10 text-yellow-400 border border-yellow-500/20",
    error: "bg-red-500/10 text-red-400 border border-red-500/20",
  };
  
  return cn(baseClasses, sizeClasses[size], variantClasses[variant]);
};

/**
 * Input field className helper
 */
export const getInputClasses = (
  hasError?: boolean,
  size: "sm" | "md" = "md"
): string => {
  const baseClasses = "bg-zinc-800 text-white rounded-lg focus:outline-none transition-colors";
  
  const sizeClasses = {
    sm: "px-3 py-1.5 text-sm",
    md: "px-3 py-2 text-sm",
  };
  
  const stateClasses = hasError
    ? "border border-red-500 focus:ring-1 focus:ring-red-500"
    : "border border-zinc-700 focus:ring-1 focus:ring-purple-500";
  
  return cn(baseClasses, sizeClasses[size], stateClasses);
};