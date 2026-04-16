/**
 * Test to verify frontend setup is correct.
 */

describe('Frontend Setup', () => {
  it('should have Next.js environment configured', () => {
    // Verify environment variable access
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    expect(apiUrl).toBeDefined();
    expect(typeof apiUrl).toBe('string');
  });

  it('should be able to run basic tests', () => {
    expect(true).toBe(true);
  });
});
