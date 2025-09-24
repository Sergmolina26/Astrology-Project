import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Alert, AlertDescription } from './ui/alert';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { 
  Users, 
  Calendar,
  DollarSign,
  TrendingUp,
  Settings,
  UserCheck,
  Clock,
  CheckCircle,
  XCircle,
  Trash2,
  Mail,
  Shield
} from 'lucide-react';
import { toast } from 'sonner';

const AdminDashboard = () => {
  const queryClient = useQueryClient();
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState('overview');

  // Fetch dashboard stats
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['admin-stats'],
    queryFn: async () => {
      const response = await axios.get('/admin/dashboard-stats');
      return response.data;
    }
  });

  // Fetch all users
  const { data: users = [], isLoading: usersLoading } = useQuery({
    queryKey: ['admin-users'],
    queryFn: async () => {
      const response = await axios.get('/admin/users');
      return response.data;
    }
  });

  // Fetch all sessions
  const { data: sessions = [], isLoading: sessionsLoading } = useQuery({
    queryKey: ['admin-sessions'],
    queryFn: async () => {
      const response = await axios.get('/admin/sessions');
      return response.data;
    }
  });

  // Fetch all payments
  const { data: payments = [], isLoading: paymentsLoading } = useQuery({
    queryKey: ['admin-payments'],
    queryFn: async () => {
      const response = await axios.get('/admin/payments');
      return response.data;
    }
  });

  // Update session status mutation
  const updateSessionStatusMutation = useMutation({
    mutationFn: async ({ sessionId, status }) => {
      const response = await axios.put(`/admin/sessions/${sessionId}/status?status=${status}`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['admin-sessions']);
      queryClient.invalidateQueries(['admin-stats']);
      toast.success('Session status updated successfully');
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Failed to update session');
    }
  });

  // Delete session mutation
  const deleteSessionMutation = useMutation({
    mutationFn: async (sessionId) => {
      const response = await axios.delete(`/admin/sessions/${sessionId}`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['admin-sessions']);
      queryClient.invalidateQueries(['admin-stats']);
      toast.success('Session deleted successfully');
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Failed to delete session');
    }
  });

  const handleStatusUpdate = (sessionId, newStatus) => {
    updateSessionStatusMutation.mutate({ sessionId, status: newStatus });
  };

  const handleDeleteSession = (sessionId) => {
    if (window.confirm('Are you sure you want to delete this session?')) {
      deleteSessionMutation.mutate(sessionId);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      'pending_payment': 'bg-yellow-500/20 text-yellow-400',
      'confirmed': 'bg-green-500/20 text-green-400',
      'completed': 'bg-blue-500/20 text-blue-400',
      'cancelled': 'bg-red-500/20 text-red-400',
      'declined': 'bg-gray-500/20 text-gray-400'
    };
    return colors[status] || 'bg-gray-500/20 text-gray-400';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center space-y-4">
        <div className="flex justify-center items-center space-x-3">
          <div className="w-12 h-12 rounded-full bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center">
            <Shield className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-white font-mystical">
            {t('admin.dashboard')}
          </h1>
        </div>
        <p className="text-slate-300 max-w-2xl mx-auto">
          {t('admin.manageBusiness')}
        </p>
      </div>

      {/* Overview Stats */}
      {!statsLoading && stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card className="glass-card mystical-border">
            <CardContent className="pt-6">
              <div className="flex items-center space-x-4">
                <div className="w-12 h-12 rounded-full bg-blue-500/20 flex items-center justify-center">
                  <Users className="w-6 h-6 text-blue-400" />
                </div>
                <div>
                  <p className="text-sm text-slate-400">Total Clients</p>
                  <p className="text-2xl font-bold text-white">{stats.total_clients}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="glass-card mystical-border">
            <CardContent className="pt-6">
              <div className="flex items-center space-x-4">
                <div className="w-12 h-12 rounded-full bg-green-500/20 flex items-center justify-center">
                  <Calendar className="w-6 h-6 text-green-400" />
                </div>
                <div>
                  <p className="text-sm text-slate-400">Total Sessions</p>
                  <p className="text-2xl font-bold text-white">{stats.total_sessions}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="glass-card mystical-border">
            <CardContent className="pt-6">
              <div className="flex items-center space-x-4">
                <div className="w-12 h-12 rounded-full bg-amber-500/20 flex items-center justify-center">
                  <DollarSign className="w-6 h-6 text-amber-400" />
                </div>
                <div>
                  <p className="text-sm text-slate-400">Revenue</p>
                  <p className="text-2xl font-bold text-white">${stats.total_revenue.toFixed(2)}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="glass-card mystical-border">
            <CardContent className="pt-6">
              <div className="flex items-center space-x-4">
                <div className="w-12 h-12 rounded-full bg-purple-500/20 flex items-center justify-center">
                  <TrendingUp className="w-6 h-6 text-purple-400" />
                </div>
                <div>
                  <p className="text-sm text-slate-400">Conversion Rate</p>
                  <p className="text-2xl font-bold text-white">{stats.conversion_rate.toFixed(1)}%</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-4 bg-slate-800/50 border border-slate-600/30 rounded-lg p-1">
          <TabsTrigger 
            value="overview" 
            className="data-[state=active]:bg-amber-500/20 data-[state=active]:text-amber-400"
          >
            <TrendingUp className="w-4 h-4 mr-2" />
            Overview
          </TabsTrigger>
          <TabsTrigger 
            value="sessions" 
            className="data-[state=active]:bg-amber-500/20 data-[state=active]:text-amber-400"
          >
            <Calendar className="w-4 h-4 mr-2" />
            Sessions
          </TabsTrigger>
          <TabsTrigger 
            value="users" 
            className="data-[state=active]:bg-amber-500/20 data-[state=active]:text-amber-400"
          >
            <Users className="w-4 h-4 mr-2" />
            Users
          </TabsTrigger>
          <TabsTrigger 
            value="payments" 
            className="data-[state=active]:bg-amber-500/20 data-[state=active]:text-amber-400"
          >
            <DollarSign className="w-4 h-4 mr-2" />
            Payments
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="mt-6">
          <div className="grid gap-6">
            <Card className="glass-card mystical-border">
              <CardHeader>
                <CardTitle className="text-white">Recent Activity</CardTitle>
                <CardDescription className="text-slate-300">
                  Latest sessions and bookings
                </CardDescription>
              </CardHeader>
              <CardContent>
                {sessionsLoading ? (
                  <div className="text-center py-4">
                    <div className="loading-spinner mx-auto mb-2"></div>
                    <p className="text-slate-400">Loading recent activity...</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {sessions.slice(0, 5).map((session) => (
                      <div key={session.id} className="flex items-center justify-between p-3 bg-slate-800/30 rounded-lg">
                        <div className="flex items-center space-x-3">
                          <Calendar className="w-4 h-4 text-amber-400" />
                          <div>
                            <p className="text-white font-medium">{session.client_name}</p>
                            <p className="text-sm text-slate-400">{session.service_type}</p>
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          <Badge className={getStatusColor(session.status)}>
                            {session.status}
                          </Badge>
                          <span className="text-sm text-slate-400">${session.amount}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Sessions Tab */}
        <TabsContent value="sessions" className="mt-6">
          <Card className="glass-card mystical-border">
            <CardHeader>
              <CardTitle className="text-white">Session Management</CardTitle>
              <CardDescription className="text-slate-300">
                Manage all client sessions and bookings
              </CardDescription>
            </CardHeader>
            <CardContent>
              {sessionsLoading ? (
                <div className="text-center py-8">
                  <div className="loading-spinner mx-auto mb-4"></div>
                  <p className="text-slate-400">Loading sessions...</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {sessions.map((session) => (
                    <div key={session.id} className="p-4 bg-slate-800/30 rounded-lg border border-slate-600/30">
                      <div className="flex items-center justify-between">
                        <div className="space-y-2">
                          <div className="flex items-center space-x-4">
                            <h3 className="font-medium text-white">{session.client_name}</h3>
                            <Badge className={getStatusColor(session.status)}>
                              {session.status}
                            </Badge>
                          </div>
                          <div className="flex items-center space-x-4 text-sm text-slate-400">
                            <span className="flex items-center">
                              <Mail className="w-3 h-3 mr-1" />
                              {session.client_email}
                            </span>
                            <span className="flex items-center">
                              <Calendar className="w-3 h-3 mr-1" />
                              {new Date(session.start_at).toLocaleDateString()}
                            </span>
                            <span className="flex items-center">
                              <Clock className="w-3 h-3 mr-1" />
                              {new Date(session.start_at).toLocaleTimeString()}
                            </span>
                            <span className="flex items-center">
                              <DollarSign className="w-3 h-3 mr-1" />
                              ${session.amount}
                            </span>
                          </div>
                          <p className="text-sm text-slate-300">{session.service_type}</p>
                          {session.client_message && (
                            <p className="text-sm text-slate-400 italic">"{session.client_message}"</p>
                          )}
                        </div>
                        <div className="flex items-center space-x-2">
                          <Select
                            value={session.status}
                            onValueChange={(newStatus) => handleStatusUpdate(session.id, newStatus)}
                          >
                            <SelectTrigger className="w-40 form-input">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="pending_payment">Pending Payment</SelectItem>
                              <SelectItem value="confirmed">Confirmed</SelectItem>
                              <SelectItem value="completed">Completed</SelectItem>
                              <SelectItem value="cancelled">Cancelled</SelectItem>
                              <SelectItem value="declined">Declined</SelectItem>
                            </SelectContent>
                          </Select>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDeleteSession(session.id)}
                            className="text-red-400 hover:text-red-300"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Users Tab */}
        <TabsContent value="users" className="mt-6">
          <Card className="glass-card mystical-border">
            <CardHeader>
              <CardTitle className="text-white">User Management</CardTitle>
              <CardDescription className="text-slate-300">
                View and manage all registered users
              </CardDescription>
            </CardHeader>
            <CardContent>
              {usersLoading ? (
                <div className="text-center py-8">
                  <div className="loading-spinner mx-auto mb-4"></div>
                  <p className="text-slate-400">Loading users...</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {users.map((user) => (
                    <div key={user.id} className="p-4 bg-slate-800/30 rounded-lg border border-slate-600/30">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-4">
                          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center">
                            <UserCheck className="w-5 h-5 text-white" />
                          </div>
                          <div>
                            <h3 className="font-medium text-white">{user.name}</h3>
                            <p className="text-sm text-slate-400">{user.email}</p>
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          <Badge variant={user.role === 'admin' ? 'default' : 'secondary'}>
                            {user.role}
                          </Badge>
                          <span className="text-xs text-slate-400">
                            Joined: {new Date(user.created_at).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Payments Tab */}
        <TabsContent value="payments" className="mt-6">
          <Card className="glass-card mystical-border">
            <CardHeader>
              <CardTitle className="text-white">Payment Transactions</CardTitle>
              <CardDescription className="text-slate-300">
                View all payment transactions and revenue
              </CardDescription>
            </CardHeader>
            <CardContent>
              {paymentsLoading ? (
                <div className="text-center py-8">
                  <div className="loading-spinner mx-auto mb-4"></div>
                  <p className="text-slate-400">Loading payments...</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {payments.map((payment) => (
                    <div key={payment.id} className="p-4 bg-slate-800/30 rounded-lg border border-slate-600/30">
                      <div className="flex items-center justify-between">
                        <div className="space-y-2">
                          <div className="flex items-center space-x-4">
                            <h3 className="font-medium text-white">${payment.amount}</h3>
                            <Badge className={payment.payment_status === 'paid' ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'}>
                              {payment.payment_status}
                            </Badge>
                          </div>
                          <div className="flex items-center space-x-4 text-sm text-slate-400">
                            <span className="flex items-center">
                              <Mail className="w-3 h-3 mr-1" />
                              {payment.user_email}
                            </span>
                            <span className="flex items-center">
                              <Calendar className="w-3 h-3 mr-1" />
                              {new Date(payment.created_at).toLocaleDateString()}
                            </span>
                            <span>{payment.service_type}</span>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-sm text-slate-400">Currency: {payment.currency}</p>
                          <p className="text-xs text-slate-500">ID: {payment.payment_id.substring(0, 8)}...</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AdminDashboard;