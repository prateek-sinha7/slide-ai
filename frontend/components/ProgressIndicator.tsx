'use client';

import React, { useEffect, useState, useRef } from 'react';

interface ProgressIndicatorProps {
  isLoading: boolean;
  status?: string;
  estimatedTimeRemaining?: number; // in seconds
}

export default function ProgressIndicator({
  isLoading,
  status,
  estimatedTimeRemaining,
}: ProgressIndicatorProps) {
  const [elapsedTime, setElapsedTime] = useState(0);
  const [progress, setProgress] = useState(0);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // Main timer effect
  useEffect(() => {
    if (!isLoading) {
      setElapsedTime(0);
      setProgress(0);
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
      return;
    }

    // Start timer
    timerRef.current = setInterval(() => {
      setElapsedTime((prev) => prev + 1);
    }, 1000);

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    };
  }, [isLoading]);

  // Update progress based on elapsed time
  useEffect(() => {
    if (!isLoading) return;

    if (elapsedTime < 10) {
      setProgress(5);
    } else if (elapsedTime < 30) {
      setProgress(20);
    } else if (elapsedTime < 60) {
      setProgress(40);
    } else if (elapsedTime < 90) {
      setProgress(60);
    } else if (elapsedTime < 120) {
      setProgress(75);
    } else if (elapsedTime < 150) {
      setProgress(90);
    } else {
      setProgress(95);
    }
  }, [elapsedTime, isLoading]);

  // Override progress when downloading
  useEffect(() => {
    if (status && status.toLowerCase().includes('download')) {
      setProgress(98);
    }
  }, [status]);

  if (!isLoading) {
    return null;
  }

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Determine current status message
  const getCurrentStatus = (): string => {
    if (status) return status;
    
    if (elapsedTime < 10) return 'Initializing generation...';
    if (elapsedTime < 30) return 'Planning presentation structure...';
    if (elapsedTime < 60) return 'Generating content...';
    if (elapsedTime < 90) return 'Refining content...';
    if (elapsedTime < 120) return 'Designing slides...';
    if (elapsedTime < 150) return 'Creating presentation file...';
    return 'Finalizing...';
  };

  const stages = [
    { label: 'Planning', icon: '📋' },
    { label: 'Content', icon: '✍️' },
    { label: 'Review', icon: '🔍' },
    { label: 'Design', icon: '🎨' },
    { label: 'Export', icon: '📦' },
  ];

  const currentStage = Math.min(Math.floor(progress / 20), 4);

  return (
    <div className="progress-container" role="status" aria-live="polite">
      <div className="progress-card">
        {/* Animated Icon */}
        <div className="progress-icon-wrapper">
          <div className="progress-icon">
            <svg width="64" height="64" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="32" cy="32" r="30" stroke="url(#gradient)" strokeWidth="4" strokeDasharray="188.4" strokeDashoffset={188.4 * (1 - progress / 100)} strokeLinecap="round" className="progress-circle"/>
              <text x="32" y="38" textAnchor="middle" fontSize="16" fontWeight="bold" fill="url(#gradient)">{Math.round(progress)}%</text>
              <defs>
                <linearGradient id="gradient" x1="0" y1="0" x2="64" y2="64">
                  <stop offset="0%" stopColor="#6366f1" />
                  <stop offset="100%" stopColor="#8b5cf6" />
                </linearGradient>
              </defs>
            </svg>
          </div>
        </div>

        {/* Title and Status */}
        <div className="progress-content">
          <h3 className="progress-title">Generating Your Presentation</h3>
          <p className="progress-status">{getCurrentStatus()}</p>

          {/* Stage Indicators */}
          <div className="stages-container">
            {stages.map((stage, index) => (
              <div
                key={stage.label}
                className={`stage ${index <= currentStage ? 'active' : ''} ${index < currentStage ? 'complete' : ''}`}
              >
                <div className="stage-icon">{stage.icon}</div>
                <div className="stage-label">{stage.label}</div>
              </div>
            ))}
          </div>

          {/* Progress Bar */}
          <div className="progress-bar-container">
            <div className="progress-bar">
              <div
                className="progress-bar-fill"
                style={{ width: `${progress}%` }}
              ></div>
            </div>
          </div>

          {/* Time Info */}
          <div className="progress-time">
            <div className="time-item">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="8" cy="8" r="7" stroke="currentColor" strokeWidth="1.5"/>
                <path d="M8 4V8L11 10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
              </svg>
              <span>Elapsed: {formatTime(elapsedTime)}</span>
            </div>
            {estimatedTimeRemaining !== undefined && estimatedTimeRemaining > 0 && (
              <div className="time-item">
                <span>Remaining: ~{formatTime(estimatedTimeRemaining)}</span>
              </div>
            )}
          </div>

          {/* Note */}
          <p className="progress-note">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="8" cy="8" r="7" stroke="currentColor" strokeWidth="1.5"/>
              <path d="M8 7V11" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
              <circle cx="8" cy="5" r="0.5" fill="currentColor"/>
            </svg>
            This may take 2-3 minutes. Please don't close this window.
          </p>
        </div>
      </div>

      <style jsx>{`
        .progress-container {
          display: flex;
          justify-content: center;
          align-items: center;
          padding: 2rem 0;
        }

        .progress-card {
          background: rgba(255, 255, 255, 0.95);
          backdrop-filter: blur(10px);
          border-radius: var(--radius-xl);
          box-shadow: var(--shadow-xl);
          padding: 2.5rem;
          max-width: 600px;
          width: 100%;
        }

        .progress-icon-wrapper {
          display: flex;
          justify-content: center;
          margin-bottom: 2rem;
        }

        .progress-icon {
          position: relative;
        }

        .progress-circle {
          transform-origin: center;
          transform: rotate(-90deg);
          transition: stroke-dashoffset 0.5s ease;
        }

        .progress-content {
          text-align: center;
        }

        .progress-title {
          font-size: 1.5rem;
          font-weight: 700;
          color: var(--text-primary);
          margin: 0 0 0.5rem 0;
        }

        .progress-status {
          font-size: 1rem;
          color: var(--text-secondary);
          margin: 0 0 2rem 0;
          min-height: 1.5rem;
          font-weight: 500;
        }

        .stages-container {
          display: flex;
          justify-content: space-between;
          margin-bottom: 2rem;
          gap: 0.5rem;
        }

        .stage {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 0.5rem;
          flex: 1;
          opacity: 0.3;
          transition: all 0.3s ease;
        }

        .stage.active {
          opacity: 1;
        }

        .stage.complete .stage-icon {
          background: linear-gradient(135deg, var(--success-color) 0%, #059669 100%);
        }

        .stage-icon {
          width: 40px;
          height: 40px;
          border-radius: 50%;
          background: var(--bg-tertiary);
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 1.25rem;
          transition: all 0.3s ease;
        }

        .stage.active .stage-icon {
          background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
          animation: pulse 2s ease-in-out infinite;
        }

        .stage-label {
          font-size: 0.75rem;
          font-weight: 600;
          color: var(--text-secondary);
        }

        .progress-bar-container {
          margin: 1.5rem 0;
        }

        .progress-bar {
          width: 100%;
          height: 8px;
          background: var(--bg-tertiary);
          border-radius: 4px;
          overflow: hidden;
        }

        .progress-bar-fill {
          height: 100%;
          background: linear-gradient(90deg, #6366f1, #8b5cf6);
          transition: width 0.5s ease;
          border-radius: 4px;
          position: relative;
          overflow: hidden;
        }

        .progress-bar-fill::after {
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
          animation: shimmer 2s infinite;
        }

        @keyframes shimmer {
          0% {
            transform: translateX(-100%);
          }
          100% {
            transform: translateX(100%);
          }
        }

        .progress-time {
          display: flex;
          justify-content: center;
          gap: 2rem;
          margin-bottom: 1rem;
        }

        .time-item {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          font-size: 0.875rem;
          color: var(--text-secondary);
          font-weight: 500;
        }

        .progress-note {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 0.5rem;
          font-size: 0.875rem;
          color: var(--text-light);
          margin: 1rem 0 0 0;
          font-style: italic;
        }

        @media (max-width: 768px) {
          .progress-card {
            padding: 1.5rem;
          }

          .progress-title {
            font-size: 1.25rem;
          }

          .stages-container {
            gap: 0.25rem;
          }

          .stage-icon {
            width: 32px;
            height: 32px;
            font-size: 1rem;
          }

          .stage-label {
            font-size: 0.625rem;
          }

          .progress-time {
            flex-direction: column;
            gap: 0.5rem;
          }
        }
      `}</style>
    </div>
  );
}
