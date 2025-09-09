/**
 * Add Provider Modal Component
 *
 * Modal for adding new AI providers with API key configuration
 * Refactored to use shared provider utilities
 */

import React, { useState, useMemo } from "react";
import { Modal } from "../../../../components/ui/Modal";
import { Button } from "../../../../components/ui/Button";
import { useToast } from "../../../../contexts/ToastContext";
import type { ProviderMetadata } from "../../../../types/cleanProvider";
import { useAgents } from "../../hooks";
import { getProviderDisplayInfo } from "../common";
import { ProviderList } from "./ProviderList";
import { ProviderForm } from "./ProviderForm";

interface AddProviderModalProps {
  isOpen: boolean;
  onClose: () => void;
  onProviderAdded: () => void;
  existingProviders: string[];
  providersMetadata: Record<string, ProviderMetadata>;
  availableProviders: string[]; // DB-provided provider list
}

export const AddProviderModal: React.FC<AddProviderModalProps> = ({
  isOpen,
  onClose,
  onProviderAdded,
  existingProviders,
  providersMetadata,
  availableProviders,
}) => {
  const [selectedProvider, setSelectedProvider] = useState<string | null>(null);
  const [apiKey, setApiKey] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [showApiKey, setShowApiKey] = useState(false);

  const { showToast } = useToast();
  const { addProvider, isAddingProvider } = useAgents();

  // Using shared provider display utility

  // Get metadata for selected provider
  const selectedProviderMeta = useMemo(() => {
    if (!selectedProvider) return null;
    return providersMetadata[selectedProvider];
  }, [selectedProvider, providersMetadata]);

  // Handle provider selection
  const handleSelectProvider = (provider: string) => {
    setSelectedProvider(provider);
    setApiKey("");
  };

  // Handle adding or updating provider
  const handleAddProvider = async () => {
    if (!selectedProvider || !apiKey.trim()) {
      showToast("Please select a provider and enter an API key", "error");
      return;
    }

    try {
      // Use optimistic add provider mutation
      await addProvider({ provider: selectedProvider, apiKey: apiKey.trim() });

      const isUpdate = existingProviders.includes(selectedProvider);
      const providerName = getProviderDisplayInfo(
        selectedProvider,
        selectedProviderMeta || undefined
      ).name;
      showToast(
        `${providerName} ${isUpdate ? "updated" : "added"} successfully`,
        "success"
      );
      onProviderAdded();

      // Reset form
      setSelectedProvider(null);
      setApiKey("");
      setSearchQuery("");
      onClose();
    } catch (error) {
      console.error("Failed to add/update provider:", error);
      showToast("Failed to add/update provider", "error");
    }
  };

  // Reset state when modal opens/closes
  React.useEffect(() => {
    if (!isOpen) {
      setSelectedProvider(null);
      setApiKey("");
      setSearchQuery("");
      setShowApiKey(false);
    }
  }, [isOpen]);

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Add AI Provider" size="lg">
      <div className="space-y-6">
        {!selectedProvider ? (
          <ProviderList
            searchQuery={searchQuery}
            onSearchChange={setSearchQuery}
            availableProviders={availableProviders}
            existingProviders={existingProviders}
            providersMetadata={providersMetadata}
            onSelectProvider={handleSelectProvider}
          />
        ) : (
          <ProviderForm
            selectedProvider={selectedProvider}
            selectedProviderMeta={selectedProviderMeta}
            apiKey={apiKey}
            onApiKeyChange={setApiKey}
            showApiKey={showApiKey}
            onToggleShowApiKey={() => setShowApiKey(!showApiKey)}
            onDeselectProvider={() => setSelectedProvider(null)}
            onSubmit={handleAddProvider}
            isSubmitting={isAddingProvider}
            existingProviders={existingProviders}
          />
        )}

        {/* Cancel Button - only show when no provider is selected */}
        {!selectedProvider && (
          <div className="flex justify-end gap-2 pt-4 border-t border-zinc-700">
            <Button onClick={onClose} variant="ghost" size="sm">
              Cancel
            </Button>
          </div>
        )}
      </div>
    </Modal>
  );
};
