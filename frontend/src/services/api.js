// API Service for handling backend communication

const API_URL = 'http://localhost:5000';  // Update based on your backend URL

// Helper function to handle API responses
const handleResponse = async (response) => {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || 'An error occurred');
  }
  return response.json();
};

// Auth token management
const getToken = () => localStorage.getItem('authToken');
const setToken = (token) => localStorage.setItem('authToken', token);
const removeToken = () => localStorage.removeItem('authToken');

// User authentication services
const authService = {
  register: async (userData) => {
    const response = await fetch(`${API_URL}/api/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userData),
      credentials: 'include',
    });
    
    const data = await handleResponse(response);
    setToken(data.token);
    return data;
  },
  
  login: async (credentials) => {
    const response = await fetch(`${API_URL}/api/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(credentials),
      credentials: 'include',
    });
    
    const data = await handleResponse(response);
    setToken(data.token);
    return data;
  },
  
  logout: () => {
    removeToken();
    localStorage.removeItem('userId');
    localStorage.setItem('userType', 'guest');
  },
  
  getCurrentUser: async () => {
    const token = getToken();
    if (!token) return null;
    
    const response = await fetch(`${API_URL}/api/user`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      credentials: 'include',
    });
    
    // If token is invalid, clear it and return null
    if (response.status === 401) {
      removeToken();
      return null;
    }
    
    return handleResponse(response);
  },
  
  updateUser: async (userData) => {
    const token = getToken();
    if (!token) throw new Error('Authentication required');
    
    const response = await fetch(`${API_URL}/api/user`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(userData),
      credentials: 'include',
    });
    
    return handleResponse(response);
  },
  
  changePassword: async (passwordData) => {
    const token = getToken();
    if (!token) throw new Error('Authentication required');
    
    const response = await fetch(`${API_URL}/api/password`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(passwordData),
      credentials: 'include',
    });
    
    return handleResponse(response);
  },
};

// Bot customization services
const botService = {
  saveBotCustomization: async (customization) => {
    const token = getToken();
    const headers = {
      'Content-Type': 'application/json',
    };
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    // Add guest_id if not authenticated
    if (!token && !customization.guest_id) {
      const guestId = localStorage.getItem('guestId') || 
                      Math.random().toString(36).substring(2, 15);
      localStorage.setItem('guestId', guestId);
      customization.guest_id = guestId;
    }
    
    const response = await fetch(`${API_URL}/api/bot-customization`, {
      method: 'POST',
      headers,
      body: JSON.stringify(customization),
      credentials: 'include',
    });
    
    return handleResponse(response);
  },
  
  getBotCustomization: async () => {
    const token = getToken();
    const headers = {};
    let url = `${API_URL}/api/bot-customization`;
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    } else {
      // Add guest_id as query parameter if not authenticated
      const guestId = localStorage.getItem('guestId');
      if (guestId) {
        url += `?guest_id=${guestId}`;
      } else {
        return null; // No customization yet
      }
    }
    
    const response = await fetch(url, {
      headers,
      credentials: 'include',
    });
    
    if (response.status === 404) {
      return null;
    }
    
    return handleResponse(response);
  },
};

// Chat services
const chatService = {
  sendMessage: async (message, sessionId = null) => {
    const token = getToken();
    const headers = {
      'Content-Type': 'application/json',
    };
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    const payload = {
      message,
      session_id: sessionId || localStorage.getItem('sessionId') || 'default',
    };
    
    // Add guest_id if not authenticated
    if (!token) {
      const guestId = localStorage.getItem('guestId');
      if (guestId) {
        payload.guest_id = guestId;
      }
    }
    
    const response = await fetch(`${API_URL}/chat`, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
      credentials: 'include',
    });
    
    const data = await handleResponse(response);
    
    // Store session ID for future requests
    if (data.session_id) {
      localStorage.setItem('sessionId', data.session_id);
    }
    
    return data;
  },
  
  resetChat: async () => {
    const token = getToken();
    const headers = {
      'Content-Type': 'application/json',
    };
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    const payload = {
      session_id: localStorage.getItem('sessionId') || 'default',
    };
    
    // Add guest_id if not authenticated
    if (!token) {
      const guestId = localStorage.getItem('guestId');
      if (guestId) {
        payload.guest_id = guestId;
      }
    }
    
    const response = await fetch(`${API_URL}/reset_chat`, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
      credentials: 'include',
    });
    
    return handleResponse(response);
  },
};

// Export all services
export { authService, botService, chatService };