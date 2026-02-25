export interface ChatAttachment {
  filename: string;
  size: number;
  mime_type: string;
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
}

export interface ChatAction {
  id: string;
  status: "Čaka" | "Potrjeno" | "Zavrnjeno";
  description: string;
  tool_name?: string;
}
