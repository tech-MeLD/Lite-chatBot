import { useState } from 'react';
import { submitFeedback } from '../api/client';

interface FeedbackBarProps {
  messageId: string;
}

export default function FeedbackBar({ messageId }: FeedbackBarProps) {
  const [liked, setLiked] = useState<boolean | null>(null);
  const [rating, setRating] = useState<number>(0);
  const [hoverRating, setHoverRating] = useState<number>(0);
  const [submitted, setSubmitted] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  async function handleLike(isLike: boolean) {
    if (submitted) return;
    setSubmitting(true);
    try {
      await submitFeedback(messageId, liked === isLike ? 0 : (isLike ? 5 : 1), isLike ? true : false);
      setLiked(liked === isLike ? null : isLike);
      if (liked !== isLike) setSubmitted(true);
    } catch {
      // silently fail
    } finally {
      setSubmitting(false);
    }
  }

  async function handleRating(value: number) {
    if (submitted) return;
    setSubmitting(true);
    try {
      await submitFeedback(messageId, value, null);
      setRating(value);
      setSubmitted(true);
    } catch {
      // silently fail
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex items-center gap-2 mt-2 text-gray-400">
      {submitted ? (
        <span className="text-xs text-green-500">感谢反馈</span>
      ) : (
        <>
          <button
            onClick={() => handleLike(true)}
            disabled={submitting}
            className={`p-1 rounded hover:bg-gray-100 transition-colors ${liked === true ? 'text-primary-500' : ''}`}
            title="好评"
          >
            <svg className="w-4 h-4" fill={liked === true ? 'currentColor' : 'none'} viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" />
            </svg>
          </button>

          <button
            onClick={() => handleLike(false)}
            disabled={submitting}
            className={`p-1 rounded hover:bg-gray-100 transition-colors ${liked === false ? 'text-red-500' : ''}`}
            title="差评"
          >
            <svg className="w-4 h-4" fill={liked === false ? 'currentColor' : 'none'} viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.736 3h4.018a2 2 0 01.485.06l3.76.94m-7 10v5a2 2 0 002 2h.096c.5 0 .905-.405.905-.904 0-.715.211-1.413.608-2.008L17 13V4m-7 10h2m5-10h2a2 2 0 012 2v6a2 2 0 01-2 2h-2.5" />
            </svg>
          </button>

          <span className="text-xs">|</span>

          {/* Star rating */}
          <div className="flex items-center">
            {[1, 2, 3, 4, 5].map((star) => (
              <button
                key={star}
                onClick={() => handleRating(star)}
                onMouseEnter={() => setHoverRating(star)}
                onMouseLeave={() => setHoverRating(0)}
                disabled={submitting}
                className="p-0.5 transition-colors"
                title={`${star} 星`}
              >
                <svg
                  className="w-4 h-4"
                  fill={(hoverRating || rating) >= star ? '#f59e0b' : 'none'}
                  viewBox="0 0 24 24"
                  stroke={(hoverRating || rating) >= star ? '#f59e0b' : 'currentColor'}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.5}
                    d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"
                  />
                </svg>
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
