import React, { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import axios from "axios";
import "./App.css";

// Import components
import AuthPage from "./components/AuthPage";
import Dashboard from "./components/Dashboard";
import Navigation from "./components/Navigation";
import AstrologyPage from "./components/AstrologyPage";
import TarotPage from "./components/TarotPage";
import SessionsPage from "./components/SessionsPage";
import ProfilePage from "./components/ProfilePage";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { Toaster } from "./components/ui/sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Configure axios defaults
axios.defaults.baseURL = API;

// Create a query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      cacheTime: 1000 * 60 * 10, // 10 minutes
    },
  },
});

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center celestial-bg">
        <div className="animate-mystical-glow">
          <div className="loading-spinner w-16 h-16"></div>
        </div>
      </div>
    );
  }
  
  if (!user) {
    return <Navigate to="/auth" replace />;
  }
  
  return children;
};

// Main App Layout
const AppLayout = () => {
  const { user } = useAuth();
  
  return (
    <div className="min-h-screen celestial-bg">
      <Navigation />
      <main className="container mx-auto px-4 py-8">
        <Routes>
          <Route path="/auth" element={<AuthPage />} />
          <Route path="/dashboard" element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          } />
          <Route path="/astrology" element={
            <ProtectedRoute>
              <AstrologyPage />
            </ProtectedRoute>
          } />
          <Route path="/tarot" element={
            <ProtectedRoute>
              <TarotPage />
            </ProtectedRoute>
          } />
          <Route path="/sessions" element={
            <ProtectedRoute>
              <SessionsPage />
            </ProtectedRoute>
          } />
          <Route path="/profile" element={
            <ProtectedRoute>
              <ProfilePage />
            </ProtectedRoute>
          } />
          <Route path="/" element={
            user ? <Navigate to="/dashboard" replace /> : <Navigate to="/auth" replace />
          } />
        </Routes>
      </main>
      <Toaster />
    </div>
  );
};

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <AppLayout />
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;