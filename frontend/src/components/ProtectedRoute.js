import React, { useContext } from "react";
import { Route, Navigate } from "react-router-dom";
import { AuthContext } from "../context/AuthContext";

const ProtectedRoute = ({ element: Element, ...rest }) => {
  const { isAuthenticated, loading } = useContext(AuthContext);

  if (loading) return <div>Loading...</div>;

  return isAuthenticated ? <Element {...rest} /> : <Navigate to="/login" />;
};

export default ProtectedRoute;
