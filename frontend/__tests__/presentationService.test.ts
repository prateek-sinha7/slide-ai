import axios from 'axios';
import {
  generatePresentation,
  downloadPresentation,
  triggerDownload,
  PresentationPrompt,
  PresentationResponse,
} from '@/services/presentationService';

jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

describe('presentationService', () => {
  const mockToken = 'test-jwt-token';
  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('generatePresentation', () => {
    const mockPrompt: PresentationPrompt = {
      topic: 'AI in Healthcare',
      tone: 'professional',
      slideCount: 10,
    };

    const mockResponse: PresentationResponse = {
      presentationId: '123',
      filename: 'AI_in_Healthcare_20240101_120000.pptx',
      downloadUrl: '/api/presentations/download/123',
      generatedAt: '2024-01-01T12:00:00Z',
    };

    it('successfully generates a presentation', async () => {
      mockedAxios.post.mockResolvedValue({ data: mockResponse });

      const result = await generatePresentation(mockPrompt, mockToken);

      expect(mockedAxios.post).toHaveBeenCalledWith(
        `${API_URL}/api/presentations/generate`,
        mockPrompt,
        {
          headers: {
            Authorization: `Bearer ${mockToken}`,
            'Content-Type': 'application/json',
          },
          timeout: 210000,
        }
      );

      expect(result).toEqual(mockResponse);
    });

    it('includes JWT token in Authorization header', async () => {
      mockedAxios.post.mockResolvedValue({ data: mockResponse });

      await generatePresentation(mockPrompt, mockToken);

      const callArgs = mockedAxios.post.mock.calls[0];
      expect(callArgs[2]?.headers?.Authorization).toBe(`Bearer ${mockToken}`);
    });

    it('handles 400 validation error', async () => {
      mockedAxios.post.mockRejectedValue({
        isAxiosError: true,
        response: {
          status: 400,
          data: {
            error: 'Validation failed',
            message: 'Topic is required',
          },
        },
      });

      await expect(generatePresentation(mockPrompt, mockToken)).rejects.toThrow(
        'Topic is required'
      );
    });

    it('handles 401 authentication error', async () => {
      mockedAxios.post.mockRejectedValue({
        isAxiosError: true,
        response: {
          status: 401,
          data: {
            error: 'Authentication failed',
          },
        },
      });

      await expect(generatePresentation(mockPrompt, mockToken)).rejects.toThrow(
        'Authentication failed. Please log in again.'
      );
    });

    it('handles 408 timeout error', async () => {
      mockedAxios.post.mockRejectedValue({
        isAxiosError: true,
        response: {
          status: 408,
          data: {
            error: 'Generation timeout',
          },
        },
      });

      await expect(generatePresentation(mockPrompt, mockToken)).rejects.toThrow(
        'Generation is taking longer than expected'
      );
    });

    it('handles 500 LLM failure error', async () => {
      mockedAxios.post.mockRejectedValue({
        isAxiosError: true,
        response: {
          status: 500,
          data: {
            error: 'Generation failed',
            code: 'GENERATION_LLM_FAILURE',
          },
        },
      });

      await expect(generatePresentation(mockPrompt, mockToken)).rejects.toThrow(
        "We're having trouble generating your presentation"
      );
    });

    it('handles 503 service unavailable error', async () => {
      mockedAxios.post.mockRejectedValue({
        isAxiosError: true,
        response: {
          status: 503,
          data: {
            error: 'Service unavailable',
          },
        },
      });

      await expect(generatePresentation(mockPrompt, mockToken)).rejects.toThrow(
        'Service is temporarily unavailable'
      );
    });

    it('handles network error (no response)', async () => {
      mockedAxios.post.mockRejectedValue({
        isAxiosError: true,
        request: {},
      });

      await expect(generatePresentation(mockPrompt, mockToken)).rejects.toThrow(
        'Network error. Please check your connection'
      );
    });

    it('handles non-Axios error', async () => {
      mockedAxios.post.mockRejectedValue(new Error('Unknown error'));

      await expect(generatePresentation(mockPrompt, mockToken)).rejects.toThrow(
        'An unexpected error occurred'
      );
    });
  });

  describe('downloadPresentation', () => {
    const mockPresentationId = '123';
    const mockBlob = new Blob(['test'], { type: 'application/vnd.openxmlformats-officedocument.presentationml.presentation' });

    it('successfully downloads a presentation', async () => {
      mockedAxios.get.mockResolvedValue({ data: mockBlob });

      const result = await downloadPresentation(mockPresentationId, mockToken);

      expect(mockedAxios.get).toHaveBeenCalledWith(
        `${API_URL}/api/presentations/download/${mockPresentationId}`,
        {
          headers: {
            Authorization: `Bearer ${mockToken}`,
          },
          responseType: 'blob',
          timeout: 30000,
        }
      );

      expect(result).toEqual(mockBlob);
    });

    it('includes JWT token in Authorization header', async () => {
      mockedAxios.get.mockResolvedValue({ data: mockBlob });

      await downloadPresentation(mockPresentationId, mockToken);

      const callArgs = mockedAxios.get.mock.calls[0];
      expect(callArgs[1]?.headers?.Authorization).toBe(`Bearer ${mockToken}`);
    });

    it('handles 401 authentication error', async () => {
      mockedAxios.get.mockRejectedValue({
        isAxiosError: true,
        response: {
          status: 401,
          data: {},
        },
      });

      await expect(downloadPresentation(mockPresentationId, mockToken)).rejects.toThrow(
        'Authentication failed. Please log in again.'
      );
    });

    it('handles 404 not found error', async () => {
      mockedAxios.get.mockRejectedValue({
        isAxiosError: true,
        response: {
          status: 404,
          data: {},
        },
      });

      await expect(downloadPresentation(mockPresentationId, mockToken)).rejects.toThrow(
        'Presentation not found or has expired'
      );
    });

    it('handles network error', async () => {
      mockedAxios.get.mockRejectedValue({
        isAxiosError: true,
        request: {},
      });

      await expect(downloadPresentation(mockPresentationId, mockToken)).rejects.toThrow(
        'Network error. Please check your connection'
      );
    });
  });

  describe('triggerDownload', () => {
    let createElementSpy: jest.SpyInstance;
    let createObjectURLSpy: jest.SpyInstance;
    let revokeObjectURLSpy: jest.SpyInstance;
    let mockLink: HTMLAnchorElement;

    beforeEach(() => {
      mockLink = {
        href: '',
        download: '',
        click: jest.fn(),
      } as unknown as HTMLAnchorElement;

      createElementSpy = jest.spyOn(document, 'createElement').mockReturnValue(mockLink);
      jest.spyOn(document.body, 'appendChild').mockImplementation(() => mockLink);
      jest.spyOn(document.body, 'removeChild').mockImplementation(() => mockLink);

      createObjectURLSpy = jest.spyOn(window.URL, 'createObjectURL').mockReturnValue('blob:mock-url');
      revokeObjectURLSpy = jest.spyOn(window.URL, 'revokeObjectURL').mockImplementation(() => {});
    });

    afterEach(() => {
      jest.restoreAllMocks();
    });

    it('triggers browser download with correct filename', () => {
      const mockBlob = new Blob(['test'], { type: 'application/vnd.openxmlformats-officedocument.presentationml.presentation' });
      const filename = 'test-presentation.pptx';

      triggerDownload(mockBlob, filename);

      expect(createObjectURLSpy).toHaveBeenCalledWith(mockBlob);
      expect(createElementSpy).toHaveBeenCalledWith('a');
      expect(mockLink.href).toBe('blob:mock-url');
      expect(mockLink.download).toBe(filename);
      expect(mockLink.click).toHaveBeenCalled();
      expect(revokeObjectURLSpy).toHaveBeenCalledWith('blob:mock-url');
    });

    it('cleans up temporary elements and URLs', () => {
      const mockBlob = new Blob(['test']);
      const filename = 'test.pptx';

      triggerDownload(mockBlob, filename);

      expect(document.body.appendChild).toHaveBeenCalledWith(mockLink);
      expect(document.body.removeChild).toHaveBeenCalledWith(mockLink);
      expect(revokeObjectURLSpy).toHaveBeenCalled();
    });
  });
});
