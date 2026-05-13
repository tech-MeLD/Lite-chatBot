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

  // AbortController for timeout (120s should be enough for CPU inference)
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 120000);

  try {
    console.log('[SSE] Opening connection to', `${API_BASE}/chat/send`);
    const response = await fetch(`${API_BASE}/chat/send`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ session_id: sessionId, content }),
      signal: controller.signal,
    });

    if (!response.ok) {
      if (response.status === 401) {
        clearToken();
        window.location.href = '/';
        return;
      }
      const detail = await response.text();
      console.error('[SSE] HTTP error:', response.status, detail);
      onError(detail || `HTTP ${response.status}`);
      return;
    }

    console.log('[SSE] Connection opened, starting stream read');
    const reader = response.body!.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let receivedDone = false;
    let hadError = false;
    let eventsParsed = 0;

    while (true) {
      const { done, value } = await reader.read();

      if (value) {
        const chunk = decoder.decode(value, { stream: true });
        console.log('[SSE] Received chunk, length:', chunk.length, 'preview:', chunk.substring(0, 80));
        buffer += chunk;

        // SSE events are separated by double-newline.
        // Handle both \n\n (Unix) and \r\n\r\n (HTTP line endings that may leak through).
        while (containsEventSeparator(buffer)) {
          const { eventStr, remaining } = extractNextEvent(buffer);
          buffer = remaining;

          // Skip comment lines (SSE ping: ": ping - ...")
          const dataLine = extractDataLine(eventStr);
          if (!dataLine) {
            // Comment or empty event, skip
            continue;
          }

          console.log('[SSE] Parsing event line:', dataLine.substring(0, 100));
          try {
            const data = JSON.parse(dataLine) as SSEEvent;
            eventsParsed++;
            console.log('[SSE] Event #' + eventsParsed + ' type:', data.type);

            if (data.type === 'error') {
              hadError = true;
              console.warn('[SSE] Error event received:', data.data?.message);
              onError(data.data.message || '未知错误');
            } else if (data.type === 'done') {
              receivedDone = true;
              console.log('[SSE] Done event received, answer:', (data.data?.answer || '').substring(0, 50));
              onEvent(data);
              onDone();
            } else {
              onEvent(data);
            }
          } catch (parseErr) {
            console.error('[SSE] JSON parse failed for line:', dataLine.substring(0, 100), 'Error:', parseErr);
          }
        }
      }

      if (done) {
        console.log('[SSE] Stream ended (reader done). receivedDone:', receivedDone, 'hadError:', hadError);
        break;
      }
    }

    // Try parsing any remaining data in the buffer
    if (!receivedDone && !hadError && buffer.trim()) {
      const trimmed = buffer.trim();
      console.log('[SSE] Remaining buffer after stream end:', trimmed.substring(0, 200));
      const dataLine = extractDataLine(trimmed);
      if (dataLine) {
        try {
          const data = JSON.parse(dataLine) as SSEEvent;
          console.log('[SSE] Final buffer parsed, type:', data.type);
          if (data.type === 'done') {
            receivedDone = true;
            onEvent(data);
            onDone();
          }
        } catch {
          console.error('[SSE] Final buffer JSON parse failed');
        }
      }
    }

    // Only report disconnect if we never got done OR error event
    if (!receivedDone && !hadError) {
      console.error('[SSE] Disconnect without done or error. Total events:', eventsParsed, 'Remaining buffer:', buffer.substring(0, 200));
      onError('连接意外断开，请重新发送消息');
    }
  } catch (err) {
    console.error('[SSE] Fatal error:', err);
    if (err instanceof DOMException && err.name === 'AbortError') {
      onError('回复超时，AI正在处理中，请稍后再试');
    } else if (err instanceof TypeError && err.message === 'Failed to fetch') {
      onError('无法连接到服务器，请检查网络后重试');
    } else {
      onError(err instanceof Error ? err.message : '网络连接错误');
    }
  } finally {
    clearTimeout(timeoutId);
  }
}

// --- SSE parsing helpers ---

/**
 * Check if buffer contains an SSE event separator.
 * Handles both \n\n (standard SSE) and \r\n\r\n (some HTTP proxies).
 */
function containsEventSeparator(buffer: string): boolean {
  return buffer.includes('\n\n') || buffer.includes('\r\n\r\n');
}

/**
 * Extract the next complete SSE event from the buffer.
 * Returns the event string and the remaining buffer after the separator.
 */
function extractNextEvent(buffer: string): { eventStr: string; remaining: string } {
  // Try \n\n first (most common)
  const doubleIdx = buffer.indexOf('\n\n');
  if (doubleIdx !== -1) {
    return {
      eventStr: buffer.substring(0, doubleIdx),
      remaining: buffer.substring(doubleIdx + 2),
    };
  }
  // Fallback to \r\n\r\n
  const crlfIdx = buffer.indexOf('\r\n\r\n');
  return {
    eventStr: buffer.substring(0, crlfIdx),
    remaining: buffer.substring(crlfIdx + 4),
  };
}

/**
 * Extract the first data line from an SSE event string.
 * An SSE event can have multiple "data:" lines; we take the first one.
 * Returns the content after "data: " or null if no data line found.
 */
function extractDataLine(eventStr: string): string | null {
  const lines = eventStr.split('\n');
  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed.startsWith('data: ')) {
      return trimmed.slice(6);  // Return content after "data: "
    }
    if (trimmed.startsWith('data:')) {
      return trimmed.slice(5);  // Handle "data:" without space
    }
  }
  return null;  // Comment or empty event
}
