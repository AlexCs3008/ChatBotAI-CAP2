import React from 'react';
import { useNavigate } from 'react-router-dom';
import '../css/WelcomePage.css';

const WelcomePage = () => {
  const navigate = useNavigate();

  const handleGuestLogin = () => {
    // Set user as guest in local storage or state management
    localStorage.setItem('userType', 'guest');
    navigate('/customize-bot');
  };

  const handleLoginClick = () => {
    navigate('/login');
  };

  return (
    <div className="welcome-container">
      <div className="welcome-card">
        <div className="logo-container">
          <img src="\src\assets\logo.png" alt="ChatBot Logo" className="logo" />
        </div>
        
        <h1 className="welcome-title">Welcome to ChatBot!</h1>
        
        <p className="welcome-message">
          Your intelligent conversation partner. Get started by choosing how you'd like to proceed.
        </p>
        
        <div className="button-container">
          <button 
            className="btn login-btn" 
            onClick={handleLoginClick}
          >
            Login / Register
          </button>
          
          <button 
            className="btn guest-btn" 
            onClick={handleGuestLogin}
          >
            Continue as Guest
          </button>
        </div>
        
        <p className="feature-note">
          *Creating an account unlocks additional features and saves your preferences.
        </p>
      </div>
    </div>
  );
};

export default WelcomePage;