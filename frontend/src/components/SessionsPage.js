import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Badge } from './ui/badge';
import { Calendar } from './ui/calendar';
import { 
  Calendar as CalendarIcon, 
  Clock,
  Plus, 
  Users,
  MapPin,
  CheckCircle,
  XCircle,
  AlertCircle,
  Eye
} from 'lucide-react';
import { toast } from 'sonner';
import { format, addDays, startOfMonth, endOfMonth, eachDayOfInterval, isSameDay } from 'date-fns';

const SessionsPage = () => {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [activeTab, setActiveTab] = useState('calendar');
  const [showCreateForm, setShowCreateForm] = useState(false);

  // Form state for creating sessions
  const [sessionForm, setSessionForm] = useState({
    client_id: '',
    service_type: '',
    start_at: '',
    end_at: ''
  });

  // Fetch sessions
  const { data: sessions = [], isLoading: sessionsLoading } = useQuery({
    queryKey: ['sessions'],
    queryFn: () => axios.get('/sessions').then(res => res.data)
  });

  // Create session mutation
  const createSessionMutation = useMutation({
    mutationFn: (data) => axios.post('/sessions', data),
    onSuccess: () => {
      toast.success('Session created successfully!');
      queryClient.invalidateQueries(['sessions']);
      setShowCreateForm(false);
      setSessionForm({
        client_id: '',
        service_type: '',
        start_at: '',
        end_at: ''
      });
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Failed to create session');
    }
  });

  const handleCreateSession = (e) => {
    e.preventDefault();
    
    const sessionData = {
      ...sessionForm,
      start_at: new Date(sessionForm.start_at),
      end_at: new Date(sessionForm.end_at)
    };
    
    createSessionMutation.mutate(sessionData);
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-emerald-400" />;
      case 'canceled':
        return <XCircle className="w-4 h-4 text-red-400" />;
      case 'scheduled':
        return <AlertCircle className="w-4 h-4 text-amber-400" />;
      default:
        return <Clock className="w-4 h-4 text-slate-400" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
      case 'canceled':
        return 'bg-red-500/20 text-red-400 border-red-500/30';
      case 'scheduled':
        return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
      default:
        return 'bg-slate-500/20 text-slate-400 border-slate-500/30';
    }
  };

  // Get sessions for selected date
  const sessionsForDate = sessions.filter(session => 
    isSameDay(new Date(session.start_at), selectedDate)
  );

  // Get upcoming sessions
  const upcomingSessions = sessions
    .filter(session => new Date(session.start_at) > new Date() && session.status === 'scheduled')
    .sort((a, b) => new Date(a.start_at) - new Date(b.start_at))
    .slice(0, 10);

  // Get all sessions sorted by date
  const allSessions = [...sessions].sort((a, b) => new Date(b.start_at) - new Date(a.start_at));

  // Service types
  const serviceTypes = [
    'Astrology Reading - 60min',
    'Tarot Reading - 30min',
    'Birth Chart + Tarot - 90min',
    'Follow-up Session - 30min',
    'Relationship Reading - 45min',
    'Career Guidance - 60min'
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="font-serif text-3xl font-bold text-white mb-4 flex items-center">
            <CalendarIcon className="w-8 h-8 mr-3 text-blue-400" />
            Sessions
          </h1>
          <p className="text-slate-400">
            {user?.role === 'reader' 
              ? 'Manage your client sessions and appointments'
              : 'View your scheduled readings and session history'
            }
          </p>
        </div>
        
        {user?.role === 'reader' && (
          <Button 
            onClick={() => setShowCreateForm(!showCreateForm)}
            className="btn-primary"
            data-testid="create-session-button"
          >
            <Plus className="w-4 h-4 mr-2" />
            New Session
          </Button>
        )}
      </div>

      {/* Create Session Form */}
      {showCreateForm && user?.role === 'reader' && (
        <Card className="glass-card">
          <CardHeader>
            <CardTitle className="text-white font-serif">Create New Session</CardTitle>
            <CardDescription className="text-slate-400">
              Schedule a session with your client
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreateSession} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="client_id" className="text-slate-200">
                    Client ID *
                  </Label>
                  <Input
                    id="client_id"
                    type="text"
                    placeholder="Enter client ID"
                    value={sessionForm.client_id}
                    onChange={(e) => setSessionForm({ ...sessionForm, client_id: e.target.value })}
                    className="form-input"
                    data-testid="client-id-input"
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="service_type" className="text-slate-200">
                    Service Type *
                  </Label>
                  <Select
                    value={sessionForm.service_type}
                    onValueChange={(value) => setSessionForm({ ...sessionForm, service_type: value })}
                  >
                    <SelectTrigger className="form-input" data-testid="service-type-select">
                      <SelectValue placeholder="Select service type" />
                    </SelectTrigger>
                    <SelectContent className="bg-slate-800 border-slate-600">
                      {serviceTypes.map((service) => (
                        <SelectItem key={service} value={service}>
                          {service}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="start_at" className="text-slate-200">
                    Start Time *
                  </Label>
                  <Input
                    id="start_at"
                    type="datetime-local"
                    value={sessionForm.start_at}
                    onChange={(e) => setSessionForm({ ...sessionForm, start_at: e.target.value })}
                    className="form-input"
                    data-testid="start-time-input"
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="end_at" className="text-slate-200">
                    End Time *
                  </Label>
                  <Input
                    id="end_at"
                    type="datetime-local"
                    value={sessionForm.end_at}
                    onChange={(e) => setSessionForm({ ...sessionForm, end_at: e.target.value })}
                    className="form-input"
                    data-testid="end-time-input"
                    required
                  />
                </div>
              </div>

              <div className="flex space-x-3">
                <Button
                  type="submit"
                  disabled={createSessionMutation.isPending}
                  className="btn-primary"
                  data-testid="submit-session-button"
                >
                  {createSessionMutation.isPending ? (
                    <div className="flex items-center space-x-2">
                      <div className="loading-spinner"></div>
                      <span>Creating...</span>
                    </div>
                  ) : (
                    'Create Session'
                  )}
                </Button>
                <Button
                  type="button"
                  onClick={() => setShowCreateForm(false)}
                  className="btn-secondary"
                >
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-3 bg-slate-800/50">
          <TabsTrigger 
            value="calendar" 
            className="data-[state=active]:bg-blue-500/20 data-[state=active]:text-blue-400"
            data-testid="calendar-tab"
          >
            <CalendarIcon className="w-4 h-4 mr-2" />
            Calendar
          </TabsTrigger>
          <TabsTrigger 
            value="upcoming" 
            className="data-[state=active]:bg-blue-500/20 data-[state=active]:text-blue-400"
            data-testid="upcoming-tab"
          >
            <Clock className="w-4 h-4 mr-2" />
            Upcoming
          </TabsTrigger>
          <TabsTrigger 
            value="all" 
            className="data-[state=active]:bg-blue-500/20 data-[state=active]:text-blue-400"
            data-testid="all-sessions-tab"
          >
            <Eye className="w-4 h-4 mr-2" />
            All Sessions
          </TabsTrigger>
        </TabsList>

        {/* Calendar View */}
        <TabsContent value="calendar">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card className="glass-card lg:col-span-1">
              <CardHeader>
                <CardTitle className="text-white font-serif">Calendar</CardTitle>
                <CardDescription className="text-slate-400">
                  Select a date to view sessions
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Calendar
                  mode="single"
                  selected={selectedDate}
                  onSelect={setSelectedDate}
                  className="rounded-md border border-slate-600 bg-slate-800/30"
                  data-testid="sessions-calendar"
                />
              </CardContent>
            </Card>

            <Card className="glass-card lg:col-span-2">
              <CardHeader>
                <CardTitle className="text-white font-serif flex items-center">
                  <CalendarIcon className="w-5 h-5 mr-2 text-blue-400" />
                  {format(selectedDate, 'EEEE, MMMM d, yyyy')}
                </CardTitle>
                <CardDescription className="text-slate-400">
                  Sessions for this date
                </CardDescription>
              </CardHeader>
              <CardContent>
                {sessionsLoading ? (
                  <div className="space-y-4">
                    {[1, 2, 3].map(i => (
                      <div key={i} className="animate-pulse p-4 rounded-lg bg-slate-700/30">
                        <div className="h-4 bg-slate-600/50 rounded mb-2"></div>
                        <div className="h-3 bg-slate-600/30 rounded w-3/4"></div>
                      </div>
                    ))}
                  </div>
                ) : sessionsForDate.length > 0 ? (
                  <div className="space-y-4">
                    {sessionsForDate.map((session) => (
                      <div 
                        key={session.id} 
                        className="p-4 rounded-lg bg-slate-800/30 border border-slate-600/30"
                      >
                        <div className="flex justify-between items-start">
                          <div className="space-y-2">
                            <div className="flex items-center space-x-2">
                              {getStatusIcon(session.status)}
                              <h3 className="font-medium text-white">
                                {session.service_type}
                              </h3>
                            </div>
                            <div className="flex items-center space-x-4 text-sm text-slate-400">
                              <span className="flex items-center">
                                <Clock className="w-3 h-3 mr-1" />
                                {format(new Date(session.start_at), 'h:mm a')} - {format(new Date(session.end_at), 'h:mm a')}
                              </span>
                              <span className="flex items-center">
                                <Users className="w-3 h-3 mr-1" />
                                Client ID: {session.client_id}
                              </span>
                            </div>
                            {session.payment_status && (
                              <Badge variant="outline" className="text-xs">
                                Payment: {session.payment_status}
                              </Badge>
                            )}
                          </div>
                          <Badge className={`${getStatusColor(session.status)} border`}>
                            {session.status}
                          </Badge>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-slate-400">
                    <CalendarIcon className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <p>No sessions scheduled for this date</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Upcoming Sessions */}
        <TabsContent value="upcoming">
          <Card className="glass-card">
            <CardHeader>
              <CardTitle className="text-white font-serif flex items-center">
                <Clock className="w-5 h-5 mr-2 text-blue-400" />
                Upcoming Sessions
              </CardTitle>
              <CardDescription className="text-slate-400">
                Your scheduled sessions in chronological order
              </CardDescription>
            </CardHeader>
            <CardContent>
              {sessionsLoading ? (
                <div className="space-y-4">
                  {[1, 2, 3, 4].map(i => (
                    <div key={i} className="animate-pulse p-4 rounded-lg bg-slate-700/30">
                      <div className="h-4 bg-slate-600/50 rounded mb-2"></div>
                      <div className="h-3 bg-slate-600/30 rounded w-3/4"></div>
                    </div>
                  ))}
                </div>
              ) : upcomingSessions.length > 0 ? (
                <div className="space-y-4">
                  {upcomingSessions.map((session, index) => (
                    <div 
                      key={session.id} 
                      className="p-4 rounded-lg bg-slate-800/30 border border-slate-600/30 hover:border-blue-500/40 transition-all"
                    >
                      <div className="flex justify-between items-start">
                        <div className="space-y-2">
                          <div className="flex items-center space-x-3">
                            <Badge variant="outline" className="text-xs">
                              #{index + 1}
                            </Badge>
                            <h3 className="font-medium text-white">
                              {session.service_type}
                            </h3>
                          </div>
                          <div className="flex items-center space-x-4 text-sm text-slate-400">
                            <span className="flex items-center">
                              <CalendarIcon className="w-3 h-3 mr-1" />
                              {format(new Date(session.start_at), 'MMM d, yyyy')}
                            </span>
                            <span className="flex items-center">
                              <Clock className="w-3 h-3 mr-1" />
                              {format(new Date(session.start_at), 'h:mm a')} - {format(new Date(session.end_at), 'h:mm a')}
                            </span>
                            <span className="flex items-center">
                              <Users className="w-3 h-3 mr-1" />
                              Client: {session.client_id}
                            </span>
                          </div>
                        </div>
                        <Badge className={`${getStatusColor(session.status)} border`}>
                          {session.status}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 text-slate-400">
                  <Clock className="w-16 h-16 mx-auto mb-4 opacity-50" />
                  <h3 className="text-white font-medium mb-2">No Upcoming Sessions</h3>
                  <p className="mb-6">
                    {user?.role === 'reader' 
                      ? 'Create new sessions to start serving your clients'
                      : 'Book a session to begin your cosmic journey'
                    }
                  </p>
                  {user?.role === 'reader' && (
                    <Button 
                      onClick={() => setShowCreateForm(true)}
                      className="btn-primary"
                    >
                      <Plus className="w-4 h-4 mr-2" />
                      Create Session
                    </Button>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* All Sessions */}
        <TabsContent value="all">
          <Card className="glass-card">
            <CardHeader>
              <CardTitle className="text-white font-serif flex items-center">
                <Eye className="w-5 h-5 mr-2 text-blue-400" />
                All Sessions
              </CardTitle>
              <CardDescription className="text-slate-400">
                Complete session history
              </CardDescription>
            </CardHeader>
            <CardContent>
              {sessionsLoading ? (
                <div className="space-y-4">
                  {[1, 2, 3, 4, 5].map(i => (
                    <div key={i} className="animate-pulse p-4 rounded-lg bg-slate-700/30">
                      <div className="h-4 bg-slate-600/50 rounded mb-2"></div>
                      <div className="h-3 bg-slate-600/30 rounded w-3/4"></div>
                    </div>
                  ))}
                </div>
              ) : allSessions.length > 0 ? (
                <div className="space-y-4">
                  {allSessions.map((session) => (
                    <div 
                      key={session.id} 
                      className="p-4 rounded-lg bg-slate-800/30 border border-slate-600/30"
                    >
                      <div className="flex justify-between items-start">
                        <div className="space-y-2">
                          <div className="flex items-center space-x-2">
                            {getStatusIcon(session.status)}
                            <h3 className="font-medium text-white">
                              {session.service_type}
                            </h3>
                          </div>
                          <div className="flex items-center space-x-4 text-sm text-slate-400">
                            <span className="flex items-center">
                              <CalendarIcon className="w-3 h-3 mr-1" />
                              {format(new Date(session.start_at), 'MMM d, yyyy')}
                            </span>
                            <span className="flex items-center">
                              <Clock className="w-3 h-3 mr-1" />
                              {format(new Date(session.start_at), 'h:mm a')} - {format(new Date(session.end_at), 'h:mm a')}
                            </span>
                            <span className="flex items-center">
                              <Users className="w-3 h-3 mr-1" />
                              Client: {session.client_id}
                            </span>
                          </div>
                          {session.payment_status && (
                            <div className="flex items-center space-x-2">
                              <Badge variant="outline" className="text-xs">
                                Payment: {session.payment_status}
                              </Badge>
                            </div>
                          )}
                        </div>
                        <Badge className={`${getStatusColor(session.status)} border`}>
                          {session.status}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 text-slate-400">
                  <Eye className="w-16 h-16 mx-auto mb-4 opacity-50" />
                  <h3 className="text-white font-medium mb-2">No Sessions Found</h3>
                  <p>Your session history will appear here once you start booking or creating sessions.</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default SessionsPage;