import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Header from '../common/Header';

describe('Header Component', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    test('renders app name', () => {
        render(
            <MemoryRouter>
                <Header authenticated={false} currentUser={null} role="" />
            </MemoryRouter>
        );
        expect(screen.getAllByText(/PhongTro/).length).toBeGreaterThan(0);
    });

    test('renders login button when not authenticated', () => {
        render(
            <MemoryRouter>
                <Header authenticated={false} currentUser={null} role="" />
            </MemoryRouter>
        );
        expect(screen.getByText(/Đăng nhập/)).toBeInTheDocument();
    });

    test('renders signup button when not authenticated', () => {
        render(
            <MemoryRouter>
                <Header authenticated={false} currentUser={null} role="" />
            </MemoryRouter>
        );
        expect(screen.getByText(/Đăng kí/)).toBeInTheDocument();
    });

    test('renders user name when authenticated', () => {
        const currentUser = {
            name: 'Test User',
            email: 'test@gmail.com',
            roles: [{ name: 'ROLE_USER' }]
        };
        render(
            <MemoryRouter>
                <Header authenticated={true} currentUser={currentUser} role="ROLE_USER" />
            </MemoryRouter>
        );
        expect(screen.getByText('Test User')).toBeInTheDocument();
    });

    test('renders logout button when authenticated', () => {
        const currentUser = {
            name: 'Test User',
            email: 'test@gmail.com',
            roles: [{ name: 'ROLE_USER' }]
        };
        render(
            <MemoryRouter>
                <Header authenticated={true} currentUser={currentUser} role="ROLE_USER" />
            </MemoryRouter>
        );
        expect(screen.getByText(/Đăng xuất/)).toBeInTheDocument();
    });

    test('does not render login button when authenticated', () => {
        const currentUser = {
            name: 'Test User',
            email: 'test@gmail.com',
            roles: [{ name: 'ROLE_USER' }]
        };
        render(
            <MemoryRouter>
                <Header authenticated={true} currentUser={currentUser} role="ROLE_USER" />
            </MemoryRouter>
        );
        const loginLinks = screen.queryAllByText(/Đăng nhập/);
        expect(loginLinks.length).toBe(0);
    });

    test('renders profile link when authenticated', () => {
        const currentUser = {
            name: 'Test User',
            email: 'test@gmail.com',
            roles: [{ name: 'ROLE_USER' }]
        };
        render(
            <MemoryRouter>
                <Header authenticated={true} currentUser={currentUser} role="ROLE_USER" />
            </MemoryRouter>
        );
        expect(screen.getByText(/Hồ Sơ/)).toBeInTheDocument();
    });

    test('renders navigation links', () => {
        render(
            <MemoryRouter>
                <Header authenticated={false} currentUser={null} role="" />
            </MemoryRouter>
        );
        expect(screen.getByText(/Trang chủ/)).toBeInTheDocument();
        expect(screen.getByText(/Nhà cho thuê/)).toBeInTheDocument();
        expect(screen.getByText(/Liên hệ/)).toBeInTheDocument();
        expect(screen.getByText(/Người cho thuê/)).toBeInTheDocument();
    });

    test('renders "Đăng tin" button when not authenticated', () => {
        render(
            <MemoryRouter>
                <Header authenticated={false} currentUser={null} role="" />
            </MemoryRouter>
        );
        expect(screen.getByText(/Đăng tin/)).toBeInTheDocument();
    });

    test('renders user avatar initial when no imageUrl', () => {
        const currentUser = {
            name: 'Test User',
            email: 'test@gmail.com',
            roles: [{ name: 'ROLE_USER' }]
        };
        render(
            <MemoryRouter>
                <Header authenticated={true} currentUser={currentUser} role="ROLE_USER" />
            </MemoryRouter>
        );
        expect(screen.getByText('T')).toBeInTheDocument();
    });
});
