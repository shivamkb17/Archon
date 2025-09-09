/**
 * Modal Header Component
 *
 * Reusable header component for modals with title and close button
 */

import React from "react";
import { X } from "lucide-react";

interface ModalHeaderProps {
  title: string;
  onClose: () => void;
  className?: string;
}

export const ModalHeader: React.FC<ModalHeaderProps> = ({
  title,
  onClose,
  className = "",
}) => {
  return (
    <div
      className={`flex items-center justify-between p-6 border-b border-zinc-700 ${className}`}
    >
      <h2 className="text-lg font-light text-white">{title}</h2>
      <button
        onClick={onClose}
        className="text-gray-400 hover:text-white transition-colors"
        title="Close modal"
      >
        <X className="w-5 h-5" />
      </button>
    </div>
  );
};
