'use client';

import { useState } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSearch, faBell } from '@fortawesome/free-solid-svg-icons';

const Header = ({ onSearch }) => {
  const [ticker, setTicker] = useState('');

  const handleSearch = () => {
    if (ticker.trim()) {
      onSearch(ticker.trim());
    }
  };

  return (
    <header className="flex items-center justify-between p-6 bg-background border-b border-border">
      <div className="flex items-center">
        <div className="relative">
          <input 
            type="text" 
            placeholder="Search for a stock... (e.g. RELIANCE.NS)" 
            className="bg-card-alt border border-border rounded-lg pl-4 pr-16 py-2 w-96 text-text-primary focus:outline-none focus:ring-2 focus:ring-accent"
            value={ticker}
            onChange={(e) => setTicker(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          />
          <button 
            onClick={handleSearch}
            className="absolute right-2 top-1/2 -translate-y-1/2 bg-accent hover:bg-accent-hover text-white font-bold py-1 px-3 rounded"
          >
            <FontAwesomeIcon icon={faSearch} />
          </button>
        </div>
      </div>
      <div className="flex items-center">
        <FontAwesomeIcon icon={faBell} className="w-6 h-6 text-text-secondary mr-6" />
        <div className="w-10 h-10 bg-accent rounded-full"></div>
      </div>
    </header>
  );
};

export default Header;
