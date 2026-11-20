import React from "react";
import { NavLink } from 'react-router-dom';
import { useSidebar } from '../../common/SidebarContext';

const SidebarNav = (props) => {
  const { currentUser, onLogout } = props;
  const { accountOpen, toggleAccount, closeAccount } = useSidebar();

  const handleAccountClick = (event) => {
    event.preventDefault();
    toggleAccount();
  };

  const handleLogoutClick = (event) => {
    event.preventDefault();
    closeAccount();
    if (onLogout) {
      onLogout();
    }
  };

  return (
    <>
      <ul className="sidebar-nav">
        <li className="sidebar-header">
          Quản lí chức năng
        </li>
        <li className="sidebar-item">
          <NavLink to="/admin" className="sidebar-link">
            <i className="align-middle" data-feather="sliders"></i> <span className="align-middle">Thống kê</span>
          </NavLink>
        </li>
        <li className="sidebar-item">
          <NavLink to="/admin/account-management" className="sidebar-link">
            <i className="align-middle" data-feather="sliders"></i> <span className="align-middle">Quản lý tài khoản</span>
          </NavLink>
        </li>
        <li className="sidebar-item">
          <NavLink to="/admin/room-management" className="sidebar-link">
            <i className="align-middle" data-feather="sliders"></i> <span className="align-middle">Quản lý phòng trọ</span>
          </NavLink>
        </li>
      </ul>

      <div className="sidebar-account">
        <a
          href="#"
          className="sidebar-account-toggle"
          onClick={handleAccountClick}
          aria-expanded={accountOpen}
        >
          <img
            src="../../assets/img/author-2.jpg"
            className="sidebar-account-avatar"
            alt={currentUser && currentUser.name ? currentUser.name : "Tài khoản"}
          />
          <span className="sidebar-account-text">
            <span className="sidebar-account-name">
              {currentUser === null || currentUser === undefined ? "Tài khoản" : currentUser.name}
            </span>
            <span className="sidebar-account-role">Quản trị viên</span>
          </span>
          <i className={`bi ${accountOpen ? 'bi-chevron-down' : 'bi-chevron-right'} sidebar-account-chevron`}></i>
        </a>

        {accountOpen && (
          <ul className="sidebar-account-menu">
            <li className="sidebar-item">
              <NavLink to="/admin" className="sidebar-link" onClick={closeAccount}>
                <i className="bi bi-house-door align-middle"></i> <span className="align-middle">Trang chủ</span>
              </NavLink>
            </li>
            <li className="sidebar-item">
              <NavLink to="/rental-home" className="sidebar-link" onClick={closeAccount}>
                <i className="bi bi-buildings align-middle"></i> <span className="align-middle">Nhà cho thuê</span>
              </NavLink>
            </li>
            <li className="sidebar-item">
              <NavLink to="/profile" className="sidebar-link" onClick={closeAccount}>
                <i className="bi bi-person-badge align-middle"></i> <span className="align-middle">Hồ sơ</span>
              </NavLink>
            </li>
            <li className="sidebar-item">
              <a href="#" className="sidebar-link sidebar-logout" onClick={handleLogoutClick}>
                <i className="bi bi-box-arrow-right align-middle"></i> <span className="align-middle">Đăng xuất</span>
              </a>
            </li>
          </ul>
        )}
      </div>
    </>
  )
}

export default SidebarNav;
