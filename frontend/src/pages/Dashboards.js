import React, { useState, useEffect } from "react";
import axios from "axios";
import { Link } from "react-router-dom";
import "./Dashboards.css";

const Dashboard = () => {
  const [incidents, setIncidents] = useState([]);
  const [filters, setFilters] = useState({
    status: "",
    severity: "",
    analyst: "",
  });

  useEffect(() => {
    fetchIncidents();
  }, [filters]);

  const fetchIncidents = async () => {
    try {
      const response = await axios.get(
        "http://localhost:8000/incidents/api/incidents/",
        {
          params: filters,
        }
      );
      setIncidents(response.data);
    } catch (error) {
      console.error("Error fetching incidents:", error);
    }
  };

  const handleFilterChange = (e) => {
    setFilters({ ...filters, [e.target.name]: e.target.value });
  };

  return (
    <div className="dashboard">
      <h1>Analyst Dashboard</h1>
      <div className="filters">
        <select
          name="status"
          value={filters.status}
          onChange={handleFilterChange}
        >
          <option value="">All Statuses</option>
          <option value="OPEN">Open</option>
          <option value="ASSIGNED">Assigned</option>
          <option value="IN_PROGRESS">In Progress</option>
        </select>
        <select
          name="severity"
          value={filters.severity}
          onChange={handleFilterChange}
        >
          <option value="">All Severities</option>
          <option value="LOW">Low</option>
          <option value="MEDIUM">Medium</option>
          <option value="HIGH">High</option>
        </select>
        <select
          name="analyst"
          value={filters.analyst}
          onChange={handleFilterChange}
        >
          <option value="">All Analysts</option>
          {/* Optionally fetch analysts dynamically */}
        </select>
      </div>
      <div className="incident-list">
        {incidents.map((incident) => (
          <div key={incident.id} className="incident-card">
            <h3>{incident.incident_type || `Incident ${incident.id}`}</h3>
            <p>Status: {incident.status}</p>
            <p>Severity: {incident.severity}</p>
            <Link to={`/incidents/${incident.id}`}>View Details</Link>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Dashboard;
