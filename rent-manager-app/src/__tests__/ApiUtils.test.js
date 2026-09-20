import { API_BASE_URL, ACCESS_TOKEN } from '../constants/Connect';

describe('API Utils', () => {
    beforeEach(() => {
        localStorage.clear();
        jest.restoreAllMocks();
    });

    describe('login function', () => {
        test('sends POST request to /auth/login', async () => {
            const mockHeaders = new Map();
            mockHeaders.set('content-type', 'application/json');
            const mockFetch = jest.spyOn(global, 'fetch').mockResolvedValue({
                ok: true,
                headers: mockHeaders,
                json: async () => ({ accessToken: 'mock-token' }),
            });

            const { login } = await import('../services/fetch/ApiUtils');
            const loginRequest = { email: 'test@gmail.com', password: 'password123' };
            const result = await login(loginRequest);

            expect(mockFetch).toHaveBeenCalledWith(
                `${API_BASE_URL}/auth/login`,
                expect.objectContaining({
                    method: 'POST',
                })
            );
            expect(result).toEqual({ accessToken: 'mock-token' });
        });

        test('throws error on failed login', async () => {
            const mockHeaders = new Map();
            mockHeaders.set('content-type', 'application/json');
            jest.spyOn(global, 'fetch').mockResolvedValue({
                ok: false,
                headers: mockHeaders,
                json: async () => ({ message: 'Invalid credentials' }),
            });

            const { login } = await import('../services/fetch/ApiUtils');
            const loginRequest = { email: 'wrong@gmail.com', password: 'wrong' };

            await expect(login(loginRequest)).rejects.toEqual({ message: 'Invalid credentials' });
        });
    });

    describe('getCurrentUser function', () => {
        test('sends GET request with Authorization header', async () => {
            localStorage.setItem(ACCESS_TOKEN, 'test-token');
            const mockHeaders = new Map();
            mockHeaders.set('content-type', 'application/json');
            const mockFetch = jest.spyOn(global, 'fetch').mockResolvedValue({
                ok: true,
                headers: mockHeaders,
                json: async () => ({ id: 1, name: 'Test User', email: 'test@gmail.com' }),
            });

            const { getCurrentUser } = await import('../services/fetch/ApiUtils');
            const result = await getCurrentUser();

            expect(mockFetch).toHaveBeenCalledWith(
                `${API_BASE_URL}/user/me`,
                expect.objectContaining({
                    method: 'GET',
                })
            );
            expect(result.name).toBe('Test User');
        });

        test('rejects when no token', async () => {
            const { getCurrentUser } = await import('../services/fetch/ApiUtils');
            await expect(getCurrentUser()).rejects.toBe('No access token set.');
        });
    });

    describe('API_BASE_URL', () => {
        test('is defined', () => {
            expect(API_BASE_URL).toBeDefined();
        });

        test('is a string', () => {
            expect(typeof API_BASE_URL).toBe('string');
        });
    });

    describe('ACCESS_TOKEN constant', () => {
        test('is defined', () => {
            expect(ACCESS_TOKEN).toBeDefined();
        });

        test('equals accessToken', () => {
            expect(ACCESS_TOKEN).toBe('accessToken');
        });
    });
});
