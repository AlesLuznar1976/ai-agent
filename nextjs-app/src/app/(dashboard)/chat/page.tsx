"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { ChatMessage } from "@/types/chat";
import { apiSendMessage, apiConfirmAction, apiRejectAction } from "@/lib/api";
import ChatWelcome from "@/components/chat/ChatWelcome";
import MessageBubble from "@/components/chat/MessageBubble";
import TypingIndicator from "@/components/chat/TypingIndicator";
import SuggestedCommands from "@/components/chat/SuggestedCommands";
import ChatInput from "@/components/chat/ChatInput";

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [suggestedCommands, setSuggestedCommands] = useState<string[]>([
    "Pomoč",
    "Preveri emaile",
    "Seznam projektov",
  ]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading, scrollToBottom]);

  const sendMessage = async (text: string, files?: File[]) => {
    const attachments = files?.map((f) => ({
      filename: f.name,
      size: f.size,
      mime_type: f.type || "application/octet-stream",
    }));

    const userMsg: ChatMessage = {
      role: "user",
      content: text,
      timestamp: new Date().toISOString(),
      attachments,
    };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const response = await apiSendMessage(text, undefined, files);
      setMessages((prev) => [...prev, response]);
      if (response.suggestedCommands?.length) {
        setSuggestedCommands(response.suggestedCommands);
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "Neznana napaka";
      console.error("Chat error:", err);
      setMessages((prev) => [
        ...prev,
        {
          role: "system",
          content: `Napaka: ${errorMsg}`,
          timestamp: new Date().toISOString(),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleConfirm = async (actionId: string) => {
    try {
      await apiConfirmAction(actionId);
      setMessages((prev) =>
        prev.map((msg) => ({
          ...msg,
          actions: msg.actions?.map((a) =>
            a.id === actionId ? { ...a, status: "Potrjeno" as const } : a
          ),
        }))
      );
    } catch {
      // silently fail
    }
  };

  const handleReject = async (actionId: string) => {
    try {
      await apiRejectAction(actionId);
      setMessages((prev) =>
        prev.map((msg) => ({
          ...msg,
          actions: msg.actions?.map((a) =>
            a.id === actionId ? { ...a, status: "Zavrnjeno" as const } : a
          ),
        }))
      );
    } catch {
      // silently fail
    }
  };

  return (
    <div className="flex flex-col h-full bg-surface">
      {messages.length === 0 ? (
        <ChatWelcome onSend={sendMessage} />
      ) : (
        <div className="flex-1 overflow-y-auto scrollbar-thin px-4 py-3">
          {messages.map((msg, idx) => (
            <MessageBubble
              key={idx}
              message={msg}
              onConfirm={handleConfirm}
              onReject={handleReject}
            />
          ))}
          {isLoading && <TypingIndicator />}
          <div ref={messagesEndRef} />
        </div>
      )}
      <SuggestedCommands commands={suggestedCommands} onSelect={sendMessage} />
      <ChatInput onSend={sendMessage} disabled={isLoading} />
    </div>
  );
}
