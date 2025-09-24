import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Badge } from './ui/badge';
import { 
  User, 
  Calendar,
  Clock, 
  Star,
  FileText,
  Settings,
  MapPin,
  Phone,
  Mail,
  Edit3,
  CheckCircle,
  AlertCircle,
  XCircle
} from 'lucide-react';
import { format } from 'date-fns';

const ProfilePage = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('overview');
  const [isEditing, setIsEditing] = useState(false);

  // Fetch user's sessions
  const { data: sessions = [], isLoading: sessionsLoading } = useQuery({
    queryKey: ['user-sessions'],
    queryFn: () => axios.get('/sessions').then(res => res.data)
  });

  // Fetch user's birth data and charts
  const { data: birthData = [], isLoading: birthDataLoading } = useQuery({
    queryKey: ['user-birth-data'],
    queryFn: async () => {
      try {
        const response = await axios.get(`/birth-data/${user.id}`);
        return response.data;
      } catch (error) {
        return [];
      }
    },
    enabled: !!user?.id
  });

  const { data: charts = [], isLoading: chartsLoading } = useQuery({
    queryKey: ['user-charts'],
    queryFn: async () => {
      try {
        const response = await axios.get(`/astrology/charts/${user.id}`);
        return response.data;
      } catch (error) {
        return [];
      }
    },
    enabled: !!user?.id
  });

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

  const upcomingSessions = sessions.filter(session => 
    new Date(session.start_at) > new Date() && session.status === 'scheduled'
  ).sort((a, b) => new Date(a.start_at) - new Date(b.start_at));

  const pastSessions = sessions.filter(session => 
    session.status === 'completed' || new Date(session.start_at) < new Date()
  ).sort((a, b) => new Date(b.start_at) - new Date(a.start_at));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="font-serif text-3xl font-bold text-white mb-2 flex items-center">
            <User className="w-8 h-8 mr-3 text-purple-400" />
            My Profile
          </h1>
          <p className="text-slate-400">Manage your account and view your cosmic journey</p>
        </div>
        <Button 
          onClick={() => setIsEditing(!isEditing)}
          variant="outline" 
          className="btn-secondary"
        >
          <Edit3 className="w-4 h-4 mr-2" />
          {isEditing ? 'Cancel' : 'Edit Profile'}
        </Button>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-4 bg-slate-800/50">
          <TabsTrigger 
            value="overview" 
            className="data-[state=active]:bg-purple-500/20 data-[state=active]:text-purple-400"
          >
            <User className="w-4 h-4 mr-2" />
            Overview
          </TabsTrigger>
          <TabsTrigger 
            value="sessions" 
            className="data-[state=active]:bg-purple-500/20 data-[state=active]:text-purple-400"
          >
            <Calendar className="w-4 h-4 mr-2" />
            Sessions
          </TabsTrigger>
          <TabsTrigger 
            value="charts" 
            className="data-[state=active]:bg-purple-500/20 data-[state=active]:text-purple-400"
          >
            <Star className="w-4 h-4 mr-2" />
            My Charts
          </TabsTrigger>
          <TabsTrigger 
            value="settings" 
            className="data-[state=active]:bg-purple-500/20 data-[state=active]:text-purple-400"
          >
            <Settings className="w-4 h-4 mr-2" />
            Settings
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Profile Info */}
            <Card className="glass-card lg:col-span-1">
              <CardHeader>
                <CardTitle className="text-white font-serif">Profile Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="text-center mb-4">
                  <div className="w-20 h-20 rounded-full bg-gradient-to-br from-purple-400 to-pink-500 flex items-center justify-center mx-auto mb-3">
                    <User className="w-10 h-10 text-white" />
                  </div>
                  <h3 className="text-lg font-semibold text-white">{user?.name}</h3>
                  <Badge className="bg-purple-500/20 text-purple-400 border-purple-500/30 mt-1">
                    {user?.role}
                  </Badge>
                </div>

                <div className="space-y-3">
                  <div className="flex items-center space-x-3">
                    <Mail className="w-4 h-4 text-slate-400" />
                    <span className="text-slate-300 text-sm">{user?.email}</span>
                  </div>
                  {user?.phone && (
                    <div className="flex items-center space-x-3">
                      <Phone className="w-4 h-4 text-slate-400" />
                      <span className="text-slate-300 text-sm">{user?.phone}</span>
                    </div>
                  )}
                  <div className="flex items-center space-x-3">
                    <Clock className="w-4 h-4 text-slate-400" />
                    <span className="text-slate-300 text-sm">
                      Member since {format(new Date(user?.created_at || Date.now()), 'MMM yyyy')}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Quick Stats */}
            <div className="lg:col-span-2 space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card className="glass-card">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-slate-400">Total Sessions</p>
                        <p className="text-2xl font-bold text-white">{sessions.length}</p>
                      </div>
                      <Calendar className="w-8 h-8 text-purple-400" />
                    </div>
                  </CardContent>
                </Card>

                <Card className="glass-card">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-slate-400">Upcoming</p>
                        <p className="text-2xl font-bold text-white">{upcomingSessions.length}</p>
                      </div>
                      <AlertCircle className="w-8 h-8 text-amber-400" />
                    </div>
                  </CardContent>
                </Card>

                <Card className="glass-card">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-slate-400">Birth Charts</p>
                        <p className="text-2xl font-bold text-white">{charts.length}</p>
                      </div>
                      <Star className="w-8 h-8 text-emerald-400" />
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Recent Activity */}
              <Card className="glass-card">
                <CardHeader>
                  <CardTitle className="text-white font-serif">Recent Activity</CardTitle>
                </CardHeader>
                <CardContent>
                  {sessionsLoading ? (
                    <div className="space-y-3">
                      {[1, 2, 3].map(i => (
                        <div key={i} className="animate-pulse flex items-center space-x-3">
                          <div className="w-8 h-8 bg-slate-700 rounded-full"></div>
                          <div className="flex-1">
                            <div className="h-4 bg-slate-700 rounded w-3/4 mb-1"></div>
                            <div className="h-3 bg-slate-700 rounded w-1/2"></div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : sessions.length > 0 ? (
                    <div className="space-y-3">
                      {sessions.slice(0, 5).map((session) => (
                        <div key={session.id} className="flex items-center justify-between p-3 rounded-lg bg-slate-800/30">
                          <div className="flex items-center space-x-3">
                            {getStatusIcon(session.status)}
                            <div>
                              <p className="text-sm font-medium text-white">{session.service_type}</p>
                              <p className="text-xs text-slate-400">
                                {format(new Date(session.start_at), 'MMM d, yyyy')}
                              </p>
                            </div>
                          </div>
                          <Badge className={`${getStatusColor(session.status)} border`}>
                            {session.status}
                          </Badge>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-6 text-slate-400">
                      <Calendar className="w-12 h-12 mx-auto mb-3 opacity-50" />
                      <p>No sessions yet</p>
                      <p className="text-sm">Book your first reading to get started</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>

        {/* Sessions Tab */}
        <TabsContent value="sessions">
          <div className="space-y-6">
            {/* Upcoming Sessions */}
            <Card className="glass-card">
              <CardHeader>
                <CardTitle className="text-white font-serif flex items-center">
                  <Clock className="w-5 h-5 mr-2 text-amber-400" />
                  Upcoming Sessions
                </CardTitle>
              </CardHeader>
              <CardContent>
                {upcomingSessions.length > 0 ? (
                  <div className="space-y-4">
                    {upcomingSessions.map((session) => (
                      <div key={session.id} className="p-4 rounded-lg bg-slate-800/30 border border-slate-600/30">
                        <div className="flex justify-between items-start">
                          <div>
                            <h3 className="font-medium text-white mb-2">{session.service_type}</h3>
                            <div className="space-y-1 text-sm text-slate-400">
                              <div className="flex items-center">
                                <Calendar className="w-3 h-3 mr-2" />
                                {format(new Date(session.start_at), 'EEEE, MMMM d, yyyy')}
                              </div>
                              <div className="flex items-center">
                                <Clock className="w-3 h-3 mr-2" />
                                {format(new Date(session.start_at), 'h:mm a')} - {format(new Date(session.end_at), 'h:mm a')}
                              </div>
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
                  <div className="text-center py-8 text-slate-400">
                    <Clock className="w-12 h-12 mx-auto mb-3 opacity-50" />
                    <p>No upcoming sessions</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Past Sessions */}
            <Card className="glass-card">
              <CardHeader>
                <CardTitle className="text-white font-serif flex items-center">
                  <CheckCircle className="w-5 h-5 mr-2 text-emerald-400" />
                  Session History
                </CardTitle>
              </CardHeader>
              <CardContent>
                {pastSessions.length > 0 ? (
                  <div className="space-y-4">
                    {pastSessions.slice(0, 10).map((session) => (
                      <div key={session.id} className="p-4 rounded-lg bg-slate-800/30 border border-slate-600/30">
                        <div className="flex justify-between items-start">
                          <div>
                            <h3 className="font-medium text-white mb-2">{session.service_type}</h3>
                            <div className="space-y-1 text-sm text-slate-400">
                              <div className="flex items-center">
                                <Calendar className="w-3 h-3 mr-2" />
                                {format(new Date(session.start_at), 'MMM d, yyyy')}
                              </div>
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
                  <div className="text-center py-8 text-slate-400">
                    <FileText className="w-12 h-12 mx-auto mb-3 opacity-50" />
                    <p>No past sessions</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Charts Tab */}
        <TabsContent value="charts">
          <Card className="glass-card">
            <CardHeader>
              <CardTitle className="text-white font-serif flex items-center">
                <Star className="w-5 h-5 mr-2 text-purple-400" />
                My Birth Charts
              </CardTitle>
            </CardHeader>
            <CardContent>
              {chartsLoading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {[1, 2].map(i => (
                    <div key={i} className="animate-pulse p-4 rounded-lg bg-slate-700/30">
                      <div className="h-4 bg-slate-600/50 rounded mb-2"></div>
                      <div className="h-3 bg-slate-600/30 rounded w-3/4"></div>
                    </div>
                  ))}
                </div>
              ) : charts.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {charts.map((chart) => (
                    <div key={chart.id} className="p-4 rounded-lg bg-slate-800/30 border border-slate-600/30">
                      <h3 className="font-medium text-white mb-2">
                        Birth Chart - {chart.birth_data.birth_date}
                      </h3>
                      <div className="space-y-2 text-sm text-slate-400">
                        <div className="flex items-center">
                          <MapPin className="w-3 h-3 mr-2" />
                          {chart.birth_data.birth_place}
                        </div>
                        <div className="flex items-center">
                          <Calendar className="w-3 h-3 mr-2" />
                          Generated {format(new Date(chart.created_at), 'MMM d, yyyy')}
                        </div>
                      </div>
                      <div className="mt-3 text-xs text-emerald-400">
                        {Object.keys(chart.planets).length} planets • {Object.keys(chart.houses).length} houses
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-slate-400">
                  <Star className="w-12 h-12 mx-auto mb-3 opacity-50" />
                  <p>No birth charts generated</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Settings Tab */}
        <TabsContent value="settings">
          <Card className="glass-card">
            <CardHeader>
              <CardTitle className="text-white font-serif">Account Settings</CardTitle>
              <CardDescription className="text-slate-400">
                Manage your account preferences and information
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label className="text-slate-200">Full Name</Label>
                    <Input 
                      value={user?.name || ''} 
                      className="form-input"
                      disabled={!isEditing}
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label className="text-slate-200">Email</Label>
                    <Input 
                      value={user?.email || ''} 
                      className="form-input"
                      disabled={!isEditing}
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label className="text-slate-200">Phone (Optional)</Label>
                    <Input 
                      value={user?.phone || ''} 
                      placeholder="Enter phone number"
                      className="form-input"
                      disabled={!isEditing}
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label className="text-slate-200">Timezone</Label>
                    <Input 
                      value={user?.timezone || 'America/Chicago'} 
                      className="form-input"
                      disabled={!isEditing}
                    />
                  </div>
                </div>

                {isEditing && (
                  <div className="flex space-x-3 pt-4 border-t border-slate-600/30">
                    <Button className="btn-primary">
                      Save Changes
                    </Button>
                    <Button 
                      onClick={() => setIsEditing(false)}
                      className="btn-secondary"
                    >
                      Cancel
                    </Button>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default ProfilePage;