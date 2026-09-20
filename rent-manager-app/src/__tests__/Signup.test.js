import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Signup from '../page/signup/Signup';

jest.mock('../services/fetch/ApiUtils', () => ({
    signup: jest.fn(),
}));

const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useNavigate: () => mockNavigate,
}));

describe('Signup Component', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    test('renders signup form', () => {
        const { container } = render(
            <MemoryRouter>
                <Signup />
            </MemoryRouter>
        );
        expect(container.querySelector('form')).toBeInTheDocument();
        expect(container.querySelector('input[type="submit"]')).toBeInTheDocument();
    });

    test('renders all input fields', () => {
        const { container } = render(
            <MemoryRouter>
                <Signup />
            </MemoryRouter>
        );
        expect(container.querySelector('input[name="email"]')).toBeInTheDocument();
        expect(container.querySelector('input[name="phone"]')).toBeInTheDocument();
        expect(container.querySelector('input[name="name"]')).toBeInTheDocument();
        expect(container.querySelector('input[name="password"]')).toBeInTheDocument();
        expect(container.querySelector('input[name="confirmPassword"]')).toBeInTheDocument();
    });

    test('renders heading with "Đăng kí"', () => {
        const { container } = render(
            <MemoryRouter>
                <Signup />
            </MemoryRouter>
        );
        const heading = container.querySelector('h3');
        expect(heading).toBeInTheDocument();
        expect(heading.textContent).toMatch(/Đăng ký/);
    });

    test('renders login link', () => {
        render(
            <MemoryRouter>
                <Signup />
            </MemoryRouter>
        );
        expect(screen.getByText(/Đăng nhập/)).toBeInTheDocument();
    });

    test('renders submit button with correct text', () => {
        render(
            <MemoryRouter>
                <Signup />
            </MemoryRouter>
        );
        expect(screen.getByDisplayValue(/Đăng ký/)).toBeInTheDocument();
    });

    test('renders email input with correct type', () => {
        const { container } = render(
            <MemoryRouter>
                <Signup />
            </MemoryRouter>
        );
        expect(container.querySelector('input[name="email"]')).toHaveAttribute('type', 'email');
    });

    test('renders password inputs with correct type', () => {
        const { container } = render(
            <MemoryRouter>
                <Signup />
            </MemoryRouter>
        );
        expect(container.querySelector('input[name="password"]')).toHaveAttribute('type', 'password');
        expect(container.querySelector('input[name="confirmPassword"]')).toHaveAttribute('type', 'password');
    });

    test('renders span labels for form fields', () => {
        const { container } = render(
            <MemoryRouter>
                <Signup />
            </MemoryRouter>
        );
        const spans = container.querySelectorAll('span');
        const spanTexts = Array.from(spans).map(s => s.textContent);
        expect(spanTexts).toContain('Email');
        expect(spanTexts).toContain('Mật khẩu');
        expect(spanTexts).toContain('Họ và tên');
        expect(spanTexts).toContain('Số điện thoại');
    });
});
