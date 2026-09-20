import React, { Component } from "react";
import './Login.css';
import { ACCESS_TOKEN, FACEBOOK_AUTH_URL, GOOGLE_AUTH_URL } from "../../constants/Connect";
import { Link, Navigate, useNavigate, useLocation } from 'react-router-dom';
import { toast } from 'react-toastify';
import { useEffect } from "react";
import { login, resendConfirmation, changeConfirmedStatus } from "../../services/fetch/ApiUtils";
import { useState } from "react";

function LoginRentaler(props) {
    const history = useNavigate();
    const location = useLocation();

    useEffect(() => {
        // If the OAuth2 login encounters an error, the user is redirected to the /login page with an error.
        // Here we display the error and then remove the error query parameter from the location.
        if (location.state && location.state.error) {
            setTimeout(() => {
                toast.error(location.state.error, {
                    timeout: 5000
                });
                history.replace({
                    pathname: location.pathname,
                    state: {}
                });
            }, 2000);
        }
    }, [location.state, location.pathname, history]);

    const uRole = (props.currentUser && props.currentUser.roles && (
        typeof props.currentUser.roles[0] === 'string'
            ? props.currentUser.roles[0]
            : (props.currentUser.roles[0]?.name?.trim() || props.currentUser.roles[0]?.name)
    )) || props.role;

    if (props.authenticated) {
        if (uRole === "ROLE_RENTALER") {
            return <Navigate
                to={{
                    pathname: "/rentaler/room-management",
                    state: { from: location }
                }} />;
        } else if (uRole === "ROLE_ADMIN") {
            return <Navigate
                to={{
                    pathname: "/admin",
                    state: { from: location }
                }} />;
        } else {
            return <Navigate
                to={{
                    pathname: "/",
                    state: { from: location }
                }} />;
        }
    }

    return (
        <>
            <div className="content">
                <div className="container">
                    <div className="row">
                        <div className="col-md-6 order-md-2">
                            <img src="../../assets/img/undraw_file_sync_ot38.svg" alt="Image" className="img-fluid" />
                        </div>
                        <div className="col-md-6 contents">
                            <div className="row justify-content-center">
                                <div className="col-md-8">
                                    <div className="mb-4">
                                        <h3>Đăng nhập <a href="/" style={{ textDecoration: 'none' }}>Estate<span className="color-b">Agency</span></a></h3>
                                        <p className="mb-4">Nếu bạn chưa có tài khoản. <a href="/signup-rentaler">Đăng ký tài khoản mới</a></p>
                                    </div>
                                    <LoginForm onLoginSuccess={props.onLoginSuccess} />
                                </div>
                            </div>

                        </div>

                    </div>
                </div>
            </div>
        </>
    )
}

