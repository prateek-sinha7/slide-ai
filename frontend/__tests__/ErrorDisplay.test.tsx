import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import ErrorDisplay from '@/components/ErrorDisplay';

describe('ErrorDisplay Component', () => {
  it('renders nothing when error is null', () => {
    const { container } = render(<ErrorDisplay error={null} />);
    expect(container.firstChild).toBeNull();
  });

  it('displays error message', () => {
    const errorMessage = 'Something went wrong';
    render(<ErrorDisplay error={errorMessage} />);

    expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();
    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });

  it('maps technical error codes to user-friendly messages', () => {
    render(<ErrorDisplay error="AUTH_INVALID_CREDENTIALS" />);

    expect(screen.getByText(/username or password is incorrect/i)).toBeInTheDocument();
  });

  it('shows retry button for retryable errors', () => {
    const mockRetry = jest.fn();
    render(<ErrorDisplay error="Network error. Please try again." onRetry={mockRetry} />);

    const retryButton = screen.getByRole('button', { name: /try again/i });
    expect(retryButton).toBeInTheDocument();

    fireEvent.click(retryButton);
    expect(mockRetry).toHaveBeenCalledTimes(1);
  });

  it('does not show retry button for non-retryable errors', () => {
    const mockRetry = jest.fn();
    render(<ErrorDisplay error="Invalid credentials" onRetry={mockRetry} />);

    expect(screen.queryByRole('button', { name: /try again/i })).not.toBeInTheDocument();
  });

  it('shows dismiss button when onDismiss is provided', () => {
    const mockDismiss = jest.fn();
    render(<ErrorDisplay error="Test error" onDismiss={mockDismiss} />);

    const dismissButton = screen.getByRole('button', { name: /dismiss/i });
    expect(dismissButton).toBeInTheDocument();

    fireEvent.click(dismissButton);
    expect(mockDismiss).toHaveBeenCalledTimes(1);
  });

  it('handles authentication error pattern', () => {
    render(<ErrorDisplay error="Authentication token expired" />);

    expect(screen.getByText(/authentication failed.*please log in again/i)).toBeInTheDocument();
  });

  it('handles timeout error pattern', () => {
    render(<ErrorDisplay error="Request timeout occurred" />);

    expect(screen.getByText(/generation is taking longer than expected/i)).toBeInTheDocument();
  });

  it('handles service unavailable error pattern', () => {
    render(<ErrorDisplay error="Service temporarily unavailable" />);

    expect(screen.getByText(/service is temporarily unavailable/i)).toBeInTheDocument();
  });

  it('has proper ARIA attributes for accessibility', () => {
    render(<ErrorDisplay error="Test error" />);

    const errorDisplay = screen.getByRole('alert');
    expect(errorDisplay).toHaveAttribute('aria-live', 'assertive');
  });

  it('identifies retryable errors correctly', () => {
    const retryableErrors = [
      'Network error occurred',
      'Service temporarily unavailable',
      'Please try again',
      'Request timeout',
      'Generation failed',
      'Unable to create file',
    ];

    retryableErrors.forEach((error) => {
      const mockRetry = jest.fn();
      const { unmount } = render(<ErrorDisplay error={error} onRetry={mockRetry} />);

      expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
      unmount();
    });
  });

  it('maps GENERATION_LLM_FAILURE to user-friendly message', () => {
    render(<ErrorDisplay error="GENERATION_LLM_FAILURE" />);

    expect(
      screen.getByText(/we're having trouble generating your presentation/i)
    ).toBeInTheDocument();
  });

  it('maps VALIDATION_TOPIC_LENGTH to user-friendly message', () => {
    render(<ErrorDisplay error="VALIDATION_TOPIC_LENGTH" />);

    expect(screen.getByText(/please enter a topic between 1 and 500 characters/i)).toBeInTheDocument();
  });

  it('displays original error if no mapping found', () => {
    const customError = 'This is a custom error message';
    render(<ErrorDisplay error={customError} />);

    expect(screen.getByText(customError)).toBeInTheDocument();
  });
});
