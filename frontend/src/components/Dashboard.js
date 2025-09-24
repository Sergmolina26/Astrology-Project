import React from 'react';
import { useAuth } from '../context/AuthContext';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { 
  Calendar, 
  Sparkles, 
  Stars, 
  Clock, 
  Users, 
  TrendingUp,
  Moon,
  Sun
} from 'lucide-react';

const Dashboard = () => {
  const { user } = useAuth();

  const { data: sessions = [], isLoading: sessionsLoading } = useQuery({
    queryKey: ['sessions'],
    queryFn: () => axios.get('/sessions').then(res => res.data)
  });

  const upcomingSessions = sessions.filter(session => 
    new Date(session.start_at) > new Date() && session.status === 'scheduled'
  ).slice(0, 3);

  const recentSessions = sessions.filter(session => 
    session.status === 'completed'
  ).slice(0, 3);

  return (
    <div className="space-y-8">
      {/* Welcome Header */}
      <div className="relative">
        <div className="glass-card p-8 text-center relative overflow-hidden">
          {/* Decorative elements */}
          <div className="absolute top-4 left-4 animate-float">
            <Stars className="w-6 h-6 text-amber-400/30" />
          </div>
          <div className="absolute top-4 right-4 animate-float" style={{ animationDelay: '2s' }}>
            <Moon className="w-6 h-6 text-purple-400/30" />
          </div>
          <div className="absolute bottom-4 left-1/4 animate-float" style={{ animationDelay: '4s' }}>
            <Sparkles className="w-5 h-5 text-amber-300/25" />
          </div>
          <div className="absolute bottom-4 right-1/4 animate-float" style={{ animationDelay: '1s' }}>
            <Sun className="w-5 h-5 text-orange-400/30" />
          </div>

          <h1 className="font-serif text-3xl md:text-4xl font-bold text-white mb-4">
            Welcome back, {user?.name}
          </h1>
          <p className="text-slate-300 text-lg mb-6">
            {user?.role === 'reader' 
              ? 'Your cosmic guidance awaits those who seek wisdom'
              : 'Your celestial journey continues with new insights'
            }
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/astrology">
              <Button className="btn-primary" data-testid="quick-astrology-btn">
                <Sparkles className="w-4 h-4 mr-2" />
                Generate Birth Chart
              </Button>
            </Link>
            <Link to="/tarot">
              <Button className="btn-secondary" data-testid="quick-tarot-btn">
                <Stars className="w-4 h-4 mr-2" />
                Book Services
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="glass-card card-hover">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">
              Total Sessions
            </CardTitle>
            <Calendar className="h-4 w-4 text-amber-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white" data-testid="total-sessions-count">
              {sessionsLoading ? '...' : sessions.length}
            </div>
            <p className="text-xs text-slate-400">
              {user?.role === 'reader' ? 'Readings conducted' : 'Sessions attended'}
            </p>
          </CardContent>
        </Card>

        <Card className="glass-card card-hover">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">
              This Month
            </CardTitle>
            <TrendingUp className="h-4 w-4 text-emerald-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white" data-testid="monthly-sessions-count">
              {sessionsLoading ? '...' : sessions.filter(s => 
                new Date(s.created_at).getMonth() === new Date().getMonth()
              ).length}
            </div>
            <p className="text-xs text-slate-400">
              Sessions this month
            </p>
          </CardContent>
        </Card>

        <Card className="glass-card card-hover">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">
              Upcoming
            </CardTitle>
            <Clock className="h-4 w-4 text-blue-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white" data-testid="upcoming-sessions-count">
              {sessionsLoading ? '...' : upcomingSessions.length}
            </div>
            <p className="text-xs text-slate-400">
              Scheduled sessions
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Upcoming Sessions */}
        <Card className="glass-card">
          <CardHeader>
            <CardTitle className="text-white font-serif flex items-center">
              <Clock className="w-5 h-5 mr-2 text-amber-400" />
              Upcoming Sessions
            </CardTitle>
            <CardDescription className="text-slate-400">
              Your next scheduled readings
            </CardDescription>
          </CardHeader>
          <CardContent>
            {sessionsLoading ? (
              <div className="space-y-4">
                {[1, 2, 3].map(i => (
                  <div key={i} className="animate-pulse">
                    <div className="h-4 bg-slate-700/50 rounded mb-2"></div>
                    <div className="h-3 bg-slate-700/30 rounded w-3/4"></div>
                  </div>
                ))}
              </div>
            ) : upcomingSessions.length > 0 ? (
              <div className="space-y-4">
                {upcomingSessions.map((session) => (
                  <div key={session.id} className="p-4 rounded-lg bg-slate-800/30 border border-slate-600/30">
                    <div className="flex justify-between items-start">
                      <div>
                        <h4 className="font-medium text-white">
                          {session.service_type}
                        </h4>
                        <p className="text-sm text-slate-400">
                          {new Date(session.start_at).toLocaleDateString()} at{' '}
                          {new Date(session.start_at).toLocaleTimeString([], {
                            hour: '2-digit',
                            minute: '2-digit'
                          })}
                        </p>
                      </div>
                      <span className="px-2 py-1 text-xs bg-amber-500/20 text-amber-400 rounded-full">
                        {session.status}
                      </span>
                    </div>
                  </div>
                ))}
                <Link to="/sessions">
                  <Button variant="ghost" className="w-full text-amber-400 hover:text-amber-300">
                    View All Sessions
                  </Button>
                </Link>
              </div>
            ) : (
              <div className="text-center py-8 text-slate-400">
                <Calendar className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>No upcoming sessions</p>
                <p className="text-sm">Schedule your next cosmic reading</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent Sessions */}
        <Card className="glass-card">
          <CardHeader>
            <CardTitle className="text-white font-serif flex items-center">
              <Stars className="w-5 h-5 mr-2 text-purple-400" />
              Recent Sessions
            </CardTitle>
            <CardDescription className="text-slate-400">
              Your latest completed readings
            </CardDescription>
          </CardHeader>
          <CardContent>
            {sessionsLoading ? (
              <div className="space-y-4">
                {[1, 2, 3].map(i => (
                  <div key={i} className="animate-pulse">
                    <div className="h-4 bg-slate-700/50 rounded mb-2"></div>
                    <div className="h-3 bg-slate-700/30 rounded w-3/4"></div>
                  </div>
                ))}
              </div>
            ) : recentSessions.length > 0 ? (
              <div className="space-y-4">
                {recentSessions.map((session) => (
                  <div key={session.id} className="p-4 rounded-lg bg-slate-800/30 border border-slate-600/30">
                    <div className="flex justify-between items-start">
                      <div>
                        <h4 className="font-medium text-white">
                          {session.service_type}
                        </h4>
                        <p className="text-sm text-slate-400">
                          {new Date(session.start_at).toLocaleDateString()}
                        </p>
                      </div>
                      <span className="px-2 py-1 text-xs bg-emerald-500/20 text-emerald-400 rounded-full">
                        completed
                      </span>
                    </div>
                  </div>
                ))}
                <Link to="/sessions">
                  <Button variant="ghost" className="w-full text-amber-400 hover:text-amber-300">
                    View All Sessions
                  </Button>
                </Link>
              </div>
            ) : (
              <div className="text-center py-8 text-slate-400">
                <Stars className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>No completed sessions yet</p>
                <p className="text-sm">Your reading history will appear here</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card className="glass-card">
        <CardHeader>
          <CardTitle className="text-white font-serif">
            Quick Actions
          </CardTitle>
          <CardDescription className="text-slate-400">
            Jump into your mystical practice
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <Link to="/astrology" className="group">
              <div className="p-6 rounded-lg bg-gradient-to-br from-amber-500/10 to-orange-500/10 border border-amber-500/20 hover:border-amber-500/40 transition-all card-hover group-hover:scale-105">
                <Sparkles className="w-8 h-8 text-amber-400 mb-3" />
                <h3 className="font-medium text-white mb-2">Birth Chart</h3>
                <p className="text-sm text-slate-400">Generate natal charts</p>
              </div>
            </Link>

            <Link to="/tarot" className="group">
              <div className="p-6 rounded-lg bg-gradient-to-br from-purple-500/10 to-pink-500/10 border border-purple-500/20 hover:border-purple-500/40 transition-all card-hover group-hover:scale-105">
                <Stars className="w-8 h-8 text-purple-400 mb-3" />
                <h3 className="font-medium text-white mb-2">Tarot Reading</h3>
                <p className="text-sm text-slate-400">Draw and interpret cards</p>
              </div>
            </Link>

            <Link to="/sessions" className="group">
              <div className="p-6 rounded-lg bg-gradient-to-br from-blue-500/10 to-cyan-500/10 border border-blue-500/20 hover:border-blue-500/40 transition-all card-hover group-hover:scale-105">
                <Calendar className="w-8 h-8 text-blue-400 mb-3" />
                <h3 className="font-medium text-white mb-2">Sessions</h3>
                <p className="text-sm text-slate-400">Manage appointments</p>
              </div>
            </Link>

            {user?.role === 'reader' && (
              <div className="group cursor-pointer">
                <div className="p-6 rounded-lg bg-gradient-to-br from-emerald-500/10 to-teal-500/10 border border-emerald-500/20 hover:border-emerald-500/40 transition-all card-hover group-hover:scale-105">
                  <Users className="w-8 h-8 text-emerald-400 mb-3" />
                  <h3 className="font-medium text-white mb-2">Clients</h3>
                  <p className="text-sm text-slate-400">Manage client profiles</p>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Dashboard;