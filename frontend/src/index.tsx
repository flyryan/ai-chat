import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

// Debug logging
console.log('Backend URL:', process.env.REACT_APP_API_URL);
console.log('WebSocket URL:', process.env.REACT_APP_WS_URL);

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);