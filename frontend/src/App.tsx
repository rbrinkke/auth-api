// Single Page Auth Application
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '@/hooks/useAuth';
import { AuthPage } from '@/pages/AuthPage';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AuthPage />
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
