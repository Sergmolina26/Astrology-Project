import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button } from './ui/button';
import { 
  User, 
  LogOut, 
  Home, 
  Calendar, 
  Sparkles, 
  Stars 
} from 'lucide-react';

const Navigation = () => {
  const { user, logout } = useAuth();
  const location = useLocation();

  if (!user) return null;

  const isActive = (path) => location.pathname === path;

  return (
    <nav className="glass border-b border-slate-700/50">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo - now clickable to go home */}
          <Link to="/" className="flex items-center space-x-2 hover:opacity-80 transition-opacity">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center">
              <Stars className="w-5 h-5 text-white" />
            </div>
            <span className="font-serif text-xl font-semibold text-amber-400">
              Celestia
            </span>
          </Link>

          {/* Navigation Links */}
          <div className="hidden md:flex items-center space-x-1">
            <Link
              to="/dashboard"
              className={`nav-link ${isActive('/dashboard') ? 'active' : ''}`}
              data-testid="nav-dashboard"
            >
              <Home className="w-4 h-4 inline mr-2" />
              Dashboard
            </Link>
            <Link
              to="/astrology"
              className={`nav-link ${isActive('/astrology') ? 'active' : ''}`}
              data-testid="nav-astrology"
            >
              <Sparkles className="w-4 h-4 inline mr-2" />
              Astrology
            </Link>
            <Link
              to="/tarot"
              className={`nav-link ${isActive('/tarot') ? 'active' : ''}`}
              data-testid="nav-tarot"
            >
              <Calendar className="w-4 h-4 inline mr-2" />
              Book Reading
            </Link>
            <Link
              to="/sessions"
              className={`nav-link ${isActive('/sessions') ? 'active' : ''}`}
              data-testid="nav-sessions"
            >
              <Calendar className="w-4 h-4 inline mr-2" />
              Sessions
            </Link>
          </div>

          {/* User Menu */}
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <User className="w-5 h-5 text-slate-400" />
              <span className="text-sm font-medium text-slate-200">
                {user.name}
              </span>
              <span className="px-2 py-1 text-xs bg-amber-500/20 text-amber-400 rounded-full">
                {user.role}
              </span>
            </div>
            <Button
              onClick={logout}
              variant="ghost"
              size="sm"
              className="text-slate-400 hover:text-amber-400"
              data-testid="logout-button"
            >
              <LogOut className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navigation;