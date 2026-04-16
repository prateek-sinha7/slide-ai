'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import PromptForm, { PresentationPrompt } from '@/components/PromptForm';
import ProgressIndicator from '@/components/ProgressIndicator';
import ErrorDisplay from '@/components/ErrorDisplay';
import {
  generatePresentation,
  downloadPresentation,
  triggerDownload,
} from '@/services/presentationService';

export default function Home() {
  const { isAuthenticated, token, user, logout } = useAuth();
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [generationStatus, setGenerationStatus] = useState<string>('');

  // Redirect unauthenticated users to login
  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/auth');
    }
  }, [isAuthenticated, router]);

  // Handle presentation generation
  const handleGeneratePresentation = async (prompt: PresentationPrompt) => {
    if (!token) {
      setError('Authentication required. Please log in again.');
      return;
    }

    setIsLoading(true);
    setError(null);
    setGenerationStatus('Initializing generation...');

    try {
      // Generate presentation
      const response = await generatePresentation(prompt, token);

      setGenerationStatus('Downloading presentation...');

      // Download the presentation file
      const blob = await downloadPresentation(response.presentationId, token);

      // Trigger browser download
      triggerDownload(blob, response.filename);

      setGenerationStatus('');
      setIsLoading(false);
    } catch (err) {
      setIsLoading(false);
      setGenerationStatus('');

      if (err instanceof Error) {
        // Check if it's an authentication error
        if (err.message.includes('Authentication') || err.message.includes('log in')) {
          setError(err.message);
          // Redirect to login after a delay
          setTimeout(() => {
            logout();
            router.push('/auth');
          }, 2000);
        } else {
          setError(err.message);
        }
      } else {
        setError('An unexpected error occurred. Please try again.');
      }
    }
  };

  const handleRetry = () => {
    setError(null);
  };

  const handleDismissError = () => {
    setError(null);
  };

  // Show loading state while checking authentication
  if (!isAuthenticated) {
    return null; // Will redirect in useEffect
  }

  return (
    <div className="min-h-screen bg-gradient">
      {/* Header */}
      <header className="header">
        <div className="container">
          <div className="header-content">
            <div className="header-left">
              <div className="logo">
                <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <rect width="32" height="32" rx="8" fill="url(#gradient)" />
                  <path d="M8 12h16M8 16h16M8 20h10" stroke="white" strokeWidth="2" strokeLinecap="round" />
                  <defs>
                    <linearGradient id="gradient" x1="0" y1="0" x2="32" y2="32">
                      <stop offset="0%" stopColor="#6366f1" />
                      <stop offset="100%" stopColor="#8b5cf6" />
                    </linearGradient>
                  </defs>
                </svg>
              </div>
              <div className="header-text">
                <h1 className="header-title">AI PowerPoint Generator</h1>
                {user && (
                  <p className="header-subtitle">Welcome back, {user.username}</p>
                )}
              </div>
            </div>
            <button onClick={logout} className="btn btn-danger btn-sm">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M6 14H3.33333C2.97971 14 2.64057 13.8595 2.39052 13.6095C2.14048 13.3594 2 13.0203 2 12.6667V3.33333C2 2.97971 2.14048 2.64057 2.39052 2.39052C2.64057 2.14048 2.97971 2 3.33333 2H6M10.6667 11.3333L14 8M14 8L10.6667 4.66667M14 8H6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="main-content">
        <div className="container">
          <div className="content-wrapper">
            {/* Hero Section */}
            {!isLoading && !error && (
              <div className="hero-section fade-in">
                <h2 className="hero-title">Create Stunning Presentations with AI</h2>
                <p className="hero-description">
                  Transform your ideas into professional PowerPoint presentations in minutes.
                  Just describe your topic, and let AI do the rest.
                </p>
              </div>
            )}

            {/* Error Display */}
            {error && (
              <div className="fade-in">
                <ErrorDisplay
                  error={error}
                  onRetry={handleRetry}
                  onDismiss={handleDismissError}
                />
              </div>
            )}

            {/* Progress Indicator */}
            {isLoading && (
              <div className="fade-in">
                <ProgressIndicator isLoading={isLoading} status={generationStatus} />
              </div>
            )}

            {/* Prompt Form */}
            {!isLoading && (
              <div className="fade-in">
                <PromptForm onSubmit={handleGeneratePresentation} isLoading={isLoading} />
              </div>
            )}

            {/* Features Section */}
            {!isLoading && (
              <div className="features-section fade-in">
                <div className="features-grid">
                  <div className="feature-card">
                    <div className="feature-icon">
                      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M13 2L3 14h8l-1 8 10-12h-8l1-8z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      </svg>
                    </div>
                    <h3 className="feature-title">Lightning Fast</h3>
                    <p className="feature-description">Generate complete presentations in 2-3 minutes</p>
                  </div>

                  <div className="feature-card">
                    <div className="feature-icon">
                      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      </svg>
                    </div>
                    <h3 className="feature-title">Professional Quality</h3>
                    <p className="feature-description">AI-powered content with polished designs</p>
                  </div>

                  <div className="feature-card">
                    <div className="feature-icon">
                      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        <path d="M12 6V12L16 14" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      </svg>
                    </div>
                    <h3 className="feature-title">Fully Customizable</h3>
                    <p className="feature-description">Choose tone, slide count, and more</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>

      <style jsx>{`
        .bg-gradient {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          min-height: 100vh;
        }

        .header {
          background: rgba(255, 255, 255, 0.95);
          backdrop-filter: blur(10px);
          border-bottom: 1px solid rgba(0, 0, 0, 0.1);
          padding: 1rem 0;
          position: sticky;
          top: 0;
          z-index: 100;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        }

        .header-content {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .header-left {
          display: flex;
          align-items: center;
          gap: 1rem;
        }

        .logo {
          flex-shrink: 0;
        }

        .header-text {
          display: flex;
          flex-direction: column;
        }

        .header-title {
          font-size: 1.25rem;
          font-weight: 700;
          color: var(--text-primary);
          margin: 0;
        }

        .header-subtitle {
          font-size: 0.875rem;
          color: var(--text-secondary);
          margin: 0;
        }

        .btn-sm {
          padding: 0.5rem 1rem;
          font-size: 0.8125rem;
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }

        .main-content {
          padding: 3rem 0;
        }

        .content-wrapper {
          max-width: 800px;
          margin: 0 auto;
        }

        .hero-section {
          text-align: center;
          margin-bottom: 3rem;
        }

        .hero-title {
          font-size: 2.5rem;
          font-weight: 800;
          color: white;
          margin: 0 0 1rem 0;
          line-height: 1.2;
          text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }

        .hero-description {
          font-size: 1.125rem;
          color: rgba(255, 255, 255, 0.9);
          margin: 0;
          line-height: 1.6;
        }

        .features-section {
          margin-top: 3rem;
        }

        .features-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 1.5rem;
        }

        .feature-card {
          background: rgba(255, 255, 255, 0.95);
          backdrop-filter: blur(10px);
          border-radius: var(--radius-lg);
          padding: 1.5rem;
          text-align: center;
          transition: transform 0.2s ease, box-shadow 0.2s ease;
        }

        .feature-card:hover {
          transform: translateY(-4px);
          box-shadow: var(--shadow-xl);
        }

        .feature-icon {
          width: 48px;
          height: 48px;
          margin: 0 auto 1rem;
          display: flex;
          align-items: center;
          justify-content: center;
          background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
          border-radius: var(--radius-md);
          color: white;
        }

        .feature-title {
          font-size: 1rem;
          font-weight: 600;
          color: var(--text-primary);
          margin: 0 0 0.5rem 0;
        }

        .feature-description {
          font-size: 0.875rem;
          color: var(--text-secondary);
          margin: 0;
          line-height: 1.5;
        }

        @media (max-width: 768px) {
          .header-title {
            font-size: 1rem;
          }

          .header-subtitle {
            font-size: 0.75rem;
          }

          .hero-title {
            font-size: 1.75rem;
          }

          .hero-description {
            font-size: 1rem;
          }

          .features-grid {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  );
}
