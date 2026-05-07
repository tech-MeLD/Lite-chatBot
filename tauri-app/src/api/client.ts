import type { LoginResponse, Session, Message, Feedback, SSEEvent } from '../types';

const API_BASE = (import.meta.env.VITE_API_BASE as string || 'http://localhost:8000') + '/api/v1';

function getToken(): string | null {
  return localStorage.getItem('access_token');
}

function setToken(token: string): void {
  localStorage.setItem('access_token', token);
}

export function clearToken(): void {
  localStorage.removeItem('access_token');
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  const token = getToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    if (response.status === 401) {
      clearToken();
      window.location.href = '/';
    }
    const detail = await response.text();
    throw new Error(detail || `HTTP ${response.status}`);
  }

  // 204 No Content
  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

// Auth
export async function login(code: string): Promise<LoginResponse> {
  const data = await request<LoginResponse>('POST', '/auth/login', { code });
  setToken(data.access_token);
  return data;
}

export async function getMe() {
  return request<{
    id: string;
    nickname: string;
    avatar_url: string | null;
    is_active: boolean;
  }>('GET', '/auth/me');
}

// Sessions
export async function getSessions(limit = 50, offset = 0): Promise<Session[]> {
  return request<Session[]>('GET', `/sessions?limit=${limit}&offset=${offset}`);
}

export async function createSession(title?: string): Promise<Session> {
  return request<Session>('POST', '/sessions', { title });
}

export async function getSession(sessionId: string): Promise<Session> {
  return request<Session>('GET', `/sessions/${sessionId}`);
}

export async function deleteSession(sessionId: string): Promise<void> {
  return request<void>('DELETE', `/sessions/${sessionId}`);
}

// Messages
export async function getMessages(
  sessionId: string,
  limit = 100,
  offset = 0
): Promise<Message[]> {
  return request<Message[]>(
    'GET',
    `/sessions/${sessionId}/messages?limit=${limit}&offset=${offset}`
  );
}

// Feedback
export async function submitFeedback(
  messageId: string,
  rating: number,
  isLiked?: boolean | null,
  comment?: string
): Promise<Feedback> {
  return request<Feedback>('POST', '/feedback', {
    message_id: messageId,
    rating,
    is_liked: isLiked,
    comment,
  });
}

// SSE Chat - uses fetch + ReadableStream (EventSource doesn't support POST + custom headers)
export async function sendMessageSSE(
  sessionId: string,
  content: string,
  onEvent: (event: SSEEvent) => void,
  onError: (error: string) => void,
  onDone: () => void
): Promise<void> {
  const token = getToken();
  if (!token) {
    onError('未登录');
    return;
  }

  try {
    const response = await fetch(`${API_BASE}/chat/send`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ session_id: sessionId, content }),
    });

    if (!response.ok) {
      if (response.status === 401) {
        clearToken();
        window.location.href = '/';
        return;
      }
      const detail = await response.text();
      onError(detail || `HTTP ${response.status}`);
      return;
    }

    const reader = response.body!.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let receivedDone = false;
    let hadError = false;

    while (true) {
      const { done, value } = await reader.read();

      // Process any data before checking done flag.
      // This is critical: some browser implementations may return
      // { value: lastChunk, done: true } for the final frame.
      if (value) {
        buffer += decoder.decode(value, { stream: true });

        // SSE events are separated by \n\n
        while (buffer.includes('\n\n')) {
          const idx = buffer.indexOf('\n\n');
          const eventStr = buffer.substring(0, idx);
          buffer = buffer.substring(idx + 2);

          if (eventStr.startsWith('data: ')) {
            try {
              const data = JSON.parse(eventStr.slice(6)) as SSEEvent;

              if (data.type === 'error') {
                hadError = true;
                onError(data.data.message || '未知错误');
                // After receiving error, we can stop reading — the stream will end
              } else if (data.type === 'done') {
                receivedDone = true;
                onEvent(data);
                onDone();
              } else {
                onEvent(data);
              }
            } catch {
              // Skip malformed JSON - may be split across chunks
            }
          }
        }
      }

      if (done) break;
    }

    // Try parsing any remaining data in the buffer
    if (!receivedDone && !hadError && buffer.trim()) {
      const trimmed = buffer.trim();
      if (trimmed.startsWith('data: ')) {
        try {
          const data = JSON.parse(trimmed.slice(6)) as SSEEvent;
          if (data.type === 'done') {
            receivedDone = true;
            onEvent(data);
            onDone();
          }
        } catch {
          // Final parse failed, data was incomplete
        }
      }
    }

    // Only report disconnect if we never got done OR error event
    if (!receivedDone && !hadError) {
      onError('连接意外断开');
    }
  } catch (err) {
    onError(err instanceof Error ? err.message : '网络连接错误');
  }
}
