export interface ChatAttachment {
  filename: string;
  size: number;
  mime_type: string;
}

export interface FormField {
  key: string;
  label: string;
  type: "text" | "date" | "select" | "textarea";
  value?: string;
  placeholder?: string;
  options?: { value: string; label: string }[];
  required?: boolean;
}

export interface DocumentFormData {
  doc_type: string;
  fields: FormField[];
}

export interface ChatMessage {
  role: "user" | "agent" | "system";
  content: string;
  timestamp: string;
  projektId?: number;
  needsConfirmation?: boolean;
  actions?: ChatAction[];
  suggestedCommands?: string[];
  attachments?: ChatAttachment[];
  documentForm?: DocumentFormData;
}

export interface ChatAction {
  id: string;
  status: "Čaka" | "Potrjeno" | "Zavrnjeno";
  description: string;
  tool_name?: string;
}
