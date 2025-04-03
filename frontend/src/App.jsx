import React, { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';

// Import components
import WelcomePage from './components/WelcomePage';
import BotCustomizationPage from './components/BotCustomizationPage';
import Login from './components/Auth/Login';
import Register from './components/Auth/Register';
import Settings from './components/Settings';
import ChatInterface from './components/ChatInterface';

// Import CSS
import './css/style.css';

// Protected route wrapper
const ProtectedRoute = ({ children }) => {
  const isAuthenticated = localStorage.getItem('authToken') !== null;
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  
  return children;
};

function App() {
  const [initialized, setInitialized] = useState(false);
  
  useEffect(() => {
    // Check if this is the first visit
    const hasVisited = localStorage.getItem('hasVisited');
    
    if (!hasVisited) {
      // First time visitor
      localStorage.setItem('hasVisited', 'true');
      localStorage.setItem('userType', 'guest');
    }
    
    setInitialized(true);
  }, []);
  
  if (!initialized) {
    return <div className="loading-app">Loading...</div>;
  }
  
  return (
    <BrowserRouter>
      <Routes>
        {/* Public routes */}
        <Route path="/" element={<WelcomePage />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        
        {/* Semi-protected routes */}
        <Route 
          path="/customize-bot" 
          element={
            localStorage.getItem('userType') ? 
              <BotCustomizationPage /> : 
              <Navigate to="/" replace />
          } 
        />
        
        <Route 
          path="/chat" 
          element={
            localStorage.getItem('userType') ? 
              <ChatInterface /> : 
              <Navigate to="/" replace />
          } 
        />
        
        {/* Protected routes */}
        <Route 
          path="/settings" 
          element={
            <ProtectedRoute>
              <Settings />
            </ProtectedRoute>
          } 
        />
        
        {/* Catch-all redirect */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;