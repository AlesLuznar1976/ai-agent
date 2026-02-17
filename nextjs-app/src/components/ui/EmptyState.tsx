import { type ReactNode } from "react";

interface EmptyStateProps {
  icon: ReactNode;
  message: string;
}

export default function EmptyState({ icon, message }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16">
      <div className="text-text-muted mb-4">{icon}</div>
      <p className="text-text-secondary">{message}</p>
    </div>
  );
}
