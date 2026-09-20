import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Login from '../page/login/Login';
import { login } from '../services/fetch/ApiUtils';

jest.mock('../services/fetch/ApiUtils');

const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useNavigate: () => mockNavigate,
    useLocation: () => ({ state: {}, pathname: '/login' }),
}));

describe('Login Component', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        localStorage.clear();
    });

    test('renders login form', () => {
        const { container } = render(
            <MemoryRouter>
                <Login authenticated={false} />
            </MemoryRouter>
        );
        expect(screen.getAllByText(/Đăng nhập/).length).toBeGreaterThan(0);
        expect(container.querySelector('input[name="email"]')).toBeInTheDocument();
        expect(container.querySelector('input[name="password"]')).toBeInTheDocument();
    });

    test('renders signup link', () => {
        render(
            <MemoryRouter>
                <Login authenticated={false} />
            </MemoryRouter>
        );
        expect(screen.getByText(/Đăng ký tài khoản mới/)).toBeInTheDocument();
    });

    test('renders forgot password link', () => {
        render(
            <MemoryRouter>
                <Login authenticated={false} />
            </MemoryRouter>
        );
        expect(screen.getByText(/Quên mật khẩu/)).toBeInTheDocument();
    });

    test('renders social login section', () => {
        render(
            <MemoryRouter>
                <Login authenticated={false} />
            </MemoryRouter>
        );
        expect(screen.getByText(/hoặc đăng nhập với/)).toBeInTheDocument();
    });

    test('redirects to home if already authenticated', () => {
        const { container } = render(
            <MemoryRouter>
                <Login authenticated={true} />
            </MemoryRouter>
        );
        expect(container.querySelector('.content')).not.toBeInTheDocument();
    });

    test('handles form input changes', () => {
        const { container } = render(
            <MemoryRouter>
                <Login authenticated={false} />
            </MemoryRouter>
        );
        const emailInput = container.querySelector('input[name="email"]');
        const passwordInput = container.querySelector('input[name="password"]');
        fireEvent.change(emailInput, { target: { name: 'email', value: 'test@gmail.com' } });
        fireEvent.change(passwordInput, { target: { name: 'password', value: 'password123' } });
        expect(emailInput.value).toBe('test@gmail.com');
        expect(passwordInput.value).toBe('password123');
    });

    test('calls login API on form submit', async () => {
        login.mockResolvedValue({ accessToken: 'mock-token-123' });
        const { container } = render(
            <MemoryRouter>
                <Login authenticated={false} onLoginSuccess={jest.fn()} />
            </MemoryRouter>
        );
        fireEvent.change(container.querySelector('input[name="email"]'), {
            target: { name: 'email', value: 'test@gmail.com' }
        });
        fireEvent.change(container.querySelector('input[name="password"]'), {
            target: { name: 'password', value: 'password123' }
        });
        fireEvent.click(container.querySelector('input[type="submit"]'));
        await waitFor(() => {
            expect(login).toHaveBeenCalledWith({ email: 'test@gmail.com', password: 'password123' });
        });
    });

    test('stores token in localStorage on successful login', async () => {
        login.mockResolvedValue({ accessToken: 'mock-token-123' });
        const { container } = render(
            <MemoryRouter>
                <Login authenticated={false} onLoginSuccess={jest.fn()} />
            </MemoryRouter>
        );
        fireEvent.change(container.querySelector('input[name="email"]'), {
            target: { name: 'email', value: 'test@gmail.com' }
        });
        fireEvent.change(container.querySelector('input[name="password"]'), {
            target: { name: 'password', value: 'password123' }
        });
        fireEvent.click(container.querySelector('input[type="submit"]'));
        await waitFor(() => {
            expect(localStorage.getItem('accessToken')).toBe('mock-token-123');
        });
    });

    test('calls onLoginSuccess callback', async () => {
        login.mockResolvedValue({ accessToken: 'mock-token-123' });
        const onLoginSuccess = jest.fn();
        const { container } = render(
            <MemoryRouter>
                <Login authenticated={false} onLoginSuccess={onLoginSuccess} />
            </MemoryRouter>
        );
        fireEvent.change(container.querySelector('input[name="email"]'), {
            target: { name: 'email', value: 'test@gmail.com' }
        });
        fireEvent.change(container.querySelector('input[name="password"]'), {
            target: { name: 'password', value: 'password123' }
        });
        fireEvent.click(container.querySelector('input[type="submit"]'));
        await waitFor(() => {
            expect(onLoginSuccess).toHaveBeenCalled();
        });
    });

    test('email input is type email', () => {
        const { container } = render(
            <MemoryRouter>
                <Login authenticated={false} />
            </MemoryRouter>
        );
        expect(container.querySelector('input[name="email"]')).toHaveAttribute('type', 'email');
    });

    test('password input is type password', () => {
        const { container } = render(
            <MemoryRouter>
                <Login authenticated={false} />
            </MemoryRouter>
        );
        expect(container.querySelector('input[name="password"]')).toHaveAttribute('type', 'password');
    });
});
