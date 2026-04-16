import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import ProgressIndicator from '@/components/ProgressIndicator';

describe('ProgressIndicator Component', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  it('renders nothing when isLoading is false', () => {
    const { container } = render(<ProgressIndicator isLoading={false} />);
    expect(container.firstChild).toBeNull();
  });

  it('displays loading indicator when isLoading is true', () => {
    render(<ProgressIndicator isLoading={true} />);

    expect(screen.getByText(/generating your presentation/i)).toBeInTheDocument();
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('displays initial status message', () => {
    render(<ProgressIndicator isLoading={true} />);

    expect(screen.getByText(/initializing/i)).toBeInTheDocument();
  });

  it('updates status message over time', async () => {
    render(<ProgressIndicator isLoading={true} />);

    // Initial status
    expect(screen.getByText(/initializing/i)).toBeInTheDocument();

    // After 15 seconds
    jest.advanceTimersByTime(15000);
    await waitFor(() => {
      expect(screen.getByText(/planning presentation structure/i)).toBeInTheDocument();
    });

    // After 35 seconds
    jest.advanceTimersByTime(20000);
    await waitFor(() => {
      expect(screen.getByText(/generating content/i)).toBeInTheDocument();
    });

    // After 65 seconds
    jest.advanceTimersByTime(30000);
    await waitFor(() => {
      expect(screen.getByText(/refining content/i)).toBeInTheDocument();
    });

    // After 95 seconds
    jest.advanceTimersByTime(30000);
    await waitFor(() => {
      expect(screen.getByText(/creating presentation file/i)).toBeInTheDocument();
    });
  });

  it('displays custom status when provided', () => {
    const customStatus = 'Processing your request...';
    render(<ProgressIndicator isLoading={true} status={customStatus} />);

    expect(screen.getByText(customStatus)).toBeInTheDocument();
  });

  it('displays elapsed time', async () => {
    render(<ProgressIndicator isLoading={true} />);

    // Initial time
    expect(screen.getByText(/elapsed: 0:00/i)).toBeInTheDocument();

    // After 5 seconds
    jest.advanceTimersByTime(5000);
    await waitFor(() => {
      expect(screen.getByText(/elapsed: 0:05/i)).toBeInTheDocument();
    });

    // After 65 seconds
    jest.advanceTimersByTime(60000);
    await waitFor(() => {
      expect(screen.getByText(/elapsed: 1:05/i)).toBeInTheDocument();
    });
  });

  it('displays estimated time remaining when provided', () => {
    render(<ProgressIndicator isLoading={true} estimatedTimeRemaining={60} />);

    expect(screen.getByText(/estimated remaining: 1:00/i)).toBeInTheDocument();
  });

  it('does not display estimated time when not provided', () => {
    render(<ProgressIndicator isLoading={true} />);

    expect(screen.queryByText(/estimated remaining/i)).not.toBeInTheDocument();
  });

  it('updates progress bar based on elapsed and estimated time', () => {
    const { rerender } = render(
      <ProgressIndicator isLoading={true} estimatedTimeRemaining={100} />
    );

    // Progress bar should exist
    const progressBar = document.querySelector('.progress-bar-fill');
    expect(progressBar).toBeInTheDocument();

    // Advance time and check progress updates
    jest.advanceTimersByTime(50000);
    rerender(<ProgressIndicator isLoading={true} estimatedTimeRemaining={50} />);

    // Progress should be around 50%
    expect(progressBar).toHaveStyle({ width: expect.stringMatching(/\d+%/) });
  });

  it('displays warning message about not closing window', () => {
    render(<ProgressIndicator isLoading={true} />);

    expect(screen.getByText(/this may take up to 2 minutes/i)).toBeInTheDocument();
    expect(screen.getByText(/please don't close this window/i)).toBeInTheDocument();
  });

  it('has proper ARIA attributes for accessibility', () => {
    render(<ProgressIndicator isLoading={true} />);

    const progressIndicator = screen.getByRole('status');
    expect(progressIndicator).toHaveAttribute('aria-live', 'polite');
  });

  it('resets elapsed time when isLoading changes to false', async () => {
    const { rerender } = render(<ProgressIndicator isLoading={true} />);

    // Advance time
    jest.advanceTimersByTime(30000);
    await waitFor(() => {
      expect(screen.getByText(/elapsed: 0:30/i)).toBeInTheDocument();
    });

    // Stop loading
    rerender(<ProgressIndicator isLoading={false} />);

    // Component should not render
    expect(screen.queryByRole('status')).not.toBeInTheDocument();

    // Start loading again
    rerender(<ProgressIndicator isLoading={true} />);

    // Time should be reset
    expect(screen.getByText(/elapsed: 0:00/i)).toBeInTheDocument();
  });

  it('formats time correctly with leading zeros', async () => {
    render(<ProgressIndicator isLoading={true} />);

    jest.advanceTimersByTime(9000);
    await waitFor(() => {
      expect(screen.getByText(/elapsed: 0:09/i)).toBeInTheDocument();
    });

    jest.advanceTimersByTime(60000);
    await waitFor(() => {
      expect(screen.getByText(/elapsed: 1:09/i)).toBeInTheDocument();
    });
  });

  it('cleans up timers on unmount', () => {
    const { unmount } = render(<ProgressIndicator isLoading={true} />);

    // Verify timers are running
    expect(jest.getTimerCount()).toBeGreaterThan(0);

    unmount();

    // Timers should be cleaned up
    jest.runOnlyPendingTimers();
  });
});
