import { useState, useCallback, useRef } from 'react';
import type { SSEEvent, Message } from '../types';
import { sendMessageSSE } from '../api/client';

interface UseChatResult {
  messages: Message[];
  isStreaming: boolean;
  currentIntent: string | null;
  error: string | null;
  send: (sessionId: string, content: string) => Promise<string | null>;
  clearMessages: () => void;
  setMessages: (msgs: Message[]) => void;
}

export function useChat(): UseChatResult {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentIntent, setCurrentIntent] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const messagesRef = useRef<Message[]>([]);

  const send = useCallback(
    async (sessionId: string, content: string): Promise<string | null> => {
      setIsStreaming(true);
      setError(null);
      setCurrentIntent(null);

      // Add user message
      const userMsg: Message = {
        id: `user_${Date.now()}`,
        role: 'user',
        content,
        intent: null,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMsg]);

      let finalMessageId: string | null = null;
      let finalAnswer = '';
      let capturedIntent: string | null = null;  // Capture intent from SSE, avoid stale closure

      return new Promise((resolve) => {
        sendMessageSSE(
          sessionId,
          content,
          (event: SSEEvent) => {
            switch (event.type) {
              case 'intent':
                capturedIntent = event.data.intent || null;
                setCurrentIntent(capturedIntent);
                break;
              case 'done':
                finalAnswer = event.data.answer || '';
                finalMessageId = event.data.message_id || null;
                break;
            }
          },
          (errMsg: string) => {
            setError(errMsg);
            const errTmpMsg: Message = {
              id: `error_${Date.now()}`,
              role: 'assistant',
              content: `错误: ${errMsg}`,
              intent: null,
              created_at: new Date().toISOString(),
            };
            setMessages((prev) => [...prev, errTmpMsg]);
            setIsStreaming(false);
            resolve(null);
          },
          () => {
            // Done - add assistant message with captured intent (not stale React state)
            const assistantMsg: Message = {
              id: finalMessageId || `assistant_${Date.now()}`,
              role: 'assistant',
              content: finalAnswer,
              intent: capturedIntent,
              created_at: new Date().toISOString(),
            };
            setMessages((prev) => [...prev, assistantMsg]);
            setCurrentIntent(null);
            setIsStreaming(false);
            resolve(finalMessageId);
          }
        );
      });
    },
    []
  );

  const clearMessages = useCallback(() => {
    setMessages([]);
    messagesRef.current = [];
  }, []);

  return {
    messages,
    isStreaming,
    currentIntent,
    error,
    send,
    clearMessages,
    setMessages,
  };
}
