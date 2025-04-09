import React, { useContext } from "react";
import { Link, useNavigate } from "react-router-dom";
import { AuthContext } from "../context/AuthContext";
import "./Navbar.css";

const Navbar = () => {
  const { isAuthenticated, user, logout } = useContext(AuthContext);
  const navigate = useNavigate();

  if (!isAuthenticated || !user) return null;

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <nav>
      <Link to="/dashboard">Dashboard</Link>
      {user.is_staff && <Link to="/analysts">Analysts</Link>}
      <button onClick={handleLogout}>Logout</button>
    </nav>
  );
};

export default Navbar;
