import { useEffect, useRef } from 'react';
import type { Message } from '../types';
import MessageBubble from './MessageBubble';
import ChatInput from './ChatInput';
import FeedbackBar from './FeedbackBar';

interface ChatWindowProps {
  messages: Message[];
  isStreaming: boolean;
  currentIntent: string | null;
  onSend: (content: string) => void;
}

export default function ChatWindow({
  messages,
  isStreaming,
  currentIntent,
  onSend,
}: ChatWindowProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex flex-col h-full">
      {/* Status bar */}
      {isStreaming && (
        <div className="px-4 py-2 bg-primary-50 text-primary-700 text-xs flex items-center gap-2 border-b border-primary-100">
          <svg className="animate-spin h-3 w-3" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <span>
            {currentIntent
              ? `正在处理: ${currentIntent}`
              : '正在生成回复...'}
          </span>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center text-gray-400">
              <svg className="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                  d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
              <p className="text-sm">新建对话，开始提问</p>
            </div>
          </div>
        ) : (
          messages.map((msg, index) => (
            <MessageBubble
              key={msg.id}
              message={msg}
              isLastAI={index === messages.length - 1 && msg.role === 'assistant'}
              feedbackBar={
                index === messages.length - 1 &&
                msg.role === 'assistant' &&
                msg.id &&
                !msg.id.startsWith('error_') &&
                !msg.id.startsWith('assistant_') ? (
                  <FeedbackBar messageId={msg.id} />
                ) : undefined
              }
            />
          ))
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <ChatInput onSend={onSend} disabled={isStreaming} />
    </div>
  );
}
