import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import backgroundImage from "../assets/bg.png";
import eyLogo from "../assets/ey.png";

const RequestAccess = () => {
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("Analyst");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post(
        "http://localhost:8000/users/api/request-access/",
        {
          email,
          role,
        }
      );
      setMessage(response.data.message);
      setError("");
      setTimeout(() => navigate("/login"), 3000); // Redirect after 3 seconds
    } catch (err) {
      if (err.response && err.response.data && err.response.data.error) {
        setError(err.response.data.error);
      } else {
        setError("Request failed. Please try again.");
      }
      setMessage("");
    }
  };

  return (
    <div
      className="full-screen-bg"
      style={{ backgroundImage: `url(${backgroundImage})` }}
    >
      <div className="inner-container">
        <img src={eyLogo} alt="EY Logo" className="logo" />
        <h2 className="heading">Request Access</h2>
        {message && <p className="success-text">{message}</p>}
        {error && <p className="error-text">{error}</p>}
        <form onSubmit={handleSubmit}>
          <div>
            <input
              type="email"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="input-field"
            />
          </div>
          <div>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value)}
              className="input-field"
            >
              <option value="Analyst">Analyst</option>
              <option value="Admin">Admin</option>
            </select>
          </div>
          <button type="submit" className="button">
            Request Access
          </button>
        </form>
      </div>
    </div>
  );
};

export default RequestAccess;
