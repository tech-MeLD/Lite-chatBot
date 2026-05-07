import { useState } from 'react';
import type { Session } from '../types';

interface SessionListProps {
  sessions: Session[];
  selectedId: string | null;
  onSelect: (session: Session) => void;
  onCreate: () => void;
  onDelete: (session: Session) => void;
  loading: boolean;
  deleteError: string | null;
  onDismissError: () => void;
}

export default function SessionList({
  sessions,
  selectedId,
  onSelect,
  onCreate,
  onDelete,
  loading,
  deleteError,
  onDismissError,
}: SessionListProps) {
  const [confirmId, setConfirmId] = useState<string | null>(null);

  function handleDeleteClick(e: React.MouseEvent, session: Session) {
    e.stopPropagation();
    if (confirmId === session.id) {
      onDelete(session);
      setConfirmId(null);
    } else {
      setConfirmId(session.id);
    }
  }

  function handleCancelConfirm(e: React.MouseEvent) {
    e.stopPropagation();
    setConfirmId(null);
  }

  return (
    <div className="w-[280px] bg-white border-r border-gray-200 flex flex-col h-full shrink-0">
      <div className="p-4 border-b border-gray-100">
        {deleteError && (
          <div className="mb-3 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-700 flex items-center justify-between">
            <span>{deleteError}</span>
            <button onClick={onDismissError} className="text-red-400 hover:text-red-600 ml-2">&times;</button>
          </div>
        )}
        <button
          onClick={onCreate}
          disabled={loading}
          className="w-full py-2.5 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 disabled:opacity-50 transition-colors flex items-center justify-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          新建对话
        </button>
      </div>

      <div className="flex-1 overflow-y-auto">
        {sessions.length === 0 ? (
          <div className="p-6 text-center text-gray-400 text-sm">
            {loading ? '加载中...' : '暂无对话记录'}
          </div>
        ) : (
          sessions.map((session) => (
            <div
              key={session.id}
              onClick={() => { onSelect(session); setConfirmId(null); }}
              className={`group relative px-4 py-3 cursor-pointer border-b border-gray-50 transition-colors hover:bg-gray-50 ${
                selectedId === session.id
                  ? 'bg-primary-50 border-l-2 border-l-primary-500'
                  : ''
              }`}
            >
              <div className="text-sm font-medium text-gray-800 truncate pr-6">
                {session.title || '新对话'}
              </div>
              <div className="text-xs text-gray-400 mt-1">
                {new Date(session.updated_at).toLocaleDateString('zh-CN')}
              </div>

              {/* Delete button */}
              {confirmId === session.id ? (
                <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                  <button
                    onClick={(e) => handleDeleteClick(e, session)}
                    className="text-xs bg-red-500 text-white px-2 py-0.5 rounded hover:bg-red-600 transition-colors"
                    title="确认删除"
                  >
                    确认
                  </button>
                  <button
                    onClick={handleCancelConfirm}
                    className="text-xs bg-gray-300 text-gray-700 px-2 py-0.5 rounded hover:bg-gray-400 transition-colors"
                    title="取消"
                  >
                    取消
                  </button>
                </div>
              ) : (
                <button
                  onClick={(e) => handleDeleteClick(e, session)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500 transition-all"
                  title="删除对话"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
