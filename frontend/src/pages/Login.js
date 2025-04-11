import React, { useState, useContext } from "react";
import { useNavigate, Link } from "react-router-dom";
import { AuthContext } from "../context/AuthContext";
import backgroundImage from "../assets/bg.png";
import eyLogo from "../assets/ey.png";
import "./auth.css";

const Login = () => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const { login } = useContext(AuthContext);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    const success = await login(username, password);
    if (success) {
      navigate("/dashboard");
    } else {
      setError("Invalid credentials or account not approved.");
    }
  };

  return (
    <div
      className="full-screen-bg"
      style={{ backgroundImage: `url(${backgroundImage})` }}
    >
      <div className="inner-container">
        <img src={eyLogo} alt="EY Logo" className="logo" />
        <h2 className="heading">Login</h2>
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
          <button type="submit" className="button">
            Login
          </button>
        </form>
        <p className="text-center">
          Need an account?{" "}
          <Link to="/request-access" className="link-text">
            Request access here
          </Link>
        </p>
      </div>
    </div>
  );
};

export default Login;
