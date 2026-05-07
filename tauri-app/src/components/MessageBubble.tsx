import type { Message } from '../types';

interface MessageBubbleProps {
  message: Message;
  isLastAI: boolean;
  feedbackBar?: React.ReactNode;
}

export default function MessageBubble({ message, isLastAI, feedbackBar }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const isAssistant = message.role === 'assistant';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`max-w-[75%] ${isUser ? 'order-1' : ''}`}>
        {/* Role label */}
        <div className={`text-xs mb-1 ${isUser ? 'text-right text-blue-500' : 'text-gray-500'}`}>
          {isUser ? '我' : 'AI 客服'}
          {message.intent && isAssistant && (
            <span className="ml-2 inline-block px-1.5 py-0.5 bg-gray-100 text-gray-500 rounded text-[10px]">
              {message.intent}
            </span>
          )}
        </div>

        {/* Bubble */}
        <div
          className={`px-4 py-2.5 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap break-words ${
            isUser
              ? 'bg-primary-500 text-white rounded-br-md'
              : isAssistant
                ? message.content.startsWith('错误:')
                  ? 'bg-red-50 text-red-700 rounded-bl-md'
                  : 'bg-gray-100 text-gray-800 rounded-bl-md'
                : 'bg-yellow-50 text-yellow-700 rounded-bl-md'
          }`}
        >
          {message.content}
        </div>

        {/* Time */}
        <div className={`text-[10px] text-gray-400 mt-1 ${isUser ? 'text-right' : ''}`}>
          {new Date(message.created_at).toLocaleTimeString('zh-CN', {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </div>

        {/* Feedback bar for last AI message */}
        {isLastAI && isAssistant && !message.content.startsWith('错误:') && feedbackBar}
      </div>
    </div>
  );
}
