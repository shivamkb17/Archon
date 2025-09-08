/**
 * Example: Using Optimistic Updates in Agent Components
 *
 * This file demonstrates how to integrate optimistic updates into your components
 * for better user experience and visual feedback.
 */

import React, { useState } from "react";
import { useAgents, useOptimisticState, useOptimisticLoading } from "../hooks";
import {
  OptimisticButton,
  OptimisticWrapper,
  OptimisticStatus,
  OptimisticListItem,
} from "../components";

/**
 * Example Provider Card with Optimistic Updates
 */
export const ExampleProviderCard: React.FC<{
  provider: string;
  isConfigured: boolean;
  onRemove: () => Promise<void>;
  isRemoving?: boolean;
  removeError?: Error | null;
}> = ({
  provider,
  isConfigured,
  onRemove,
  isRemoving = false,
  removeError = null,
}) => {
  // Use optimistic state for configuration status
  const { value: optimisticConfigured, isOptimistic } = useOptimisticState(
    isConfigured,
    false, // Optimistically show as not configured during removal
    isRemoving,
    removeError
  );

  // Use optimistic loading state
  const loadingState = useOptimisticLoading(isRemoving, removeError);

  return (
    <OptimisticWrapper
      isOptimistic={isOptimistic}
      hasError={!!removeError}
      className="border rounded-lg p-4"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <span>{provider}</span>
          <OptimisticStatus
            status={
              loadingState === "loading"
                ? "optimistic"
                : loadingState === "error"
                ? "error"
                : loadingState === "optimistic"
                ? "optimistic"
                : "idle"
            }
          />
        </div>

        <OptimisticButton
          isLoading={isRemoving}
          isOptimistic={isOptimistic}
          hasError={!!removeError}
          onClick={onRemove}
          loadingText="Removing..."
          optimisticText="Removing..."
          errorText="Failed"
          className="text-red-600 hover:text-red-800"
        >
          Remove
        </OptimisticButton>
      </div>

      {optimisticConfigured && (
        <div className="mt-2 text-sm text-green-600">✓ Configured</div>
      )}
    </OptimisticWrapper>
  );
};

/**
 * Example Provider List with Optimistic Add/Remove
 */
export const ExampleProviderList: React.FC<{
  providers: string[];
  onAdd: (provider: string) => Promise<void>;
  onRemove: (provider: string) => Promise<void>;
  isAdding?: boolean;
  addError?: Error | null;
}> = ({ providers, onAdd, onRemove, isAdding = false, addError = null }) => {
  const [newProvider, setNewProvider] = useState("");

  const handleAdd = async () => {
    if (!newProvider.trim()) return;
    await onAdd(newProvider);
    setNewProvider("");
  };

  return (
    <div className="space-y-2">
      {providers.map((provider) => (
        <OptimisticListItem
          key={provider}
          isOptimistic={false} // You would track this per item
          className="border rounded p-2"
        >
          <ExampleProviderCard
            provider={provider}
            isConfigured={true}
            onRemove={() => onRemove(provider)}
          />
        </OptimisticListItem>
      ))}

      <div className="flex space-x-2 mt-4">
        <input
          type="text"
          value={newProvider}
          onChange={(e) => setNewProvider(e.target.value)}
          placeholder="Enter provider name"
          className="flex-1 px-3 py-2 border rounded"
        />
        <OptimisticButton
          isLoading={isAdding}
          isOptimistic={isAdding}
          hasError={!!addError}
          onClick={handleAdd}
          loadingText="Adding..."
          optimisticText="Adding..."
          errorText="Failed"
        >
          Add Provider
        </OptimisticButton>
      </div>
    </div>
  );
};

/**
 * Usage Example in a Parent Component
 */
export const ExampleUsage: React.FC = () => {
  const { availableModels, addProvider, removeProvider } = useAgents();

  const [providers, setProviders] = useState<string[]>(["openai", "anthropic"]);

  const handleAddProvider = async (provider: string) => {
    await addProvider({ provider, apiKey: "test-key" });
    setProviders((prev) => [...prev, provider]);
  };

  const handleRemoveProvider = async (provider: string) => {
    await removeProvider({ provider });
    setProviders((prev) => prev.filter((p) => p !== provider));
  };

  return (
    <div className="p-6">
      <h2 className="text-xl font-bold mb-4">
        Providers with Optimistic Updates
      </h2>

      <ExampleProviderList
        providers={providers}
        onAdd={handleAddProvider}
        onRemove={handleRemoveProvider}
      />

      <div className="mt-6">
        <h3 className="text-lg font-semibold mb-2">Available Models</h3>
        <div className="text-sm text-gray-600">
          {availableModels.length} models available
        </div>
      </div>
    </div>
  );
};
