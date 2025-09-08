/**
 * Optimistic Update Utilities
 *
 * Utilities for providing visual feedback during optimistic updates
 */

import { useState, useEffect } from 'react';

/**
 * Hook for managing optimistic update states with visual feedback
 */
export const useOptimisticState = <T>(
  initialValue: T,
  optimisticValue: T,
  isPending: boolean,
  error?: Error | null
) => {
  const [value, setValue] = useState<T>(initialValue);
  const [isOptimistic, setIsOptimistic] = useState(false);

  useEffect(() => {
    if (isPending && !error) {
      setValue(optimisticValue);
      setIsOptimistic(true);
    } else if (error) {
      setValue(initialValue);
      setIsOptimistic(false);
    } else {
      setValue(initialValue);
      setIsOptimistic(false);
    }
  }, [isPending, error, optimisticValue, initialValue]);

  return { value, isOptimistic, hasError: !!error };
};

/**
 * Hook for managing loading states with optimistic feedback
 */
export const useOptimisticLoading = (isPending: boolean, error?: Error | null) => {
  const [loadingState, setLoadingState] = useState<'idle' | 'optimistic' | 'loading' | 'error'>('idle');

  useEffect(() => {
    if (error) {
      setLoadingState('error');
    } else if (isPending) {
      setLoadingState('optimistic');
    } else {
      setLoadingState('idle');
    }
  }, [isPending, error]);

  return loadingState;
};

/**
 * Utility for creating optimistic update animations
 */
export const optimisticUpdateStyles = {
  optimistic: {
    opacity: 0.7,
    transform: 'scale(0.98)',
    transition: 'all 0.2s ease-in-out',
  },
  success: {
    opacity: 1,
    transform: 'scale(1)',
    transition: 'all 0.3s ease-in-out',
  },
  error: {
    opacity: 1,
    transform: 'scale(1)',
    animation: 'shake 0.5s ease-in-out',
  },
};

/**
 * Hook for managing optimistic list updates (add/remove items)
 */
export const useOptimisticList = <T>(
  items: T[],
  pendingOperation: 'add' | 'remove' | null,
  pendingItem?: T,
  error?: Error | null
) => {
  const [optimisticItems, setOptimisticItems] = useState<T[]>(items);
  const [animatingItems, setAnimatingItems] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (pendingOperation === 'add' && pendingItem) {
      const itemId = (pendingItem as any).id || JSON.stringify(pendingItem);
      setOptimisticItems(prev => [...prev, pendingItem]);
      setAnimatingItems(prev => new Set([...prev, itemId]));
    } else if (pendingOperation === 'remove' && pendingItem) {
      const itemId = (pendingItem as any).id || JSON.stringify(pendingItem);
      setOptimisticItems(prev => prev.filter(item => {
        const currentId = (item as any).id || JSON.stringify(item);
        return currentId !== itemId;
      }));
      setAnimatingItems(prev => new Set([...prev, itemId]));
    } else if (!pendingOperation && !error) {
      setOptimisticItems(items);
      setAnimatingItems(new Set());
    } else if (error) {
      // On error, revert to original items
      setOptimisticItems(items);
      setAnimatingItems(new Set());
    }
  }, [items, pendingOperation, pendingItem, error]);

  return { optimisticItems, animatingItems };
};

/**
 * CSS keyframes for animations (to be added to global styles)
 */
export const optimisticAnimations = `
@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-5px); }
  75% { transform: translateX(5px); }
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes fadeOut {
  from { opacity: 1; transform: translateY(0); }
  to { opacity: 0; transform: translateY(-10px); }
}

.optimistic-enter {
  animation: fadeIn 0.3s ease-in-out;
}

.optimistic-exit {
  animation: fadeOut 0.3s ease-in-out;
}
`;
