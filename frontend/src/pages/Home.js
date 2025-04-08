import React from "react";
import { Link } from "react-router-dom";
import "./Home.css";

const Home = () => {
  return (
    <>
      <div className="container">
        <div className="text-section">
          <h1>
            Greetings <br /> SOC Analyst
          </h1>
          <p>Threats never sleep. Neither do we.</p>
        </div>
        <div className="button-section">
          <Link to="/login" className="access-button">
            <span className="arrow">→</span> Access NOW
          </Link>
        </div>
      </div>
    </>
  );
};

export default Home;
