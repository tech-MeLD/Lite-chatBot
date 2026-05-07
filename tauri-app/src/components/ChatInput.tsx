import { useState, type FormEvent, type KeyboardEvent } from 'react';

interface ChatInputProps {
  onSend: (content: string) => void;
  disabled: boolean;
}

export default function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [value, setValue] = useState('');

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!value.trim() || disabled) return;
    onSend(value.trim());
    setValue('');
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!value.trim() || disabled) return;
      onSend(value.trim());
      setValue('');
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="border-t border-gray-200 bg-white p-4"
    >
      <div className="flex items-end gap-2">
        <textarea
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="输入您的问题，Enter 发送，Shift+Enter 换行"
          rows={1}
          disabled={disabled}
          className="flex-1 resize-none px-4 py-2.5 border border-gray-300 rounded-xl outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors text-sm disabled:bg-gray-100"
        />
        <button
          type="submit"
          disabled={disabled || !value.trim()}
          className="px-5 py-2.5 bg-primary-600 text-white rounded-xl text-sm font-medium hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shrink-0"
        >
          {disabled ? (
            <svg className="animate-spin h-4 w-4 mx-auto" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          ) : (
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          )}
        </button>
      </div>
    </form>
  );
}
