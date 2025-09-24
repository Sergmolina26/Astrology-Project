import React, { useState } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useTranslation } from 'react-i18next';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Alert, AlertDescription } from './ui/alert';
import { Stars, Sparkles, Moon, Sun } from 'lucide-react';
import { toast } from 'sonner';

const AuthPage = () => {
  const { user, login, register } = useAuth();
  const { t } = useTranslation();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('login');

  // Form states
  const [loginForm, setLoginForm] = useState({
    email: '',
    password: ''
  });

  const [registerForm, setRegisterForm] = useState({
    name: '',
    email: '',
    password: '',
    role: 'client'
  });

  if (user) {
    return <Navigate to="/dashboard" replace />;
  }

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const result = await login(loginForm.email, loginForm.password);
    
    if (result.success) {
      toast.success('Welcome back to Celestia!');
    } else {
      const errorMessage = typeof result.error === 'string' ? result.error : 'Login failed. Please try again.';
      setError(errorMessage);
      toast.error(errorMessage);
    }
    
    setLoading(false);
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const result = await register(registerForm);
    
    if (result.success) {
      toast.success('Welcome to Celestia! Your mystical journey begins now.');
    } else {
      const errorMessage = typeof result.error === 'string' ? result.error : 'Registration failed. Please try again.';
      setError(errorMessage);
      toast.error(errorMessage);
    }
    
    setLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      {/* Floating decorative elements */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-10 animate-float">
          <Stars className="w-6 h-6 text-amber-400/30" />
        </div>
        <div className="absolute top-40 right-20 animate-float" style={{ animationDelay: '2s' }}>
          <Moon className="w-8 h-8 text-purple-400/20" />
        </div>
        <div className="absolute bottom-32 left-20 animate-float" style={{ animationDelay: '4s' }}>
          <Sparkles className="w-7 h-7 text-amber-300/25" />
        </div>
        <div className="absolute bottom-20 right-10 animate-float" style={{ animationDelay: '1s' }}>
          <Sun className="w-6 h-6 text-orange-400/30" />
        </div>
      </div>

      <div className="w-full max-w-md relative z-10">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <div className="w-16 h-16 rounded-full bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center animate-pulse-glow">
              <Stars className="w-8 h-8 text-white" />
            </div>
          </div>
          <h1 className="font-serif text-4xl font-bold text-white mb-2">
            Celestia
          </h1>
          <p className="text-slate-400 text-lg">
            Unlock the mysteries of the stars
          </p>
        </div>

        <Card className="glass-card mystical-border ornate-corner">
          <CardHeader>
            <CardTitle className="text-center text-white font-mystical text-2xl">
              ✦ Enter Your Celestial Realm ✦
            </CardTitle>
            <CardDescription className="text-center text-slate-300">
              Access your astrology and tarot portal
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
              <TabsList className="grid w-full grid-cols-2 bg-slate-800/50 border border-slate-600/30 rounded-lg p-1">
                <TabsTrigger 
                  value="login" 
                  className="data-[state=active]:bg-amber-500/20 data-[state=active]:text-amber-400 transition-all duration-200 rounded-md"
                  data-testid="login-tab"
                >
                  Sign In
                </TabsTrigger>
                <TabsTrigger 
                  value="register" 
                  className="data-[state=active]:bg-amber-500/20 data-[state=active]:text-amber-400 transition-all duration-200 rounded-md"
                  data-testid="register-tab"
                >
                  Join Us
                </TabsTrigger>
              </TabsList>

              {error && (
                <Alert className="mt-4 border-red-500/50 bg-red-500/10">
                  <AlertDescription className="text-red-400">
                    {typeof error === 'string' ? error : 'An error occurred. Please try again.'}
                  </AlertDescription>
                </Alert>
              )}

              <TabsContent value="login" className="mt-6">
                <form onSubmit={handleLogin} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="login-email" className="text-slate-200">
                      Email
                    </Label>
                    <Input
                      id="login-email"
                      type="email"
                      placeholder="Enter your email"
                      value={loginForm.email}
                      onChange={(e) => setLoginForm({ ...loginForm, email: e.target.value })}
                      className="form-input"
                      data-testid="login-email-input"
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="login-password" className="text-slate-200">
                      Password
                    </Label>
                    <Input
                      id="login-password"
                      type="password"
                      placeholder="Enter your password"
                      value={loginForm.password}
                      onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
                      className="form-input"
                      data-testid="login-password-input"
                      required
                    />
                  </div>
                  <Button
                    type="submit"
                    className="w-full btn-primary"
                    disabled={loading}
                    data-testid="login-submit-button"
                  >
                    {loading ? (
                      <div className="flex items-center space-x-2">
                        <div className="loading-spinner"></div>
                        <span>Accessing your stars...</span>
                      </div>
                    ) : (
                      'Enter Celestia'
                    )}
                  </Button>
                </form>
              </TabsContent>

              <TabsContent value="register" className="mt-6">
                <form onSubmit={handleRegister} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="register-name" className="text-slate-200">
                      Full Name
                    </Label>
                    <Input
                      id="register-name"
                      type="text"
                      placeholder="Enter your full name"
                      value={registerForm.name}
                      onChange={(e) => setRegisterForm({ ...registerForm, name: e.target.value })}
                      className="form-input"
                      data-testid="register-name-input"
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="register-email" className="text-slate-200">
                      Email
                    </Label>
                    <Input
                      id="register-email"
                      type="email"
                      placeholder="Enter your email"
                      value={registerForm.email}
                      onChange={(e) => setRegisterForm({ ...registerForm, email: e.target.value })}
                      className="form-input"
                      data-testid="register-email-input"
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="register-password" className="text-slate-200">
                      Password
                    </Label>
                    <Input
                      id="register-password"
                      type="password"
                      placeholder="Create a password"
                      value={registerForm.password}
                      onChange={(e) => setRegisterForm({ ...registerForm, password: e.target.value })}
                      className="form-input"
                      data-testid="register-password-input"
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="register-role" className="text-slate-200">
                      Account Type
                    </Label>
                    <div className="p-3 rounded-lg bg-slate-800/30 border border-slate-600/30">
                      <div className="text-sm text-slate-300">
                        Client Account - Book personalized astrology and tarot sessions
                      </div>
                    </div>
                    <input type="hidden" value="client" />
                  </div>
                  <Button
                    type="submit"
                    className="w-full btn-primary"
                    disabled={loading}
                    data-testid="register-submit-button"
                  >
                    {loading ? (
                      <div className="flex items-center space-x-2">
                        <div className="loading-spinner"></div>
                        <span>Creating your cosmic profile...</span>
                      </div>
                    ) : (
                      'Begin Your Journey'
                    )}
                  </Button>
                </form>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>

        <div className="text-center mt-6 text-sm text-slate-400">
          <p>Step into a world where the cosmos guides your path</p>
        </div>
      </div>
    </div>
  );
};

export default AuthPage;