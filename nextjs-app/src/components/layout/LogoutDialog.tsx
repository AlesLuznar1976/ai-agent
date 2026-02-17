"use client";

interface LogoutDialogProps {
  onConfirm: () => void;
  onCancel: () => void;
}

export default function LogoutDialog({ onConfirm, onCancel }: LogoutDialogProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={onCancel}>
      <div
        className="bg-white rounded-md p-6 mx-4 max-w-sm w-full shadow-lg"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="text-lg font-semibold text-navy mb-2">Odjava</h3>
        <p className="text-text-secondary text-sm mb-6">Ali se želite odjaviti?</p>
        <div className="flex justify-end gap-3">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-sm text-navy border border-navy/30 rounded-sm hover:bg-navy/5 transition-colors"
          >
            Prekliči
          </button>
          <button
            onClick={onConfirm}
            className="px-4 py-2 text-sm text-white bg-navy rounded-sm hover:bg-navy-light transition-colors"
          >
            Odjava
          </button>
        </div>
      </div>
    </div>
  );
}
