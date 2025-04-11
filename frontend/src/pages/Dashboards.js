import React, { useState, useEffect, useContext } from "react";
import axios from "axios";
import { Link } from "react-router-dom";
import { AuthContext } from "../context/AuthContext";
import "./Dashboard.css";

const Dashboard = () => {
  const { user } = useContext(AuthContext); // Assumes user includes analyst_id or username
  const [allIncidents, setAllIncidents] = useState([]);
  const [myIncidents, setMyIncidents] = useState([]);
  const [filters, setFilters] = useState({
    status: "",
    severity: "",
    analyst: "",
    search: "",
  });
  const [analysts, setAnalysts] = useState([]);

  useEffect(() => {
    fetchAnalysts();
    fetchIncidents();
  }, [filters]);

  const fetchAnalysts = async () => {
    try {
      const response = await axios.get(
        "http://localhost:8000/users/api/analysts/",
        {
          headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
        }
      );
      setAnalysts(response.data);
    } catch (error) {
      console.error("Error fetching analysts:", error);
    }
  };

  const fetchIncidents = async () => {
    try {
      const params = new URLSearchParams(filters);
      const response = await axios.get(
        `http://localhost:8000/incidents/api/incidents/?${params.toString()}`,
        {
          headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
        }
      );
      const incidents = response.data;
      setAllIncidents(incidents);
      const myAnalystId = user.analyst_id; // Adjust based on your AuthContext
      const myIncidents = incidents.filter((incident) =>
        incident.ticket.assigned_analysts.includes(myAnalystId)
      );
      setMyIncidents(myIncidents);
    } catch (error) {
      console.error("Error fetching incidents:", error);
    }
  };

  const handleFilterChange = (e) => {
    setFilters({ ...filters, [e.target.name]: e.target.value });
  };

  const formatSLA = (slaRemaining) => {
    if (!slaRemaining || slaRemaining === "PT0S") return "Overdue";
    const match = slaRemaining.match(/PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?/);
    if (!match) return slaRemaining;
    const [_, hours = 0, minutes = 0, seconds = 0] = match;
    return `${hours}h ${minutes}m`;
  };

  const assignTicket = async (ticketId) => {
    try {
      await axios.post(
        `http://localhost:8000/incidents/api/ticket/${ticketId}/assign/`,
        {},
        {
          headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
        }
      );
      fetchIncidents();
      alert("Ticket assigned successfully.");
    } catch (error) {
      alert(
        "Failed to assign ticket: " +
          (error.response?.data.error || error.message)
      );
    }
  };

  const startWork = async (ticketId) => {
    try {
      await axios.post(
        `http://localhost:8000/incidents/api/ticket/${ticketId}/start/`,
        {},
        {
          headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
        }
      );
      fetchIncidents();
      alert("Work started.");
    } catch (error) {
      alert(
        "Failed to start work: " + (error.response?.data.error || error.message)
      );
    }
  };

  return (
    <div className="dashboard">
      <h1>EY SOC Dashboard</h1>
      <div className="summary">
        <p>Total Open Tickets: {allIncidents.length}</p>
        <p>My Assigned Tickets: {myIncidents.length}</p>
        <button onClick={fetchIncidents} className="refresh-btn button_dash">
          Refresh
        </button>
      </div>

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
          {analysts.map((analyst) => (
            <option key={analyst.id} value={analyst.user.username}>
              {analyst.user.username}
            </option>
          ))}
        </select>
        <input
          type="text"
          name="search"
          value={filters.search}
          onChange={handleFilterChange}
          placeholder="Search by ID or Type"
        />
      </div>

      <section>
        <h2>My Assigned Tickets</h2>
        <table className="incident-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Type</th>
              <th>Severity</th>
              <th>Status</th>
              <th>SLA Remaining</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {myIncidents.map((incident) => (
              <tr key={incident.id}>
                <td>{incident.id}</td>
                <td>{incident.incident_type || `Incident ${incident.id}`}</td>
                <td className={`severity-${incident.severity.toLowerCase()}`}>
                  {incident.severity}
                </td>
                <td>{incident.status}</td>
                <td>{formatSLA(incident.ticket.sla_remaining)}</td>
                <td>
                  {incident.ticket.status === "ASSIGNED" && (
                    <button
                      onClick={() => startWork(incident.ticket.id)}
                      className="button_dash"
                    >
                      Start Work
                    </button>
                  )}
                  {incident.ticket.status === "IN_PROGRESS" && (
                    <button className="button_dash" disabled>
                      Pause (Detail Page)
                    </button>
                  )}
                  <Link to={`/incidents/${incident.id}`}>View Details</Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section>
        <h2>All Open Tickets</h2>
        <table className="incident-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Type</th>
              <th>Severity</th>
              <th>Status</th>
              <th>Assigned To</th>
              <th>SLA Remaining</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {allIncidents.map((incident) => (
              <tr key={incident.id}>
                <td>{incident.id}</td>
                <td>{incident.incident_type || `Incident ${incident.id}`}</td>
                <td className={`severity-${incident.severity.toLowerCase()}`}>
                  {incident.severity}
                </td>
                <td>{incident.status}</td>
                <td>
                  {incident.ticket.assigned_analysts.join(", ") || "Unassigned"}
                </td>
                <td>{formatSLA(incident.ticket.sla_remaining)}</td>
                <td>
                  {incident.ticket.status === "NEW" && (
                    <button
                      className="button_dash"
                      onClick={() => assignTicket(incident.ticket.id)}
                    >
                      Assign to Me
                    </button>
                  )}
                  <Link to={`/incidents/${incident.id}`}>View Details</Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
};

export default Dashboard;
