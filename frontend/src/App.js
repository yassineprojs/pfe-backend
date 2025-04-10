import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboards";
import IncidentDetail from "./pages/IncidentDetails";
import ProtectedRoute from "./components/ProtectedRoute";
import Navbar from "./components/Navbar";
import RequestAccess from "./components/RequestAccess";

function App() {
  return (
    <Router>
      <Navbar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/register/:token" element={<Register />} />
        <Route path="/request-access" element={<RequestAccess />} />
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
