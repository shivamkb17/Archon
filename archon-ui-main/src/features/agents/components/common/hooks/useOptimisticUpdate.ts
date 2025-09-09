/**
 * useOptimisticUpdate Hook
 * 
 * Custom hook for handling optimistic updates with rollback capability
 * Extracted from AgentCard to reduce complexity and improve reusability
 */

import React, { useState, useRef, useCallback } from "react";
import { useToast } from "../../../../../contexts/ToastContext";
import type { StatusType } from "../ui-primitives/StatusIcon";

export interface OptimisticUpdateOptions<T> {
  onSuccess?: (data: T) => void;
  onError?: (error: unknown, previousState: T) => void;
  successMessage?: string;
  errorMessage?: string;
  successTimeout?: number;
  errorTimeout?: number;
}

export interface OptimisticUpdateResult<T> {
  isUpdating: boolean;
  status: StatusType;
  executeUpdate: (
    updateFn: () => Promise<void>,
    optimisticState: T,
    currentState: T
  ) => Promise<void>;
}

export const useOptimisticUpdate = <T>(
  initialState: T,
  setState: (state: T) => void,
  options: OptimisticUpdateOptions<T> = {}
): OptimisticUpdateResult<T> => {
  const [isUpdating, setIsUpdating] = useState(false);
  const [status, setStatus] = useState<StatusType | null>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const { showToast } = useToast();

  const {
    onSuccess,
    onError,
    successMessage,
    errorMessage,
    successTimeout = 1500,
    errorTimeout = 3000,
  } = options;

  const clearTimeoutRef = useCallback(() => {
    if (timeoutRef.current) {
      window.clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  }, []);

  const executeUpdate = useCallback(
    async (
      updateFn: () => Promise<void>,
      optimisticState: T,
      currentState: T
    ): Promise<void> => {
      // Clear any existing timeouts
      clearTimeoutRef();

      // Store previous state for potential rollback
      const previousState = currentState;

      // Optimistically update the UI
      setState(optimisticState);

      // Show updating status
      setIsUpdating(true);
      setStatus("checking");

      try {
        // Execute the actual update
        await updateFn();

        // Show success status
        setStatus("healthy");
        
        if (successMessage) {
          showToast(successMessage, "success");
        }

        // Call success callback
        if (onSuccess) {
          onSuccess(optimisticState);
        }

        // Clear success status after timeout
        timeoutRef.current = window.setTimeout(() => {
          setStatus(null);
          timeoutRef.current = null;
        }, successTimeout);
      } catch (error) {
        console.error("Optimistic update failed:", error);
        
        // Rollback to previous state
        setState(previousState);
        setStatus("unhealthy");

        const message = errorMessage || "Update failed. Please try again.";
        showToast(message, "error");

        // Call error callback
        if (onError) {
          onError(error, previousState);
        }

        // Clear error status after timeout
        timeoutRef.current = window.setTimeout(() => {
          setStatus(null);
          timeoutRef.current = null;
        }, errorTimeout);
      } finally {
        setIsUpdating(false);
      }
    },
    [
      setState,
      clearTimeoutRef,
      showToast,
      onSuccess,
      onError,
      successMessage,
      errorMessage,
      successTimeout,
      errorTimeout,
    ]
  );

  // Cleanup on unmount
  React.useEffect(() => {
    return clearTimeoutRef;
  }, [clearTimeoutRef]);

  return {
    isUpdating,
    status,
    executeUpdate,
  };
};