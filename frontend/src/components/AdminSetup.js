import React, { useState } from 'react';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Alert, AlertDescription } from './ui/alert';
import { Shield, CheckCircle, AlertTriangle } from 'lucide-react';
import { toast } from 'sonner';

const AdminSetup = () => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const createAdmin = async () => {
    setLoading(true);
    try {
      const response = await axios.post('/admin/create-admin');
      setResult(response.data);
      
      if (response.data.created) {
        toast.success('Admin user created successfully!');
      } else {
        toast.info('Admin user already exists');
      }
    } catch (error) {
      console.error('Admin creation failed:', error);
      toast.error('Failed to create admin user');
      setResult({ error: error.response?.data?.detail || 'Failed to create admin' });
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 celestial-bg">
      <Card className="w-full max-w-lg glass-card mystical-border">
        <CardHeader className="text-center">
          <div className="w-16 h-16 rounded-full bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center mx-auto mb-4">
            <Shield className="w-8 h-8 text-white" />
          </div>
          <CardTitle className="text-2xl font-bold text-white">
            Celestia Admin Setup
          </CardTitle>
          <CardDescription className="text-slate-300">
            Create the main administrator account for full system access
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {!result ? (
            <>
              <div className="space-y-3 text-sm text-slate-300">
                <h3 className="font-medium text-white">Admin User Details:</h3>
                <p><strong>Email:</strong> lago.mistico11@gmail.com</p>
                <p><strong>Role:</strong> Administrator</p>
                <p><strong>Permissions:</strong> Full system access</p>
              </div>

              <Button
                onClick={createAdmin}
                className="w-full btn-primary"
                disabled={loading}
              >
                {loading ? (
                  <div className="flex items-center space-x-2">
                    <div className="loading-spinner"></div>
                    <span>Creating Admin User...</span>
                  </div>
                ) : (
                  <div className="flex items-center space-x-2">
                    <Shield className="w-4 h-4" />
                    <span>Create Admin User</span>
                  </div>
                )}
              </Button>
            </>
          ) : (
            <div className="space-y-4">
              {result.created ? (
                <Alert className="border-green-500/50 bg-green-500/10">
                  <CheckCircle className="w-4 h-4 text-green-400" />
                  <AlertDescription className="text-green-400">
                    <div className="space-y-2">
                      <p><strong>Admin user created successfully!</strong></p>
                      <div className="text-sm">
                        <p><strong>Email:</strong> {result.admin_email}</p>
                        <p><strong>Default Password:</strong> {result.default_password}</p>
                        <p className="text-green-300 mt-2">
                          ⚠️ Please save this password and change it after first login
                        </p>
                      </div>
                    </div>
                  </AlertDescription>
                </Alert>
              ) : result.error ? (
                <Alert className="border-red-500/50 bg-red-500/10">
                  <AlertTriangle className="w-4 h-4 text-red-400" />
                  <AlertDescription className="text-red-400">
                    {result.error}
                  </AlertDescription>
                </Alert>
              ) : (
                <Alert className="border-amber-500/50 bg-amber-500/10">
                  <AlertTriangle className="w-4 h-4 text-amber-400" />
                  <AlertDescription className="text-amber-400">
                    <div className="space-y-2">
                      <p><strong>Admin user already exists</strong></p>
                      <div className="text-sm">
                        <p><strong>Email:</strong> {result.admin_email}</p>
                        <p>You can login with your existing credentials.</p>
                      </div>
                    </div>
                  </AlertDescription>
                </Alert>
              )}

              <Button
                onClick={() => window.location.href = '/auth'}
                className="w-full btn-primary"
              >
                Go to Login
              </Button>
            </div>
          )}

          <div className="text-center">
            <a
              href="/auth"
              className="text-sm text-slate-400 hover:text-amber-400 transition-colors"
            >
              Already have an admin account? Login here
            </a>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default AdminSetup;