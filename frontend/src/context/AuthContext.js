import React, { createContext, useState, useEffect } from "react";
import axios from "axios";

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("token");
    const storedUser = JSON.parse(localStorage.getItem("user"));
    if (token && storedUser) {
      setIsAuthenticated(true);
      setUser(storedUser);
      axios.defaults.headers.common["Authorization"] = `Token ${token}`;
    }
    setLoading(false);
  }, []);

  const login = async (username, password) => {
    try {
      const response = await axios.post(
        "http://localhost:8000/users/api/login/",
        { username, password }
      );
      const { token, user } = response.data;
      localStorage.setItem("token", token);
      localStorage.setItem("user", JSON.stringify(user));
      axios.defaults.headers.common["Authorization"] = `Token ${token}`;
      setIsAuthenticated(true);
      setUser(user);
      return true;
    } catch (error) {
      console.error(error);
      return false;
    }
  };

  const logout = async () => {
    try {
      await axios.post("http://localhost:8000/users/api/logout/");
    } catch (error) {
      console.error(error);
    }
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    delete axios.defaults.headers.common["Authorization"];
    setIsAuthenticated(false);
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{ isAuthenticated, user, login, logout, loading }}
    >
      {children}
    </AuthContext.Provider>
  );
};
