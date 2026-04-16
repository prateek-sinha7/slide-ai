'use client';

import React from 'react';

interface ErrorDisplayProps {
  error: string | null;
  onRetry?: () => void;
  onDismiss?: () => void;
}

// Map technical error codes/messages to user-friendly messages
const ERROR_MESSAGES: Record<string, string> = {
  AUTH_INVALID_CREDENTIALS: 'Username or password is incorrect. Please try again.',
  VALIDATION_TOPIC_LENGTH: 'Please enter a topic between 1 and 500 characters.',
  GENERATION_TIMEOUT:
    'Generation is taking longer than expected. Try reducing the number of slides.',
  GENERATION_LLM_FAILURE:
    "We're having trouble generating your presentation. Please try again in a moment.",
  FILE_CREATION_ERROR: 'Unable to create your presentation file. Please try again.',
  NETWORK_ERROR: 'Network error. Please check your connection and try again.',
  SERVICE_UNAVAILABLE: 'Service is temporarily unavailable. Please try again later.',
  AUTHENTICATION_REQUIRED: 'Authentication failed. Please log in again.',
  PRESENTATION_NOT_FOUND: 'Presentation not found or has expired.',
};

// Determine if an error is retryable based on its content
function isRetryable(error: string): boolean {
  const retryablePatterns = [
    'network error',
    'temporarily unavailable',
    'try again',
    'timeout',
    'service unavailable',
    'generation failed',
    'unable to create',
  ];

  const lowerError = error.toLowerCase();
  return retryablePatterns.some((pattern) => lowerError.includes(pattern));
}

// Get user-friendly error message
function getUserFriendlyMessage(error: string): string {
  // Check if error matches a known error code
  for (const [code, message] of Object.entries(ERROR_MESSAGES)) {
    if (error.includes(code)) {
      return message;
    }
  }

  // Check if error contains known patterns
  if (error.toLowerCase().includes('authentication')) {
    return ERROR_MESSAGES.AUTHENTICATION_REQUIRED;
  }
  if (error.toLowerCase().includes('network')) {
    return ERROR_MESSAGES.NETWORK_ERROR;
  }
  if (error.toLowerCase().includes('timeout')) {
    return ERROR_MESSAGES.GENERATION_TIMEOUT;
  }
  if (error.toLowerCase().includes('unavailable')) {
    return ERROR_MESSAGES.SERVICE_UNAVAILABLE;
  }

  // Return original error if no mapping found
  return error;
}

export default function ErrorDisplay({ error, onRetry, onDismiss }: ErrorDisplayProps) {
  if (!error) {
    return null;
  }

  const friendlyMessage = getUserFriendlyMessage(error);
  const canRetry = isRetryable(error) && onRetry;

  return (
    <div className="error-container" role="alert" aria-live="assertive">
      <div className="error-card">
        <div className="error-icon-wrapper">
          <div className="error-icon">
            <svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="24" cy="24" r="20" stroke="currentColor" strokeWidth="3" />
              <path d="M24 16V26" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
              <circle cx="24" cy="32" r="2" fill="currentColor" />
            </svg>
          </div>
        </div>

        <div className="error-content">
          <h3 className="error-title">Oops! Something went wrong</h3>
          <p className="error-message">{friendlyMessage}</p>

          <div className="error-actions">
            {canRetry && (
              <button className="btn btn-primary" onClick={onRetry}>
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M14 8C14 11.3137 11.3137 14 8 14C4.68629 14 2 11.3137 2 8C2 4.68629 4.68629 2 8 2C10.3 2 12.3 3.2 13.4 5M13.4 2V5H10.4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
                Try Again
              </button>
            )}
            {onDismiss && (
              <button className="btn btn-secondary" onClick={onDismiss}>
                Dismiss
              </button>
            )}
          </div>
        </div>
      </div>

      <style jsx>{`
        .error-container {
          display: flex;
          justify-content: center;
          padding: 1rem 0;
        }

        .error-card {
          background: rgba(255, 255, 255, 0.95);
          backdrop-filter: blur(10px);
          border-radius: var(--radius-xl);
          box-shadow: var(--shadow-xl);
          padding: 2rem;
          max-width: 600px;
          width: 100%;
          border: 2px solid var(--error-color);
        }

        .error-icon-wrapper {
          display: flex;
          justify-content: center;
          margin-bottom: 1.5rem;
        }

        .error-icon {
          width: 64px;
          height: 64px;
          border-radius: 50%;
          background: linear-gradient(135deg, #fee, #fcc);
          display: flex;
          align-items: center;
          justify-content: center;
          color: var(--error-color);
          animation: shake 0.5s ease;
        }

        @keyframes shake {
          0%, 100% {
            transform: translateX(0);
          }
          25% {
            transform: translateX(-10px);
          }
          75% {
            transform: translateX(10px);
          }
        }

        .error-content {
          text-align: center;
        }

        .error-title {
          font-size: 1.5rem;
          font-weight: 700;
          color: var(--text-primary);
          margin: 0 0 1rem 0;
        }

        .error-message {
          font-size: 1rem;
          color: var(--text-secondary);
          margin: 0 0 1.5rem 0;
          line-height: 1.6;
        }

        .error-actions {
          display: flex;
          gap: 0.75rem;
          justify-content: center;
          flex-wrap: wrap;
        }

        .btn {
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }

        @media (max-width: 768px) {
          .error-card {
            padding: 1.5rem;
          }

          .error-title {
            font-size: 1.25rem;
          }

          .error-actions {
            flex-direction: column;
          }

          .btn {
            width: 100%;
          }
        }
      `}</style>
    </div>
  );
}
