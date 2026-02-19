import React from 'react';
import { Routes, Route, Link, Navigate, useLocation } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import ImageUpload from './components/ImageUpload';
import BookList from './components/BookList';
import ConditionAssessment from './components/ConditionAssessment';
import Login from './components/Login';
import Register from './components/Register';
import { useAuth } from './context/AuthContext';

function App() {
  const { currentUser, logout, loading } = useAuth();

  if (loading) {
    return <div className="flex items-center justify-center min-h-screen">Laden...</div>;
  }

  return (
    <>
      <Toaster position="top-right" />
      <Routes>
        <Route path="/login" element={!currentUser ? <AuthPage /> : <Navigate to="/" />} />
        <Route path="/register" element={!currentUser ? <AuthPage /> : <Navigate to="/" />} />
        <Route path="/*" element={currentUser ? <MainApp handleLogout={logout} currentUser={currentUser} /> : <Navigate to="/login" />} />
      </Routes>
    </>
  );
}

const AuthPage = () => {
  const location = useLocation();
  const isLoginPage = location.pathname === '/login';

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          {isLoginPage ? (
            <div>
              <Login />
              <p className="mt-4 text-center text-sm text-gray-600">
                Noch keinen Account? <Link to="/register" className="font-medium text-blue-600 hover:text-blue-500">Registrieren</Link>
              </p>
            </div>
          ) : (
            <div>
              <Register />
              <p className="mt-4 text-center text-sm text-gray-600">
                Bereits registriert? <Link to="/login" className="font-medium text-blue-600 hover:text-blue-500">Login</Link>
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const MainApp = ({ handleLogout, currentUser }) => {
  const location = useLocation();
  const [isMenuOpen, setIsMenuOpen] = React.useState(false);

  const navLinkClasses = (path) =>
    `block px-4 py-3 rounded-xl text-base font-medium transition-all duration-200 ${
      location.pathname === path
        ? 'bg-blue-50 text-blue-700'
        : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
    }`;

  const desktopNavLinkClasses = (path) =>
    `inline-flex items-center px-1 pt-1 text-sm font-medium border-b-2 transition-all duration-200 ${
      location.pathname === path
        ? 'border-blue-600 text-gray-900'
        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
    }`;

  return (
    <div className="min-h-screen bg-[#F3F4F6]">
      <nav className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-200/60 shadow-sm supports-[backdrop-filter]:bg-white/60">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex">
              <div className="flex-shrink-0 flex items-center gap-3">
                <div className="bg-blue-600 text-white p-1.5 rounded-lg shadow-lg shadow-blue-600/20">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path d="M9 4.804A7.968 7.968 0 005.5 4c-1.255 0-2.443.29-3.5.804v10A7.969 7.969 0 015.5 14c1.669 0 3.218.51 4.5 1.385A7.962 7.962 0 0114.5 14c1.255 0 2.443.29 3.5.804v-10A7.968 7.968 0 0014.5 4c-1.255 0-2.443.29-3.5.804V12a1 1 0 11-2 0V4.804z" />
                  </svg>
                </div>
                <h1 className="text-lg font-bold text-gray-900 tracking-tight">BookFlow</h1>
              </div>
              <div className="hidden sm:ml-8 sm:flex sm:space-x-8">
                <Link to="/" className={desktopNavLinkClasses('/')}>Bibliothek</Link>
                <Link to="/upload" className={desktopNavLinkClasses('/upload')}>Upload</Link>
              </div>
            </div>
            
            {/* Desktop User Menu */}
            <div className="hidden sm:flex sm:items-center sm:space-x-4">
              <div className="flex flex-col items-end mr-2">
                <span className="text-xs text-gray-500 font-medium">Angemeldet als</span>
                <span className="text-sm text-gray-900 font-semibold truncate max-w-[150px]">{currentUser.email}</span>
              </div>
              <button 
                onClick={handleLogout} 
                className="bg-white border border-gray-200 text-gray-700 hover:bg-gray-50 hover:text-gray-900 hover:border-gray-300 px-4 py-2 rounded-xl text-sm font-medium transition-all shadow-sm"
              >
                Logout
              </button>
            </div>

            {/* Mobile menu button */}
            <div className="-mr-2 flex items-center sm:hidden">
              <button
                onClick={() => setIsMenuOpen(!isMenuOpen)}
                className="inline-flex items-center justify-center p-2 rounded-xl text-gray-400 hover:text-gray-500 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500 transition-colors"
              >
                <span className="sr-only">Menü öffnen</span>
                {!isMenuOpen ? (
                  <svg className="block h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
                  </svg>
                ) : (
                  <svg className="block h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Mobile menu */}
        <div className={`sm:hidden bg-white/95 backdrop-blur-xl border-b border-gray-200 overflow-hidden transition-all duration-300 ease-in-out ${isMenuOpen ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'}`}>
          <div className="pt-4 pb-4 space-y-2 px-4">
            <Link 
              to="/" 
              className={navLinkClasses('/')}
              onClick={() => setIsMenuOpen(false)}
            >
              📚 Bibliothek
            </Link>
            <Link 
              to="/upload" 
              className={navLinkClasses('/upload')}
              onClick={() => setIsMenuOpen(false)}
            >
              📤 Upload
            </Link>
          </div>
          <div className="pt-4 pb-6 border-t border-gray-100 bg-gray-50/50 px-4">
            <div className="flex items-center mb-4">
              <div className="flex-shrink-0">
                <div className="h-10 w-10 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center font-bold text-lg ring-4 ring-white shadow-sm">
                  {currentUser.email[0].toUpperCase()}
                </div>
              </div>
              <div className="ml-3 overflow-hidden">
                <div className="text-base font-bold text-gray-900 truncate">{currentUser.email}</div>
                <div className="text-xs text-gray-500">Benutzerkonto</div>
              </div>
            </div>
            <button
              onClick={() => {
                handleLogout();
                setIsMenuOpen(false);
              }}
              className="block w-full text-center px-4 py-3 rounded-xl text-sm font-semibold text-red-600 bg-red-50 hover:bg-red-100 transition-colors"
            >
              Abmelden
            </button>
          </div>
        </div>
      </nav>
      <main className="max-w-7xl mx-auto py-8 sm:px-6 lg:px-8">
        <div className="px-4 sm:px-0">
          <Routes>
            <Route path="/" element={<BookList />} />
            <Route path="/upload" element={<ImageUpload />} />
            <Route path="/condition" element={<ConditionAssessment />} />
          </Routes>
        </div>
      </main>
    </div>
  );
};

export default App;