// Minimalist Professional Auth App
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from '@/hooks/useAuth';
import { LoginPage } from '@/pages/LoginPage';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/*" element={<LoginPage />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
