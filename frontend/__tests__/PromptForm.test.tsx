import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import PromptForm, { PresentationPrompt } from '@/components/PromptForm';

describe('PromptForm Component', () => {
  const mockOnSubmit = jest.fn();

  beforeEach(() => {
    mockOnSubmit.mockClear();
  });

  it('renders all form fields', () => {
    render(<PromptForm onSubmit={mockOnSubmit} isLoading={false} />);

    expect(screen.getByLabelText(/topic/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/tone/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/slide count/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /generate presentation/i })).toBeInTheDocument();
  });

  it('validates required topic field', async () => {
    render(<PromptForm onSubmit={mockOnSubmit} isLoading={false} />);

    const submitButton = screen.getByRole('button', { name: /generate presentation/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/topic is required/i)).toBeInTheDocument();
    });

    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  it('validates topic length (max 500 characters)', async () => {
    render(<PromptForm onSubmit={mockOnSubmit} isLoading={false} />);

    const topicInput = screen.getByLabelText(/topic/i);
    const longTopic = 'a'.repeat(501);

    fireEvent.change(topicInput, { target: { value: longTopic } });

    const submitButton = screen.getByRole('button', { name: /generate presentation/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/topic must be 500 characters or less/i)).toBeInTheDocument();
    });

    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  it('validates slide count range (5-20)', async () => {
    render(<PromptForm onSubmit={mockOnSubmit} isLoading={false} />);

    const topicInput = screen.getByLabelText(/topic/i);
    const slideCountInput = screen.getByLabelText(/slide count/i);

    fireEvent.change(topicInput, { target: { value: 'Test Topic' } });
    fireEvent.change(slideCountInput, { target: { value: '25' } });

    const submitButton = screen.getByRole('button', { name: /generate presentation/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/slide count must be between 5 and 20/i)).toBeInTheDocument();
    });

    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  it('submits form with valid topic only', async () => {
    mockOnSubmit.mockResolvedValue(undefined);

    render(<PromptForm onSubmit={mockOnSubmit} isLoading={false} />);

    const topicInput = screen.getByLabelText(/topic/i);
    fireEvent.change(topicInput, { target: { value: 'AI in Healthcare' } });

    const submitButton = screen.getByRole('button', { name: /generate presentation/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith({
        topic: 'AI in Healthcare',
      });
    });
  });

  it('submits form with all optional fields', async () => {
    mockOnSubmit.mockResolvedValue(undefined);

    render(<PromptForm onSubmit={mockOnSubmit} isLoading={false} />);

    const topicInput = screen.getByLabelText(/topic/i);
    const toneSelect = screen.getByLabelText(/tone/i);
    const slideCountInput = screen.getByLabelText(/slide count/i);

    fireEvent.change(topicInput, { target: { value: 'Machine Learning' } });
    fireEvent.change(toneSelect, { target: { value: 'professional' } });
    fireEvent.change(slideCountInput, { target: { value: '10' } });

    const submitButton = screen.getByRole('button', { name: /generate presentation/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith({
        topic: 'Machine Learning',
        tone: 'professional',
        slideCount: 10,
      });
    });
  });

  it('disables form fields when loading', () => {
    render(<PromptForm onSubmit={mockOnSubmit} isLoading={true} />);

    const topicInput = screen.getByLabelText(/topic/i);
    const toneSelect = screen.getByLabelText(/tone/i);
    const slideCountInput = screen.getByLabelText(/slide count/i);
    const submitButton = screen.getByRole('button', { name: /generating/i });

    expect(topicInput).toBeDisabled();
    expect(toneSelect).toBeDisabled();
    expect(slideCountInput).toBeDisabled();
    expect(submitButton).toBeDisabled();
  });

  it('clears form after successful submission', async () => {
    mockOnSubmit.mockResolvedValue(undefined);

    render(<PromptForm onSubmit={mockOnSubmit} isLoading={false} />);

    const topicInput = screen.getByLabelText(/topic/i) as HTMLInputElement;
    const toneSelect = screen.getByLabelText(/tone/i) as HTMLSelectElement;
    const slideCountInput = screen.getByLabelText(/slide count/i) as HTMLInputElement;

    fireEvent.change(topicInput, { target: { value: 'Test Topic' } });
    fireEvent.change(toneSelect, { target: { value: 'formal' } });
    fireEvent.change(slideCountInput, { target: { value: '8' } });

    const submitButton = screen.getByRole('button', { name: /generate presentation/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(topicInput.value).toBe('');
      expect(toneSelect.value).toBe('');
      expect(slideCountInput.value).toBe('');
    });
  });

  it('displays error message on submission failure', async () => {
    mockOnSubmit.mockRejectedValue(new Error('Network error'));

    render(<PromptForm onSubmit={mockOnSubmit} isLoading={false} />);

    const topicInput = screen.getByLabelText(/topic/i);
    fireEvent.change(topicInput, { target: { value: 'Test Topic' } });

    const submitButton = screen.getByRole('button', { name: /generate presentation/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/network error/i)).toBeInTheDocument();
    });
  });

  it('validates tone enum values', async () => {
    render(<PromptForm onSubmit={mockOnSubmit} isLoading={false} />);

    const toneSelect = screen.getByLabelText(/tone/i);

    // Check that all valid tone options are present
    expect(screen.getByRole('option', { name: /formal/i })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: /casual/i })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: /fun/i })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: /professional/i })).toBeInTheDocument();
  });

  it('trims whitespace from topic', async () => {
    mockOnSubmit.mockResolvedValue(undefined);

    render(<PromptForm onSubmit={mockOnSubmit} isLoading={false} />);

    const topicInput = screen.getByLabelText(/topic/i);
    fireEvent.change(topicInput, { target: { value: '  Test Topic  ' } });

    const submitButton = screen.getByRole('button', { name: /generate presentation/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith({
        topic: 'Test Topic',
      });
    });
  });
});
