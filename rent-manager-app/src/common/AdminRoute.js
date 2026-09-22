import React from 'react';
import { Navigate } from 'react-router-dom';

const AdminRoute = ({ authenticated, role, children }) => {
  if (!authenticated) {
    return <Navigate to="/login-admin" />;
  }
  if (role !== 'ROLE_ADMIN') {
    return <Navigate to="/" />;
  }
  return children;
};

export default AdminRoute;
