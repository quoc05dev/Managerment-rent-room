import React, { Component } from "react";
import { Link, NavLink } from 'react-router-dom';
import './Profile.css';

class Header extends Component {


    render() {
        console.log("logout", this.props.onLogout)
        return (
            <>
                <nav className="navbar navbar-default navbar-trans navbar-expand-lg fixed-top">
                    <div className="container">
                        <button className="navbar-toggler collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#navbarDefault" aria-controls="navbarDefault" aria-expanded="false" aria-label="Toggle navigation">
                            <span></span>
                            <span></span>
                            <span></span>
                        </button>
                        <a className="navbar-brand text-brand" href="/">PhongTro<span className="color-b">SinhVien</span></a>

                        <div className="navbar-collapse collapse justify-content-center" id="navbarDefault">
                            <ul className="navbar-nav">

                                <li className="nav-item">
                                    <NavLink className="nav-link " to="/" activeClassName="active">
                                        Trang chủ
                                    </NavLink>
                                </li>

                                <li className="nav-item">
                                    <NavLink className="nav-link " to="/rental-home" activeClassName="active">
                                        Nhà cho thuê
                                    </NavLink>
                                </li>
                                <li className="nav-item">
                                    <NavLink className="nav-link " to="/contact" activeClassName="active">
                                        Liên hệ
                                    </NavLink>
                                </li>
                                <li className="nav-item">
                                    <NavLink className="nav-link " to="/angent-gird" activeClassName="active">
                                        Người cho thuê
                                    </NavLink>
                                </li>

                                {(() => {
                                    const uRole = (this.props.currentUser && this.props.currentUser.roles && (
                                        typeof this.props.currentUser.roles[0] === 'string'
                                            ? this.props.currentUser.roles[0]
                                            : (this.props.currentUser.roles[0]?.name?.trim() || this.props.currentUser.roles[0]?.name)
                                    )) || this.props.role;

                                    if (uRole === "ROLE_RENTALER") {
                                        return (
                                            <>
                                                <li className="nav-item">
                                                    <NavLink className="nav-link text-success font-weight-bold" to="/rentaler/room-management" style={{ fontWeight: 'bold' }}>
                                                        Quản lý phòng trọ
                                                    </NavLink>
                                                </li>
                                                <li className="nav-item">
                                                    <NavLink className="nav-link text-primary font-weight-bold" to="/rentaler" style={{ fontWeight: 'bold' }}>
                                                        Bảng điều khiển
                                                    </NavLink>
                                                </li>
                                            </>
                                        );
                                    }
                                    if (uRole === "ROLE_ADMIN") {
                                        return (
                                            <li className="nav-item">
                                                <NavLink className="nav-link text-danger font-weight-bold" to="/admin" style={{ fontWeight: 'bold' }}>
                                                    Trang Quản trị
                                                </NavLink>
                                            </li>
                                        );
                                    }
                                    return null;
                                })()}
                            </ul>
                        </div>
                        {!this.props.authenticated ? (
                            <>
                                <button type="button" className="btn btn-outline-success" style={{ borderRadius: "20px" }}>
                                    <Link to="/login" style={{ textDecoration: 'none', color: 'inherit' }}>
                                        Đăng nhập
                                    </Link>
                                </button>
                                &nbsp;&nbsp;
                                <button type="button" className="btn btn-outline-success" style={{ borderRadius: "20px" }}>
                                    <Link to="/signup" style={{ textDecoration: 'none', color: 'inherit' }}>
                                        Đăng kí
                                    </Link>
                                </button>
                                &nbsp;&nbsp;
                                <button type="button" className="btn btn-success" style={{ borderRadius: "20px" }}>
                                    <Link to="/login-rentaler" style={{ textDecoration: 'none', color: 'white' }}>
                                        Đăng tin
                                    </Link>
                                </button>
                            </>
                        ) : (
                            <>
                                <div className="profile-info" style={{ display: 'flex', alignItems: 'center' }}>
                                    {(() => {
                                        const uRole = (this.props.currentUser && this.props.currentUser.roles && (
                                            typeof this.props.currentUser.roles[0] === 'string'
                                                ? this.props.currentUser.roles[0]
                                                : (this.props.currentUser.roles[0]?.name?.trim() || this.props.currentUser.roles[0]?.name)
                                        )) || this.props.role;

                                        if (uRole === "ROLE_RENTALER") {
                                            return (
                                                <Link to="/rentaler/add-room" style={{ marginRight: '12px' }}>
                                                    <button type="button" className="btn btn-success btn-sm" style={{ borderRadius: "20px", fontWeight: 'bold', padding: '6px 14px' }}>
                                                        ➕ Đăng tin phòng mới
                                                    </button>
                                                </Link>
                                            );
                                        }
                                        return null;
                                    })()}

                                    <div className="profile-avatar">
                                        {
                                            this.props.currentUser && this.props.currentUser.imageUrl ? (
                                                <img src={this.props.currentUser.imageUrl}
                                                    alt={this.props.currentUser.name} className="img-fluid rounded-circle border border-dark border-3"
                                                    style={{ width: "45px", height: "45px", objectFit: "cover" }} />

                                            ) : (
                                                <div className="text-avatar" style={{ width: "45px", height: "45px" }}>
                                                    <span style={{ lineHeight: "45px" }}>{this.props.currentUser && this.props.currentUser.name && this.props.currentUser.name[0]}</span>
                                                </div>
                                            )
                                        }
                                    </div>
                                    <div className="flex-grow-1 ms-3">
                                        <div className="d-flex flex-row align-items-center mb-1">
                                            <p className="mb-0 me-2" style={{ fontWeight: '600' }}>{this.props.currentUser && this.props.currentUser.name}</p>
                                        </div>
                                        <div style={{ display: 'flex', gap: '5px', flexWrap: 'wrap' }}>
                                            {(() => {
                                                const uRole = (this.props.currentUser && this.props.currentUser.roles && (
                                                    typeof this.props.currentUser.roles[0] === 'string'
                                                        ? this.props.currentUser.roles[0]
                                                        : (this.props.currentUser.roles[0]?.name?.trim() || this.props.currentUser.roles[0]?.name)
                                                )) || this.props.role;
                                                return (
                                                    <>
                                                        {uRole === "ROLE_RENTALER" && (
                                                            <Link to="/rentaler/room-management">
                                                                <button type="button" className="btn btn-success btn-sm"
                                                                    style={{ borderRadius: "20px" }}>Quản lý phòng</button>
                                                            </Link>
                                                        )}
                                                        {uRole === "ROLE_ADMIN" && (
                                                            <Link to="/admin">
                                                                <button type="button" className="btn btn-primary btn-sm"
                                                                    style={{ borderRadius: "20px" }}>Trang Quản trị</button>
                                                            </Link>
                                                        )}
                                                    </>
                                                );
                                            })()}
                                            <Link to="/profile">
                                                <button type="button" className="btn btn-outline-success btn-sm"
                                                    style={{ borderRadius: "20px" }}>Hồ Sơ</button>
                                            </Link>
                                            <button type="button" className="btn btn-outline-danger btn-sm"
                                                style={{ borderRadius: "20px" }} onClick={this.props.onLogout}>Đăng xuất</button>
                                        </div>
                                    </div>
                                    
                                </div>
                            </>
                        )}
                    </div>
                </nav>
            </>
        )
    }
}

export default Header;