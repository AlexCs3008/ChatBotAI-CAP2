import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import '../../css/AuthForms.css';

const Login = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [loginError, setLoginError] = useState('');

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
    
    // Clear error for this field if user is typing
    if (errors[name]) {
      setErrors({
        ...errors,
        [name]: ''
      });
    }
    
    // Clear general login error when user makes changes
    if (loginError) {
      setLoginError('');
    }
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Email is invalid';
    }
    
    if (!formData.password) {
      newErrors.password = 'Password is required';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    setIsLoading(true);
    
    try {
      // This would be replaced with your actual API call
      const response = await mockLoginApi(formData);
      
      if (response.success) {
        // Store authentication token
        localStorage.setItem('authToken', response.token);
        localStorage.setItem('userType', 'authenticated');
        localStorage.setItem('userId', response.userId);
        
        // Check if user has already customized their bot
        const hasBotCustomization = localStorage.getItem('botCustomization');
        
        // Redirect based on customization status
        if (hasBotCustomization) {
          navigate('/chat');
        } else {
          navigate('/customize-bot');
        }
      } else {
        setLoginError(response.message || 'Login failed. Please check your credentials.');
      }
    } catch (error) {
      setLoginError('An error occurred. Please try again later.');
      console.error('Login error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Mock API call - replace with actual implementation
  const mockLoginApi = async (data) => {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Mock successful login (replace with actual API call)
    return {
      success: true,
      token: 'mock-jwt-token',
      userId: '123',
      message: 'Login successful'
    };
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <h1 className="auth-title">Login</h1>
          <p className="auth-subtitle">Welcome back! Please login to your account.</p>
        </div>
        
        {loginError && (
          <div className="auth-error-message">
            {loginError}
          </div>
        )}
        
        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              className={errors.email ? 'input-error' : ''}
              placeholder="Enter your email"
            />
            {errors.email && <p className="error-text">{errors.email}</p>}
          </div>
          
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              className={errors.password ? 'input-error' : ''}
              placeholder="Enter your password"
            />
            {errors.password && <p className="error-text">{errors.password}</p>}
          </div>
          
          <div className="form-options">
            <div className="remember-me">
              <input type="checkbox" id="remember" />
              <label htmlFor="remember">Remember me</label>
            </div>
            <Link to="/forgot-password" className="forgot-password">
              Forgot password?
            </Link>
          </div>
          
          <button 
            type="submit" 
            className="auth-button"
            disabled={isLoading}
          >
            {isLoading ? 'Logging in...' : 'Login'}
          </button>
        </form>
        
        <div className="auth-footer">
          <p>
            Don't have an account? <Link to="/register" className="auth-link">Register</Link>
          </p>
          <p>
            Or <Link to="/" className="auth-link">continue as guest</Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login; 