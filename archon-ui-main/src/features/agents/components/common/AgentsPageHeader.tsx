/**
 * Agents Page Header Component
 *
 * Displays the main header for the agents configuration page
 */

import { Brain } from "lucide-react";

export const AgentsPageHeader: React.FC = () => {
  return (
    <div className="mb-8">
      <div className="flex items-center gap-3 mb-4">
        <Brain className="w-8 h-8 text-blue-600 dark:text-blue-400" />
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Agent Configuration
        </h1>
      </div>
      <p className="text-gray-600 dark:text-gray-400">
        Configure which AI models power your agents and services
      </p>
    </div>
  );
};
