import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboards";
import IncidentDetail from "./pages/IncidentDetails";
import ProtectedRoute from "./components/ProtectedRoute";
import Navbar from "./components/Navbar";
import "./App.css";

function App() {
  return (
    <Router>
      <Navbar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route
          path="/dashboard"
          element={<ProtectedRoute element={Dashboard} />}
        />
        <Route
          path="/incidents/:id"
          element={<ProtectedRoute element={IncidentDetail} />}
        />
      </Routes>
    </Router>
  );
}

export default App;
