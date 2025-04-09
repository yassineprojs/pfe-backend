import React from "react";
import { Link } from "react-router-dom";
import "./Home.css";

const Home = () => {
  return (
    <div>
      <h1>Welcome to the SOC Platform</h1>
      <Link to="/login">
        <button>Login</button>
      </Link>
    </div>
  );
};

export default Home;
