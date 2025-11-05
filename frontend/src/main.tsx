// Entry Point with Toast Provider
import React from 'react';
import ReactDOM from 'react-dom/client';
import { Toaster } from 'sonner';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
    <Toaster
      position="top-right"
      richColors
      expand={false}
      visibleToasts={3}
      closeButton
    />
  </React.StrictMode>
);
