/**
 * Modal Footer Component
 *
 * Reusable footer component for modals with action buttons
 */

import React from "react";
import { Button } from "../../../../components/ui/Button";

interface ModalFooterProps {
  onCancel?: () => void;
  onConfirm?: () => void;
  cancelText?: string;
  confirmText?: string;
  isConfirmDisabled?: boolean;
  isConfirmLoading?: boolean;
  className?: string;
  children?: React.ReactNode;
}

export const ModalFooter: React.FC<ModalFooterProps> = ({
  onCancel,
  onConfirm,
  cancelText = "Cancel",
  confirmText = "Confirm",
  isConfirmDisabled = false,
  isConfirmLoading = false,
  className = "",
  children,
}) => {
  return (
    <div
      className={`flex justify-end gap-2 pt-4 border-t border-zinc-700 ${className}`}
    >
      {onCancel && (
        <Button onClick={onCancel} variant="ghost" size="sm">
          {cancelText}
        </Button>
      )}
      {onConfirm && (
        <Button
          onClick={onConfirm}
          variant="primary"
          size="sm"
          disabled={isConfirmDisabled || isConfirmLoading}
        >
          {isConfirmLoading ? "Loading..." : confirmText}
        </Button>
      )}
      {children}
    </div>
  );
};
