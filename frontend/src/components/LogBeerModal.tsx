import { useEffect } from "react";
import EntryForm from "./EntryForm";

interface Props {
  onClose: () => void;
  onSuccess: () => void;
}

export default function LogBeerModal({ onClose, onSuccess }: Props) {
  // Close on Escape key
  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [onClose]);

  function handleSuccess() {
    onSuccess();
    onClose();
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-xl font-bold text-amber-800">Log a Beer</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
            aria-label="Close"
          >
            ×
          </button>
        </div>

        <EntryForm onSuccess={handleSuccess} />
      </div>
    </div>
  );
}
