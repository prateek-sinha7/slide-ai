'use client';

import React, { useState, FormEvent } from 'react';

interface ValidationErrors {
  topic?: string;
  tone?: string;
  slideCount?: string;
  general?: string;
}

export interface PresentationPrompt {
  topic: string;
  tone?: 'formal' | 'casual' | 'fun' | 'professional';
  slideCount?: number;
}

interface PromptFormProps {
  onSubmit: (prompt: PresentationPrompt) => Promise<void>;
  isLoading: boolean;
}

export default function PromptForm({ onSubmit, isLoading }: PromptFormProps) {
  const [topic, setTopic] = useState('');
  const [tone, setTone] = useState<string>('');
  const [slideCount, setSlideCount] = useState<string>('');
  const [errors, setErrors] = useState<ValidationErrors>({});

  const validateForm = (): boolean => {
    const newErrors: ValidationErrors = {};

    // Topic validation (required, 1-500 characters)
    if (!topic || topic.trim().length === 0) {
      newErrors.topic = 'Topic is required';
    } else if (topic.length > 500) {
      newErrors.topic = 'Topic must be 500 characters or less';
    }

    // Tone validation (optional, must be valid enum if provided)
    if (tone && !['formal', 'casual', 'fun', 'professional'].includes(tone)) {
      newErrors.tone = 'Invalid tone selected';
    }

    // Slide count validation (optional, must be 5-20 if provided)
    if (slideCount) {
      const count = parseInt(slideCount, 10);
      if (isNaN(count)) {
        newErrors.slideCount = 'Slide count must be a number';
      } else if (count < 5 || count > 20) {
        newErrors.slideCount = 'Slide count must be between 5 and 20';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setErrors({});

    // Client-side validation
    if (!validateForm()) {
      return;
    }

    // Build prompt object
    const prompt: PresentationPrompt = {
      topic: topic.trim(),
    };

    // Add optional fields if provided
    if (tone) {
      prompt.tone = tone as 'formal' | 'casual' | 'fun' | 'professional';
    }

    if (slideCount) {
      prompt.slideCount = parseInt(slideCount, 10);
    }

    try {
      await onSubmit(prompt);
      // Clear form on success
      setTopic('');
      setTone('');
      setSlideCount('');
    } catch (error) {
      if (error instanceof Error) {
        setErrors({ general: error.message });
      } else {
        setErrors({ general: 'An unexpected error occurred' });
      }
    }
  };

  const toneOptions = [
    { value: 'professional', label: 'Professional', icon: '💼', description: 'Business-ready presentations' },
    { value: 'formal', label: 'Formal', icon: '🎓', description: 'Academic and serious tone' },
    { value: 'casual', label: 'Casual', icon: '😊', description: 'Relaxed and friendly' },
    { value: 'fun', label: 'Fun', icon: '🎉', description: 'Engaging and playful' },
  ];

  return (
    <div className="prompt-form-container">
      <div className="prompt-form-card">
        <div className="form-header">
          <h2 className="form-title">Create Your Presentation</h2>
          <p className="form-subtitle">Fill in the details below to generate your AI-powered presentation</p>
        </div>

        <form onSubmit={handleSubmit} className="prompt-form">
          {/* Topic Input */}
          <div className="form-group">
            <label htmlFor="topic" className="form-label">
              Presentation Topic <span className="required">*</span>
            </label>
            <div className="input-wrapper">
              <input
                type="text"
                id="topic"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                disabled={isLoading}
                placeholder="e.g., Climate Change, Artificial Intelligence, Marketing Strategy..."
                maxLength={500}
                aria-invalid={!!errors.topic}
                aria-describedby={errors.topic ? 'topic-error' : undefined}
                aria-required="true"
                className="form-input"
              />
              <div className="char-count">{topic.length}/500</div>
            </div>
            {errors.topic && (
              <span id="topic-error" className="error-message">
                {errors.topic}
              </span>
            )}
          </div>

          {/* Tone Selection */}
          <div className="form-group">
            <label className="form-label">Presentation Tone</label>
            <div className="tone-grid">
              {toneOptions.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => setTone(tone === option.value ? '' : option.value)}
                  disabled={isLoading}
                  className={`tone-option ${tone === option.value ? 'selected' : ''}`}
                >
                  <span className="tone-icon">{option.icon}</span>
                  <span className="tone-label">{option.label}</span>
                  <span className="tone-description">{option.description}</span>
                </button>
              ))}
            </div>
            {errors.tone && (
              <span className="error-message">{errors.tone}</span>
            )}
          </div>

          {/* Slide Count */}
          <div className="form-group">
            <label htmlFor="slideCount" className="form-label">
              Number of Slides
            </label>
            <div className="slide-count-wrapper">
              <input
                type="range"
                id="slideCount"
                value={slideCount || '8'}
                onChange={(e) => setSlideCount(e.target.value)}
                disabled={isLoading}
                min={5}
                max={20}
                className="slide-range"
              />
              <div className="slide-count-display">
                <span className="slide-count-value">{slideCount || '8'}</span>
                <span className="slide-count-label">slides</span>
              </div>
            </div>
            <div className="slide-count-labels">
              <span>5</span>
              <span>20</span>
            </div>
            {errors.slideCount && (
              <span className="error-message">{errors.slideCount}</span>
            )}
          </div>

          {/* General Error */}
          {errors.general && (
            <div className="error-message general-error">{errors.general}</div>
          )}

          {/* Submit Button */}
          <button type="submit" disabled={isLoading} className="btn btn-primary btn-large">
            {isLoading ? (
              <>
                <span className="spinner-small"></span>
                Generating...
              </>
            ) : (
              <>
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M10 2L13.09 8.26L20 9.27L15 14.14L16.18 20.02L10 16.77L3.82 20.02L5 14.14L0 9.27L6.91 8.26L10 2Z" fill="currentColor"/>
                </svg>
                Generate Presentation
              </>
            )}
          </button>
        </form>
      </div>

      <style jsx>{`
        .prompt-form-container {
          margin: 0 auto;
        }

        .prompt-form-card {
          background: rgba(255, 255, 255, 0.95);
          backdrop-filter: blur(10px);
          border-radius: var(--radius-xl);
          box-shadow: var(--shadow-xl);
          padding: 2rem;
        }

        .form-header {
          text-align: center;
          margin-bottom: 2rem;
        }

        .form-title {
          font-size: 1.75rem;
          font-weight: 700;
          color: var(--text-primary);
          margin: 0 0 0.5rem 0;
        }

        .form-subtitle {
          font-size: 0.9375rem;
          color: var(--text-secondary);
          margin: 0;
        }

        .prompt-form {
          display: flex;
          flex-direction: column;
          gap: 1.5rem;
        }

        .form-label {
          display: block;
          font-size: 0.875rem;
          font-weight: 600;
          color: var(--text-primary);
          margin-bottom: 0.75rem;
        }

        .input-wrapper {
          position: relative;
        }

        .form-input {
          width: 100%;
          padding: 0.875rem 1rem;
          font-size: 0.9375rem;
          line-height: 1.5;
          color: var(--text-primary);
          background: var(--bg-primary);
          border: 2px solid var(--border-color);
          border-radius: var(--radius-md);
          transition: all 0.2s ease;
        }

        .form-input:focus {
          outline: none;
          border-color: var(--primary-color);
          box-shadow: 0 0 0 3px var(--primary-light);
        }

        .form-input:disabled {
          background: var(--bg-tertiary);
          cursor: not-allowed;
        }

        .char-count {
          position: absolute;
          right: 1rem;
          top: 50%;
          transform: translateY(-50%);
          font-size: 0.75rem;
          color: var(--text-light);
          pointer-events: none;
        }

        .tone-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
          gap: 0.75rem;
        }

        .tone-option {
          display: flex;
          flex-direction: column;
          align-items: center;
          padding: 1rem;
          background: var(--bg-secondary);
          border: 2px solid var(--border-color);
          border-radius: var(--radius-md);
          cursor: pointer;
          transition: all 0.2s ease;
          text-align: center;
        }

        .tone-option:hover:not(:disabled) {
          border-color: var(--primary-color);
          background: var(--primary-light);
          transform: translateY(-2px);
        }

        .tone-option.selected {
          border-color: var(--primary-color);
          background: var(--primary-light);
          box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
        }

        .tone-option:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .tone-icon {
          font-size: 1.5rem;
          margin-bottom: 0.5rem;
        }

        .tone-label {
          font-size: 0.875rem;
          font-weight: 600;
          color: var(--text-primary);
          margin-bottom: 0.25rem;
        }

        .tone-description {
          font-size: 0.75rem;
          color: var(--text-secondary);
        }

        .slide-count-wrapper {
          display: flex;
          align-items: center;
          gap: 1rem;
        }

        .slide-range {
          flex: 1;
          height: 6px;
          border-radius: 3px;
          background: var(--border-color);
          outline: none;
          -webkit-appearance: none;
        }

        .slide-range::-webkit-slider-thumb {
          -webkit-appearance: none;
          appearance: none;
          width: 20px;
          height: 20px;
          border-radius: 50%;
          background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
          cursor: pointer;
          box-shadow: var(--shadow-sm);
        }

        .slide-range::-moz-range-thumb {
          width: 20px;
          height: 20px;
          border-radius: 50%;
          background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
          cursor: pointer;
          border: none;
          box-shadow: var(--shadow-sm);
        }

        .slide-count-display {
          display: flex;
          flex-direction: column;
          align-items: center;
          min-width: 60px;
          padding: 0.5rem;
          background: var(--primary-light);
          border-radius: var(--radius-md);
        }

        .slide-count-value {
          font-size: 1.5rem;
          font-weight: 700;
          color: var(--primary-color);
          line-height: 1;
        }

        .slide-count-label {
          font-size: 0.75rem;
          color: var(--text-secondary);
        }

        .slide-count-labels {
          display: flex;
          justify-content: space-between;
          font-size: 0.75rem;
          color: var(--text-light);
          margin-top: 0.25rem;
        }

        .btn-large {
          padding: 1rem 2rem;
          font-size: 1rem;
          font-weight: 600;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 0.5rem;
        }

        .spinner-small {
          width: 16px;
          height: 16px;
          border: 2px solid rgba(255, 255, 255, 0.3);
          border-top-color: white;
          border-radius: 50%;
          animation: spin 0.8s linear infinite;
        }

        .general-error {
          padding: 0.75rem;
          background: #fee;
          border: 1px solid #fcc;
          border-radius: var(--radius-md);
          text-align: center;
        }

        @media (max-width: 768px) {
          .prompt-form-card {
            padding: 1.5rem;
          }

          .form-title {
            font-size: 1.5rem;
          }

          .tone-grid {
            grid-template-columns: repeat(2, 1fr);
          }
        }
      `}</style>
    </div>
  );
}
