import React from 'react';
import { Navigate } from 'react-router-dom';

const RentalerRoute = ({ authenticated, role, children }) => {
  if (!authenticated) {
    return <Navigate to="/login-rentaler" />;
  }
  if (role !== 'ROLE_RENTALER' && role !== 'ROLE_ADMIN') {
    return <Navigate to="/" />;
  }
  return children;
};

export default RentalerRoute;