function LoginForm(props) {
    const history = useNavigate();
    const [formState, setFormState] = useState({
        email: '',
        password: ''
    });
    const [showResendConfirm, setShowResendConfirm] = useState(false);
    const [unconfirmedEmail, setUnconfirmedEmail] = useState('');
    const [resendLoading, setResendLoading] = useState(false);
    const [directActivating, setDirectActivating] = useState(false);

    const handleInputChange = event => {
        const target = event.target;
        const inputName = target.name;
        const inputValue = target.value;

        setFormState(prevState => ({
            ...prevState,
            [inputName]: inputValue
        }));
    };

    const handleSubmit = event => {
        event.preventDefault();

        const loginRequest = { ...formState };

        login(loginRequest)
            .then(response => {
                localStorage.setItem(ACCESS_TOKEN, response.accessToken);
                toast.success("Bạn đã đăng nhập thành công!!");
                setShowResendConfirm(false);
                if (props.onLoginSuccess) {
                    props.onLoginSuccess();
                } else {
                    window.location.href = "/rentaler";
                }
            }).catch(error => {
                const errorCode = error && error.errorCode;
                const message = (error && error.message) || 'Oops! Có điều gì đó xảy ra. Vui lòng thử lại!';

                const isUnconfirmed = errorCode === 'ACCOUNT_NOT_CONFIRMED' || 
                    (message && (
                        message.toLowerCase().includes('xác thực') || 
                        message.toLowerCase().includes('kích hoạt') || 
                        message.toLowerCase().includes('chưa được') ||
                        message.toLowerCase().includes('disabled')
                    ));

                if (isUnconfirmed) {
                    setUnconfirmedEmail(formState.email);
                    setShowResendConfirm(true);
                    toast.warn(message);
                } else {
                    setShowResendConfirm(false);
                    toast.error(message);
                }
            });
    };

    const handleDirectActivate = () => {
        if (!unconfirmedEmail) return;
        setDirectActivating(true);
        changeConfirmedStatus({ email: unconfirmedEmail })
            .then(response => {
                toast.success(response.message || 'Tài khoản đã được kích hoạt thành công! Hãy nhấn Đăng nhập.');
                setShowResendConfirm(false);
            })
            .catch(error => {
                toast.error((error && error.message) || 'Không thể kích hoạt tài khoản. Vui lòng thử lại!');
            })
            .finally(() => {
                setDirectActivating(false);
            });
    };

    const handleResendConfirmation = () => {
        if (!unconfirmedEmail) return;
        setResendLoading(true);
        resendConfirmation({ email: unconfirmedEmail })
            .then(response => {
                toast.success(response.message || 'Email xác thực đã được gửi lại!');
                setShowResendConfirm(false);
            })
            .catch(error => {
                toast.error((error && error.message) || 'Không thể gửi email. Vui lòng thử lại!');
            })
            .finally(() => {
                setResendLoading(false);
            });
    };

    return (
        <>
            <form onSubmit={handleSubmit}>
                <div className="form-group first">
                    <span>Email</span>
                    <input type="email" className="form-control" name="email" value={formState.email} onChange={handleInputChange} required />

                </div>
                <div className="form-group last mb-4">
                    <span>Mật khẩu</span>
                    <input type="password" className="form-control" name="password" value={formState.password} onChange={handleInputChange} required />
                </div>
                <div className="d-flex mb-5 align-items-center">
                    <span className="ml-auto"><a href="/forgot-password" className="forgot-pass">Quên mật khẩu</a></span>
                </div>
                <input type="submit" value="Đăng nhập" className="btn text-white btn-block btn-primary" />
            </form>

            {showResendConfirm && (
                <div style={{
                    marginTop: '16px',
                    padding: '14px 16px',
                    background: '#fff8e1',
                    border: '1px solid #ffe082',
                    borderRadius: '8px',
                    fontSize: '14px'
                }}>
                    <p style={{ margin: '0 0 10px', color: '#5d4037', fontWeight: 500 }}>
                        ⚠️ Tài khoản <strong>{unconfirmedEmail}</strong> chưa được xác thực.
                    </p>
                    <p style={{ margin: '0 0 12px', color: '#6d4c41' }}>
                        Bạn có thể kích hoạt tài khoản ngay bây giờ hoặc gửi lại email xác thực:
                    </p>
                    <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                        <button
                            type="button"
                            onClick={handleDirectActivate}
                            disabled={directActivating}
                            style={{
                                background: '#2e7d32',
                                color: '#fff',
                                border: 'none',
                                borderRadius: '6px',
                                padding: '8px 14px',
                                cursor: directActivating ? 'not-allowed' : 'pointer',
                                fontWeight: 600,
                                fontSize: '13px',
                                opacity: directActivating ? 0.7 : 1
                            }}
                        >
                            {directActivating ? 'Đang kích hoạt...' : '⚡ Kích hoạt tài khoản ngay'}
                        </button>
                        <button
                            type="button"
                            onClick={handleResendConfirmation}
                            disabled={resendLoading}
                            style={{
                                background: '#e65100',
                                color: '#fff',
                                border: 'none',
                                borderRadius: '6px',
                                padding: '8px 14px',
                                cursor: resendLoading ? 'not-allowed' : 'pointer',
                                fontWeight: 600,
                                fontSize: '13px',
                                opacity: resendLoading ? 0.7 : 1
                            }}
                        >
                            {resendLoading ? 'Đang gửi...' : '📧 Gửi lại email'}
                        </button>
                    </div>
                </div>
            )}
        </>
    )
}

export default LoginRentaler;