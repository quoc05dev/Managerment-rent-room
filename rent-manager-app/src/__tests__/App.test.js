import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';

jest.mock('../services/fetch/ApiUtils', () => ({
    getCurrentUser: jest.fn(),
    getCurrentRentaler: jest.fn(),
    getCurrentAdmin: jest.fn(),
}));

jest.mock('../page/user/Main', () => () => <div>Main</div>);
jest.mock('../page/user/RentalHome', () => () => <div>RentalHome</div>);
jest.mock('../page/user/RentailHomeDetail', () => () => <div>RentailHomeDetail</div>);
jest.mock('../page/user/About', () => () => <div>About</div>);
jest.mock('../page/user/Contact', () => () => <div>Contact</div>);
jest.mock('../page/user/AgentsGird', () => () => <div>AgentsGird</div>);
jest.mock('../page/user/AgentSingle', () => () => <div>AgentSingle</div>);
jest.mock('../page/user/SendRequest', () => () => <div>SendRequest</div>);
jest.mock('../page/user/RequestManagement', () => () => <div>RequestManagement</div>);
jest.mock('../page/user/Follow', () => () => <div>Follow</div>);
jest.mock('../page/user/SaveBlog', () => () => <div>SaveBlog</div>);
jest.mock('../page/user/RoomHired', () => () => <div>RoomHired</div>);
jest.mock('../page/user/Profile', () => () => <div>Profile</div>);
jest.mock('../page/user/ChangePassword', () => () => <div>ChangePassword</div>);
jest.mock('../page/user/ChatOfUser', () => () => <div>ChatOfUser</div>);
jest.mock('../page/login/Login', () => () => <div>Login</div>);
jest.mock('../page/login/LoginRentaler', () => () => <div>LoginRentaler</div>);
jest.mock('../page/login/LoginAdmin', () => () => <div>LoginAdmin</div>);
jest.mock('../page/signup/Signup', () => () => <div>Signup</div>);
jest.mock('../page/signup/SignupRentaler', () => () => <div>SignupRentaler</div>);
jest.mock('../page/admin/DashboardAdmin', () => () => <div>DashboardAdmin</div>);
jest.mock('../page/admin/RoomManagerment', () => () => <div>RoomManagement</div>);
jest.mock('../page/admin/AccountManagement', () => () => <div>AccountManagement</div>);
jest.mock('../page/admin/SendEmail', () => () => <div>SendEmail</div>);
jest.mock('../page/admin/Authorization', () => () => <div>Authorization</div>);
jest.mock('../page/rentaler/DashboardRentaler', () => () => <div>DashboardRentaler</div>);
jest.mock('../page/rentaler/AddRoom', () => () => <div>AddRoom</div>);
jest.mock('../page/rentaler/RoomManagement', () => () => <div>RoomManagement</div>);
jest.mock('../page/rentaler/EditRoom', () => () => <div>EditRoom</div>);
jest.mock('../page/rentaler/ContractManagement', () => () => <div>ContractManagement</div>);
jest.mock('../page/rentaler/AddContract', () => () => <div>AddContract</div>);
jest.mock('../page/rentaler/EditContract', () => () => <div>EditContract</div>);
jest.mock('../page/rentaler/MaintenceManagement', () => () => <div>MaintenceManagement</div>);
jest.mock('../page/rentaler/AddMaintence', () => () => <div>AddMaintence</div>);
jest.mock('../page/rentaler/EditMaintence', () => () => <div>EditMaintence</div>);
jest.mock('../page/rentaler/RequierManagement', () => () => <div>RequierManagement</div>);
jest.mock('../page/rentaler/ExportBillRequier', () => () => <div>ExportBillRequier</div>);
jest.mock('../page/rentaler/ExportCheckoutRoom', () => () => <div>ExportCheckoutRoom</div>);
jest.mock('../page/rentaler/ProfileRentaler', () => () => <div>ProfileRentaler</div>);
jest.mock('../page/rentaler/ChangePassword', () => () => <div>ChangePassword</div>);
jest.mock('../page/rentaler/Chat', () => () => <div>Chat</div>);
jest.mock('../common/NotFound', () => () => <div>NotFound</div>);
jest.mock('../common/ForgotPassword', () => () => <div>ForgotPassword</div>);
jest.mock('../common/ResetPassword', () => () => <div>ResetPassword</div>);
jest.mock('../common/SuccessConfirmed', () => () => <div>SuccessConfirmed</div>);
jest.mock('../oauth2/OAuth2RedirectHandler', () => () => <div>OAuth2RedirectHandler</div>);
jest.mock('../page/messages/pages/Home', () => () => <div>Message</div>);

import App from '../App';
import { getCurrentUser, getCurrentRentaler, getCurrentAdmin } from '../services/fetch/ApiUtils';

describe('App Component', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        localStorage.clear();
    });

    test('shows loading initially', () => {
        localStorage.setItem('accessToken', 'test-token');
        getCurrentUser.mockReturnValue(new Promise(() => {}));
        getCurrentRentaler.mockReturnValue(new Promise(() => {}));
        getCurrentAdmin.mockReturnValue(new Promise(() => {}));

        render(<App />);
        expect(screen.getByText(/Loading/)).toBeInTheDocument();
    });

    test('clears token when all auth calls fail', async () => {
        localStorage.setItem('accessToken', 'test-token');
        getCurrentUser.mockRejectedValue(new Error('Not authenticated'));
        getCurrentRentaler.mockRejectedValue(new Error('Not authenticated'));
        getCurrentAdmin.mockRejectedValue(new Error('Not authenticated'));

        render(<App />);

        await waitFor(() => {
            expect(localStorage.getItem('accessToken')).toBeNull();
        });
    });

    test('sets authenticated when user loads successfully', async () => {
        localStorage.setItem('accessToken', 'test-token');
        getCurrentUser.mockResolvedValue({
            name: 'Test User',
            roles: [{ name: 'ROLE_USER' }]
        });

        render(<App />);

        await waitFor(() => {
            expect(screen.queryByText(/Loading/)).not.toBeInTheDocument();
        });
        expect(screen.getByText('Main')).toBeInTheDocument();
    });

    test('tries user then rentaler then admin sequentially', async () => {
        localStorage.setItem('accessToken', 'test-token');
        getCurrentUser.mockRejectedValue(new Error('Not auth'));
        getCurrentRentaler.mockRejectedValue(new Error('Not auth'));
        getCurrentAdmin.mockResolvedValue({
            name: 'Admin User',
            roles: [{ name: 'ROLE_ADMIN' }]
        });

        render(<App />);

        await waitFor(() => {
            expect(screen.queryByText(/Loading/)).not.toBeInTheDocument();
        });
        expect(getCurrentUser).toHaveBeenCalled();
        expect(getCurrentRentaler).toHaveBeenCalled();
        expect(getCurrentAdmin).toHaveBeenCalled();
    });

    test('skips loading when no token', async () => {
        render(<App />);

        await waitFor(() => {
            expect(screen.queryByText(/Loading/)).not.toBeInTheDocument();
        });
        expect(getCurrentUser).not.toHaveBeenCalled();
    });
});
