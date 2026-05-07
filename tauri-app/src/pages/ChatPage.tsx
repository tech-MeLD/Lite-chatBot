import { useState, useEffect, useCallback } from 'react';
import type { Session, Message } from '../types';
import { useAuth } from '../contexts/AuthContext';
import { useChat } from '../hooks/useChat';
import { getSessions, createSession, getMessages, deleteSession } from '../api/client';
import SessionList from '../components/SessionList';
import ChatWindow from '../components/ChatWindow';

export default function ChatPage() {
  const { user, logout } = useAuth();
  const { messages, isStreaming, currentIntent, send, clearMessages, setMessages } =
    useChat();

  const [sessions, setSessions] = useState<Session[]>([]);
  const [selectedSession, setSelectedSession] = useState<Session | null>(null);
  const [sessionsLoading, setSessionsLoading] = useState(false);
  const [messagesLoading, setMessagesLoading] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  // Load sessions
  const loadSessions = useCallback(async () => {
    setSessionsLoading(true);
    try {
      const data = await getSessions();
      setSessions(data);
    } catch (err) {
      console.error('Load sessions failed:', err);
    } finally {
      setSessionsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  // Create new session
  async function handleCreateSession() {
    try {
      const session = await createSession();
      setSessions((prev) => [session, ...prev]);
      setSelectedSession(session);
      clearMessages();
    } catch (err) {
      console.error('Create session failed:', err);
    }
  }

  // Select session and load messages
  async function handleSelectSession(session: Session) {
    setSelectedSession(session);
    setMessagesLoading(true);
    try {
      const msgs = await getMessages(session.id);
      setMessages(msgs);
    } catch (err) {
      console.error('Load messages failed:', err);
    } finally {
      setMessagesLoading(false);
    }
  }

  // Send message
  async function handleSend(content: string) {
    if (!selectedSession) {
      // Auto-create session if none selected
      try {
        const session = await createSession();
        setSessions((prev) => [session, ...prev]);
        setSelectedSession(session);
        await send(session.id, content);
      } catch (err) {
        console.error('Send message failed:', err);
      }
    } else {
      await send(selectedSession.id, content);
    }
  }

  // Delete session
  async function handleDelete(session: Session) {
    setDeleteError(null);
    try {
      await deleteSession(session.id);
      setSessions((prev) => prev.filter((s) => s.id !== session.id));
      if (selectedSession?.id === session.id) {
        setSelectedSession(null);
        clearMessages();
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : '删除失败';
      console.error('Delete session failed:', err);
      setDeleteError(msg);
    }
  }

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <header className="h-14 bg-white border-b border-gray-200 flex items-center justify-between px-4 shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-primary-500 rounded-lg flex items-center justify-center">
            <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
            </svg>
          </div>
          <h1 className="font-semibold text-gray-800">AI 智能客服</h1>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-500">{user?.nickname || '用户'}</span>
          <button
            onClick={logout}
            className="text-sm text-gray-400 hover:text-gray-600 transition-colors"
          >
            退出
          </button>
        </div>
      </header>

      {/* Body */}
      <div className="flex flex-1 overflow-hidden">
        <SessionList
          sessions={sessions}
          selectedId={selectedSession?.id || null}
          onSelect={handleSelectSession}
          onCreate={handleCreateSession}
          onDelete={handleDelete}
          loading={sessionsLoading}
          deleteError={deleteError}
          onDismissError={() => setDeleteError(null)}
        />

        <main className="flex-1 flex flex-col bg-gray-50 min-w-0">
          {selectedSession ? (
            <ChatWindow
              messages={messages}
              isStreaming={isStreaming}
              currentIntent={currentIntent}
              onSend={handleSend}
            />
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center text-gray-400">
                <svg className="w-20 h-20 mx-auto mb-4 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1}
                    d="M17 8h2a2 2 0 012 2v6a2 2 0 01-2 2h-2v4l-4-4H9a1.994 1.994 0 01-1.414-.586m0 0L11 14h4a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2v4l.586-.586z" />
                </svg>
                <p className="text-sm">选择一个会话或新建对话</p>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
