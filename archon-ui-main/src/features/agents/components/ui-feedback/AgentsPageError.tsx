/**
 * Agents Page Error Component
 *
 * Displays error state when services fail to load
 */

import { AlertCircle } from "lucide-react";

interface AgentsPageErrorProps {
  servicesError: string;
}

export const AgentsPageError: React.FC<AgentsPageErrorProps> = ({
  servicesError,
}) => {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen">
      <AlertCircle className="w-12 h-12 text-red-500 mb-4" />
      <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
        Failed to Load Services
      </h2>
      <p className="text-gray-600 dark:text-gray-400 mb-4 text-center max-w-md">
        Could not load service registry from database: {servicesError}
      </p>
    </div>
  );
};
