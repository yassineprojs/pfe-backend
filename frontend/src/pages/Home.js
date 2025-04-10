// src/Home.js
import React from "react";
import { Link } from "react-router-dom";
import backgroundImage from "../assets/bg.png";
import eyLogo from "../assets/ey.png";

const Home = () => {
  return (
    <div
      className="full-screen-bg"
      style={{ backgroundImage: `url(${backgroundImage})` }}
    >
      <div className="inner-container">
        <img src={eyLogo} alt="EY Logo" className="logo" />
        <h1 className="heading">Welcome to the EY SOC Platform</h1>
        <p className="text">
          Securely monitor and manage security operations with cutting-edge
          technology.
        </p>
        <Link to="/login">
          <button className="button">Login</button>
        </Link>
      </div>
    </div>
  );
};

export default Home;
