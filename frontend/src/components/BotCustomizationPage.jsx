import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import '../css/BotCustomizationPage.css';

// Bot character options (placeholder paths - you'll need actual GIF files)
const botCharacters = [
  { id: 1, name: 'Robo', src: '/src/assets/characters/robo.gif' },
  { id: 2, name: 'Pixie', src: '/src/assets/characters/pixie.png' },
  { id: 3, name: 'Buddy', src: '/bot-characters/buddy.gif' },
  { id: 4, name: 'Nova', src: '/bot-characters/nova.gif' }
];

const BotCustomizationPage = () => {
  const navigate = useNavigate();
  const [botName, setBotName] = useState('');
  const [selectedCharacter, setSelectedCharacter] = useState(null);
  const [nameError, setNameError] = useState('');

  // Handle bot name input
  const handleNameChange = (e) => {
    const value = e.target.value;
    setBotName(value);
    
    // Clear error if user is typing
    if (nameError) setNameError('');
  };

  // Handle character selection
  const handleCharacterSelect = (character) => {
    setSelectedCharacter(character);
  };

  // Handle form submission
  const handleSubmit = () => {
    // Validate bot name
    if (!botName.trim()) {
      setNameError('Please enter a name for your bot');
      return;
    }
    
    if (!selectedCharacter) {
      // If no character is selected, select the first one by default
      setSelectedCharacter(botCharacters[0]);
    }
    
    // Save customization to local storage or state management
    const botCustomization = {
      name: botName,
      characterId: selectedCharacter ? selectedCharacter.id : 1,
      characterSrc: selectedCharacter ? selectedCharacter.src : botCharacters[0].src
    };
    
    localStorage.setItem('botCustomization', JSON.stringify(botCustomization));
    
    // Navigate to chat page
    navigate('/chat');
  };

  return (
    <div className="customization-container">
      <div className="customization-card">
        <h1 className="customization-title">Customize Your Bot</h1>
        
        <div className="customization-section">
          <label htmlFor="botName" className="section-label">Give your bot a name:</label>
          <input
            type="text"
            id="botName"
            value={botName}
            onChange={handleNameChange}
            className={`name-input ${nameError ? 'error' : ''}`}
            placeholder="Enter bot name..."
            maxLength={20}
          />
          {nameError && <p className="error-message">{nameError}</p>}
        </div>
        
        <div className="customization-section">
          <p className="section-label">Choose a character:</p>
          <div className="character-grid">
            {botCharacters.map((character) => (
              <div 
                key={character.id}
                className={`character-item ${selectedCharacter && selectedCharacter.id === character.id ? 'selected' : ''}`}
                onClick={() => handleCharacterSelect(character)}
              >
                <img 
                  src={character.src} 
                  alt={character.name} 
                  className="character-image"
                />
                <p className="character-name">{character.name}</p>
              </div>
            ))}
          </div>
        </div>
        
        {/* Preview section */}
        {(botName || selectedCharacter) && (
          <div className="preview-section">
            <p className="preview-label">Preview:</p>
            <div className="preview-content">
              {selectedCharacter && (
                <img 
                  src={selectedCharacter.src} 
                  alt="Selected character" 
                  className="preview-character"
                />
              )}
              <p className="preview-name">{botName || 'Your Bot'}</p>
            </div>
          </div>
        )}
        
        <div className="button-container">
          <button className="btn back-btn" onClick={() => navigate('/')}>
            Back
          </button>
          <button className="btn next-btn" onClick={handleSubmit}>
            Continue to Chat
          </button>
        </div>
      </div>
    </div>
  );
};

export default BotCustomizationPage; 