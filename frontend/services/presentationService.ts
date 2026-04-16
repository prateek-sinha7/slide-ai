import axios, { AxiosError } from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface PresentationPrompt {
  topic: string;
  tone?: 'formal' | 'casual' | 'fun' | 'professional';
  slideCount?: number;
}

export interface PresentationResponse {
  presentationId: string;
  filename: string;
  downloadUrl: string;
  generatedAt: string;
}

export interface ErrorResponse {
  error: string;
  message?: string;
  code?: string;
  field?: string;
  retryable?: boolean;
}

/**
 * Generate a presentation from a prompt
 * @param prompt - The presentation prompt with topic and optional parameters
 * @param token - JWT authentication token
 * @returns Presentation metadata with download URL
 * @throws Error with user-friendly message on failure
 */
export async function generatePresentation(
  prompt: PresentationPrompt,
  token: string
): Promise<PresentationResponse> {
  try {
    const response = await axios.post<PresentationResponse>(
      `${API_URL}/api/presentations/generate`,
      prompt,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        timeout: 210000, // 210 seconds (slightly more than backend timeout)
      }
    );

    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const axiosError = error as AxiosError<ErrorResponse>;

      // Handle different error types
      if (axiosError.response) {
        // Server responded with error status
        const errorData = axiosError.response.data;
        const statusCode = axiosError.response.status;

        // Map technical errors to user-friendly messages
        switch (statusCode) {
          case 400:
            throw new Error(
              errorData.message || 'Invalid input. Please check your prompt and try again.'
            );
          case 401:
            throw new Error('Authentication failed. Please log in again.');
          case 408:
            throw new Error(
              'Generation is taking longer than expected. Try reducing the number of slides.'
            );
          case 500:
            if (errorData.code === 'GENERATION_LLM_FAILURE') {
              throw new Error(
                "We're having trouble generating your presentation. Please try again in a moment."
              );
            }
            throw new Error(
              errorData.message || 'An error occurred while generating your presentation.'
            );
          case 503:
            throw new Error('Service is temporarily unavailable. Please try again later.');
          default:
            throw new Error(
              errorData.message || 'An unexpected error occurred. Please try again.'
            );
        }
      } else if (axiosError.request) {
        // Request was made but no response received
        throw new Error('Network error. Please check your connection and try again.');
      } else {
        // Error setting up the request
        throw new Error('Failed to send request. Please try again.');
      }
    }

    // Non-Axios error
    throw new Error('An unexpected error occurred. Please try again.');
  }
}

/**
 * Download a generated presentation
 * @param presentationId - The ID of the presentation to download
 * @param token - JWT authentication token
 * @returns Blob containing the .pptx file
 * @throws Error with user-friendly message on failure
 */
export async function downloadPresentation(
  presentationId: string,
  token: string
): Promise<Blob> {
  try {
    const response = await axios.get(
      `${API_URL}/api/presentations/download/${presentationId}`,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        responseType: 'blob',
        timeout: 30000, // 30 seconds for download
      }
    );

    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const axiosError = error as AxiosError<ErrorResponse>;

      if (axiosError.response) {
        const statusCode = axiosError.response.status;

        switch (statusCode) {
          case 401:
            throw new Error('Authentication failed. Please log in again.');
          case 404:
            throw new Error('Presentation not found or has expired.');
          default:
            throw new Error('Failed to download presentation. Please try again.');
        }
      } else if (axiosError.request) {
        throw new Error('Network error. Please check your connection and try again.');
      }
    }

    throw new Error('Failed to download presentation. Please try again.');
  }
}

/**
 * Trigger browser download of a presentation file
 * @param blob - The file blob to download
 * @param filename - The filename to use for the download
 */
export function triggerDownload(blob: Blob, filename: string): void {
  // Create a temporary URL for the blob
  const url = window.URL.createObjectURL(blob);

  // Create a temporary anchor element
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;

  // Append to body, click, and remove
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);

  // Clean up the URL object
  window.URL.revokeObjectURL(url);
}
