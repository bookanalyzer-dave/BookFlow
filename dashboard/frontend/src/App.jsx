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
    `block px-3 py-2 rounded-md text-base font-medium ${
      location.pathname === path
        ? 'bg-gray-900 text-white'
        : 'text-gray-300 hover:bg-gray-700 hover:text-white'
    }`;

  const desktopNavLinkClasses = (path) =>
    `inline-flex items-center px-1 pt-1 text-sm font-medium ${
      location.pathname === path
        ? 'text-gray-900 border-b-2 border-blue-500'
        : 'text-gray-500 hover:text-gray-700'
    }`;

  return (
    <div className="min-h-screen bg-gray-100">
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex">
              <div className="flex-shrink-0 flex items-center">
                <h1 className="text-xl font-bold text-gray-900">📚 Book Manager</h1>
              </div>
              <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
                <Link to="/" className={desktopNavLinkClasses('/')}>📖 Bücher</Link>
                <Link to="/upload" className={desktopNavLinkClasses('/upload')}>📤 Upload</Link>
              </div>
            </div>
            
            {/* Desktop User Menu */}
            <div className="hidden sm:flex sm:items-center sm:space-x-4">
              <span className="text-sm text-gray-700 truncate max-w-[150px]">{currentUser.email}</span>
              <button onClick={handleLogout} className="bg-gray-100 hover:bg-gray-200 text-gray-800 px-3 py-2 rounded-md text-sm font-medium">
                Logout
              </button>
            </div>

            {/* Mobile menu button */}
            <div className="-mr-2 flex items-center sm:hidden">
              <button
                onClick={() => setIsMenuOpen(!isMenuOpen)}
                className="inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500"
              >
                <span className="sr-only">Menü öffnen</span>
                {/* Icon when menu is closed */}
                {!isMenuOpen ? (
                  <svg className="block h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
                  </svg>
                ) : (
                  /* Icon when menu is open */
                  <svg className="block h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Mobile menu, show/hide based on menu state */}
        {isMenuOpen && (
          <div className="sm:hidden bg-white border-t border-gray-200">
            <div className="pt-2 pb-3 space-y-1 px-2">
              <Link 
                to="/" 
                className={navLinkClasses('/')}
                onClick={() => setIsMenuOpen(false)}
              >
                📖 Bücher
              </Link>
              <Link 
                to="/upload" 
                className={navLinkClasses('/upload')}
                onClick={() => setIsMenuOpen(false)}
              >
                📤 Upload
              </Link>
            </div>
            <div className="pt-4 pb-4 border-t border-gray-200">
              <div className="flex items-center px-4">
                <div className="flex-shrink-0">
                  <div className="h-8 w-8 rounded-full bg-blue-500 flex items-center justify-center text-white font-bold">
                    {currentUser.email[0].toUpperCase()}
                  </div>
                </div>
                <div className="ml-3">
                  <div className="text-base font-medium text-gray-800">{currentUser.email}</div>
                </div>
              </div>
              <div className="mt-3 px-2 space-y-1">
                <button
                  onClick={() => {
                    handleLogout();
                    setIsMenuOpen(false);
                  }}
                  className="block w-full text-left px-3 py-2 rounded-md text-base font-medium text-gray-500 hover:text-gray-800 hover:bg-gray-100"
                >
                  Abmelden
                </button>
              </div>
            </div>
          </div>
        )}
      </nav>
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
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