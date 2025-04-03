// src/components/ChatInterface.jsx
import React, { useState, useEffect, useRef } from 'react';
import '../css/style.css';

const ChatInterface = () => {
  const [message, setMessage] = useState('');
  const [isWaiting, setIsWaiting] = useState(false);
  const [messageHistory, setMessageHistory] = useState([]);
  const [sessionId, setSessionId] = useState('');
  const chatBoxRef = useRef(null);
  const inputRef = useRef(null);

  const [botCustomization, setBotCustomization] = useState({
    name: 'Bot',
    characterSrc: '/default-avatar.gif' // Provide a default image path
  });
  
  // Add useEffect to load the customization from localStorage
  useEffect(() => {
    try {
      const savedCustomization = localStorage.getItem('botCustomization');
      if (savedCustomization) {
        setBotCustomization(JSON.parse(savedCustomization));
      }
    } catch (error) {
      console.error('Error loading bot customization:', error);
    }
  }, []);

  useEffect(() => {
    // Initialize session ID on load
    const storedSessionId = localStorage.getItem('chatSessionId') || generateSessionId();
    setSessionId(storedSessionId);
    localStorage.setItem('chatSessionId', storedSessionId);
    
    // Focus the input field
    if (inputRef.current) inputRef.current.focus();
  }, []);

  const generateSessionId = () => {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substring(2, 9);
  };

  const formatTimestamp = () => {
    const now = new Date();
    return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const sanitizeInput = (input) => {
    const div = document.createElement('div');
    div.textContent = input;
    return div.innerHTML;
  };

  const addMessage = (messageText, sender, isError = false) => {
    const newMessage = {
      id: Date.now(),
      sender,
      message: messageText,
      timestamp: new Date().toISOString(),
      isError
    };
    
    setMessageHistory(prevHistory => [...prevHistory, newMessage]);
    
    // Scroll to bottom
    setTimeout(() => {
      if (chatBoxRef.current) {
        chatBoxRef.current.scrollTop = chatBoxRef.current.scrollHeight;
      }
    }, 100);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      handleSendMessage();
    }
  };

  const handleSendMessage = async () => {
    if (!message.trim() || isWaiting) return;

    // Clear input and set waiting state
    setMessage('');
    setIsWaiting(true);
    
    // Add user message
    addMessage(sanitizeInput(message), 'user');
    
    try {
      // Send request to backend
      const response = await fetch("http://localhost:5000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: message,
          session_id: sessionId
        })
      });
      
      if (!response.ok) {
        throw new Error(`Server responded with status: ${response.status}`);
      }
      
      const data = await response.json();
      
      // Add bot response
      addMessage(data.reply, 'bot');
      
    } catch (error) {
      console.error('Error:', error);
      
      // Show error message
      addMessage(
        'Sorry, I encountered an error while processing your request. Please try again later.',
        'bot',
        true
      );
    } finally {
      setIsWaiting(false);
      
      // Focus input field
      if (inputRef.current) inputRef.current.focus();
    }
  };

  const handleResetChat = async () => {
    try {
      const response = await fetch("http://localhost:5000/reset_chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId
        })
      });
      
      if (!response.ok) {
        throw new Error(`Server responded with status: ${response.status}`);
      }
      
      // Clear message history
      setMessageHistory([]);
      
      // Add system message
      addMessage('Chat has been reset. How can I help you today?', 'bot');
      
    } catch (error) {
      console.error('Error resetting chat:', error);
      addMessage('Failed to reset the chat. Please try again.', 'bot', true);
    }
  };

  const handleExportChat = () => {
    if (messageHistory.length === 0) {
      alert('No messages to export');
      return;
    }
    
    let chatText = '=== Chat Export ===\n\n';
    messageHistory.forEach(item => {
      const time = new Date(item.timestamp).toLocaleTimeString();
      const sender = item.sender === 'user' ? 'You' : 'Bot';
      chatText += `[${time}] ${sender}: ${item.message}\n\n`;
    });
    
    const blob = new Blob([chatText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `chat-export-${new Date().toISOString().slice(0,10)}.txt`;
    a.click();
    
    URL.revokeObjectURL(url);
  };

  function ChatComponent() {
    const [botCustomization, setBotCustomization] = useState({
      name: 'Bot',
      characterSrc: '/default-avatar.gif'
    });
    
    useEffect(() => {
      // Load the bot customization from localStorage
      const savedCustomization = localStorage.getItem('botCustomization');
      if (savedCustomization) {
        setBotCustomization(JSON.parse(savedCustomization));
      }
    }, []);
  }

  return (
    <div className="chat-container">
      <div className="chat-header">
        {/* Use the custom bot name here if you want */}
        <h1>{botCustomization.name}</h1>
        <div className="chat-controls">
          <button onClick={handleResetChat} id="reset-chat">Reset Chat</button>
          <button onClick={handleExportChat} id="export-chat">Export Chat</button>
        </div>
      </div>
     
      <div className="chat-box" id="chat-box" ref={chatBoxRef}>
        {messageHistory.length === 0 ? (
          <div className="welcome-message">
            <p>Hello! How can I help you today?</p>
          </div>
        ) : (
          messageHistory.map((msg) => (
            msg.sender === 'user' ? (
              // User message stays the same
              <div key={msg.id} className={`message user-message ${msg.isError ? 'error' : ''}`}>
                <div className="message-content">
                  <strong>You: </strong>
                  <span dangerouslySetInnerHTML={{ __html: msg.message }}></span>
                </div>
                <span className="timestamp">{new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
              </div>
            ) : (
              // Bot message gets the new structure
              <div key={msg.id} className="bot-message-container">
                <img 
                  src={botCustomization.characterSrc} 
                  alt={`${botCustomization.name} avatar`} 
                  className="bot-avatar"
                />
                <div className="bot-message-content">
                  <div className={`message bot-message ${msg.isError ? 'error' : ''}`}>
                    <div className="message-content">
                      <strong>{botCustomization.name}: </strong>
                      <span dangerouslySetInnerHTML={{ __html: msg.message }}></span>
                    </div>
                    <span className="timestamp">{new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                  </div>
                </div>
              </div>
            )
          ))
        )}
        {isWaiting && (
          <div className="bot-message-container">
            <img 
              src={botCustomization.characterSrc} 
              alt={`${botCustomization.name} avatar`} 
              className="bot-avatar"
            />
            <div className="bot-message-content">
              <div className="message bot-message typing-indicator">
                <div className="message-content">
                  <strong>{botCustomization.name}: </strong>
                  <em>Typing...</em>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
     
      <div className="chat-input">
        <input
          type="text"
          id="user-input"
          ref={inputRef}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type your message here..."
          disabled={isWaiting}
        />
        <button 
          className="send-button"
          onClick={handleSendMessage} 
          disabled={isWaiting || !message.trim()}
        >
          Send
        </button>
      </div>
    </div>
  );
}

export default ChatInterface;