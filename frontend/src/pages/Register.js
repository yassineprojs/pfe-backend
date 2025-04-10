// src/Register.js
import React, { useState } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import axios from "axios";
import backgroundImage from "../assets/bg.png";
import eyLogo from "../assets/ey.png";

const Register = () => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const { token } = useParams();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }
    try {
      await axios.post(`http://localhost:8000/users/api/register/${token}/`, {
        username,
        password,
        confirm_password: confirmPassword,
      });
      navigate("/login");
    } catch (err) {
      if (err.response && err.response.data && err.response.data.error) {
        setError(err.response.data.error);
      } else {
        setError("Registration failed. Invalid token or server error.");
      }
    }
  };

  return (
    <div
      className="full-screen-bg"
      style={{ backgroundImage: `url(${backgroundImage})` }}
    >
      <div className="inner-container">
        <img src={eyLogo} alt="EY Logo" className="logo" />
        <h2 className="heading">Register</h2>
        {error && <p className="error-text">{error}</p>}
        <form onSubmit={handleSubmit}>
          <div>
            <input
              type="text"
              placeholder="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="input-field"
            />
          </div>
          <div>
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input-field"
            />
          </div>
          <div>
            <input
              type="password"
              placeholder="Confirm Password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="input-field"
            />
          </div>
          <button type="submit" className="button">
            Register
          </button>
        </form>
        <p className="text-center">
          Already have an account?{" "}
          <Link to="/login" className="link-text">
            Login here
          </Link>
        </p>
      </div>
    </div>
  );
};

export default Register;
