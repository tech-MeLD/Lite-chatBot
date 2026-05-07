export interface User {
  id: string;
  nickname: string;
  avatar_url: string | null;
  is_active: boolean;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Session {
  id: string;
  title: string | null;
  status: 'active' | 'paused' | 'closed';
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  intent: string | null;
  created_at: string;
}

export interface Feedback {
  id: string;
  message_id: string;
  rating: number;
  is_liked: boolean | null;
  comment: string | null;
}

export interface SSEEvent {
  type: 'intent' | 'thinking' | 'error' | 'done';
  data: {
    intent?: string;
    confidence?: number;
    message?: string;
    answer?: string;
    message_id?: string;
    needs_human?: boolean;
    rag_sources?: string[];
  };
}

export interface FeedbackStats {
  total_feedbacks: number;
  avg_rating: number;
  like_count: number;
  dislike_count: number;
}
