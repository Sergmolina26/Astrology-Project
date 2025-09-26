import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../context/AuthContext';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Badge } from './ui/badge';
import { Calendar } from './ui/calendar';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { 
  Calendar as CalendarIcon, 
  Clock,
  Plus, 
  Users,
  MapPin,
  CheckCircle,
  XCircle,
  AlertCircle,
  Eye,
  Edit3,
  Save,
  NotebookPen
} from 'lucide-react';
import { toast } from 'sonner';
import { format, addDays, startOfMonth, endOfMonth, eachDayOfInterval, isSameDay } from 'date-fns';

const SessionsPage = () => {
  const { user } = useAuth();
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [activeTab, setActiveTab] = useState('list');
  const [selectedSession, setSelectedSession] = useState(null);
  const [personalNote, setPersonalNote] = useState('');
  const [editingPersonalNote, setEditingPersonalNote] = useState(false);
  const [misticaNote, setMisticaNote] = useState('');
  const [misticaNoteVisible, setMisticaNoteVisible] = useState(true);

  // Fetch sessions
  const { data: sessions = [], isLoading: sessionsLoading } = useQuery({
    queryKey: ['sessions'],
    queryFn: () => axios.get('/sessions').then(res => res.data)
  });

  // Fetch session notes
  const { data: sessionNotes, isLoading: notesLoading } = useQuery({
    queryKey: ['session-notes', selectedSession?.id],
    queryFn: () => selectedSession ? axios.get(`/sessions/${selectedSession.id}/notes`).then(res => res.data) : null,
    enabled: !!selectedSession
  });

  // Load personal note when sessionNotes changes
  React.useEffect(() => {
    if (sessionNotes?.personal_notes?.[0]?.note_content && !editingPersonalNote) {
      setPersonalNote(sessionNotes.personal_notes[0].note_content);
    }
  }, [sessionNotes, editingPersonalNote]);

  // Personal note mutation
  const personalNoteMutation = useMutation({
    mutationFn: ({ sessionId, content }) => 
      axios.post(`/sessions/${sessionId}/personal-notes?note_content=${encodeURIComponent(content)}`),
    onSuccess: () => {
      queryClient.invalidateQueries(['session-notes']);
      setEditingPersonalNote(false);
      toast.success(t('sessions.saveNotes') + ' ' + t('common.success'));
    },
    onError: (error) => {
      toast.error(t('sessions.failedSavePersonalNote'));
    }
  });

  // Mistica note mutation (admin only)
  const misticaNoteMutation = useMutation({
    mutationFn: ({ sessionId, content, visible }) => 
      axios.post(`/sessions/${sessionId}/mistica-notes?note_content=${encodeURIComponent(content)}&is_visible_to_client=${visible}`),
    onSuccess: () => {
      queryClient.invalidateQueries(['session-notes']);
      toast.success(t('sessions.misticaNoteSaved'));
      setMisticaNote('');
    },
    onError: (error) => {
      toast.error(t('sessions.failedSaveMisticaNote'));
    }
  });

  const upcomingSessions = sessions.filter(session => {
    const sessionDate = new Date(session.start_at);
    return sessionDate > new Date() && ['pending_payment', 'confirmed'].includes(session.status);
  });

  const pastSessions = sessions.filter(session => {
    const sessionDate = new Date(session.start_at);
    return sessionDate <= new Date() || session.status === 'completed';
  });

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

  const getStatusText = (status) => {
    const statusMap = {
      'pending_payment': t('sessions.pendingPayment'),
      'confirmed': t('sessions.confirmed'),
      'completed': t('sessions.completed'),
      'cancelled': t('sessions.cancelled'),
      'declined': t('sessions.declined')
    };
    return statusMap[status] || status;
  };

  const handleSavePersonalNote = () => {
    if (selectedSession && personalNote.trim()) {
      personalNoteMutation.mutate({
        sessionId: selectedSession.id,
        content: personalNote.trim()
      });
    }
  };

  const handleSaveMisticaNote = () => {
    if (selectedSession && misticaNote.trim()) {
      misticaNoteMutation.mutate({
        sessionId: selectedSession.id,
        content: misticaNote.trim(),
        visible: misticaNoteVisible
      });
    }
  };

  const SessionCard = ({ session, isPast = false }) => (
    <Card className="glass-card border-slate-600/30 hover:border-amber-400/50 transition-colors">
      <CardContent className="pt-6">
        <div className="flex items-start justify-between">
          <div className="space-y-3 flex-1">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 rounded-full bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center">
                <Users className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="font-semibold text-white">{session.service_type}</h3>
                <p className="text-sm text-slate-400">
                  {t('sessions.sessionWith')} Celestia
                </p>
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
              <div className="flex items-center text-slate-300">
                <CalendarIcon className="w-4 h-4 mr-2 text-amber-400" />
                {new Date(session.start_at).toLocaleDateString()}
              </div>
              <div className="flex items-center text-slate-300">
                <Clock className="w-4 h-4 mr-2 text-amber-400" />
                {new Date(session.start_at).toLocaleTimeString('en-US', { 
                  hour: 'numeric', 
                  minute: '2-digit', 
                  hour12: true,
                  timeZone: 'UTC'
                })}
              </div>
              <div className="flex items-center text-slate-300">
                <span className="w-4 h-4 mr-2 text-amber-400">💰</span>
                ${session.amount}
              </div>
              <div className="flex items-center">
                <Badge className={getStatusColor(session.status)}>
                  {getStatusText(session.status)}
                </Badge>
              </div>
            </div>

            {session.client_message && (
              <div className="mt-3 p-3 bg-slate-800/30 rounded-lg">
                <p className="text-sm text-slate-300 italic">
                  "{session.client_message}"
                </p>
              </div>
            )}
          </div>

          <div className="flex flex-col space-y-2 ml-4">
            <Dialog onOpenChange={(open) => {
              if (open) {
                setSelectedSession(session);
                setPersonalNote('');
                setMisticaNote('');
                setEditingPersonalNote(false);
                setMisticaNoteVisible(true);
              }
            }}>
              <DialogTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-amber-400 hover:text-amber-300"
                >
                  <Eye className="w-4 h-4 mr-2" />
                  {t('sessions.viewDetails')}
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto glass-card border-amber-400/30">
                <DialogHeader>
                  <DialogTitle className="text-white flex items-center">
                    <NotebookPen className="w-5 h-5 mr-2 text-amber-400" />
                    {t('sessions.sessionDetails')}
                  </DialogTitle>
                  <DialogDescription className="text-slate-300">
                    {session.service_type} - {new Date(session.start_at).toLocaleDateString()}
                  </DialogDescription>
                </DialogHeader>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
                  {/* Session Info */}
                  <div className="space-y-4">
                    <Card className="bg-slate-800/30 border-slate-600/30">
                      <CardHeader>
                        <CardTitle className="text-white text-lg">
                          {t('sessions.sessionDetails')}
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-3 text-sm">
                        <div className="flex justify-between">
                          <span className="text-slate-400">{t('services.selectService')}:</span>
                          <span className="text-white">{session.service_type}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-400">{t('sessions.scheduledFor')}:</span>
                          <span className="text-white">
                            {new Date(session.start_at).toLocaleDateString('en-US', { 
                              month: 'long', 
                              day: 'numeric', 
                              year: 'numeric' 
                            })} {new Date(session.start_at).toLocaleTimeString('en-US', { 
                              hour: 'numeric', 
                              minute: '2-digit', 
                              hour12: true,
                              timeZone: 'UTC'
                            })}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-400">{t('sessions.investment')}:</span>
                          <span className="text-white">${session.amount}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-400">{t('sessions.status')}:</span>
                          <Badge className={getStatusColor(session.status)}>
                            {getStatusText(session.status)}
                          </Badge>
                        </div>
                      </CardContent>
                    </Card>

                    {/* Personal Notes */}
                    <Card className="bg-slate-800/30 border-slate-600/30">
                      <CardHeader>
                        <div className="flex items-center justify-between">
                          <CardTitle className="text-white text-lg">
                            {t('sessions.personalNotes')}
                          </CardTitle>
                          {!editingPersonalNote && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => setEditingPersonalNote(true)}
                              className="text-amber-400 hover:text-amber-300"
                            >
                              <Edit3 className="w-4 h-4" />
                            </Button>
                          )}
                        </div>
                      </CardHeader>
                      <CardContent>
                        {editingPersonalNote ? (
                          <div className="space-y-3">
                            <Textarea
                              placeholder={t('sessions.addPersonalNote')}
                              value={personalNote}
                              onChange={(e) => setPersonalNote(e.target.value)}
                              className="form-input min-h-[120px]"
                            />
                            <div className="flex space-x-2">
                              <Button
                                onClick={handleSavePersonalNote}
                                disabled={personalNoteMutation.isPending}
                                className="btn-primary"
                                size="sm"
                              >
                                <Save className="w-4 h-4 mr-2" />
                                {personalNoteMutation.isPending ? t('common.submitting') : t('sessions.saveNotes')}
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => setEditingPersonalNote(false)}
                                className="text-slate-400"
                              >
                                {t('common.cancel')}
                              </Button>
                            </div>
                          </div>
                        ) : (
                          <div>
                            {sessionNotes?.personal_notes?.[0]?.note_content ? (
                              <p className="text-slate-300 whitespace-pre-wrap">
                                {sessionNotes.personal_notes[0].note_content}
                              </p>
                            ) : (
                              <p className="text-slate-500 italic">
                                {t('sessions.noPersonalNotes')}
                              </p>
                            )}
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  </div>

                  {/* Mistica's Notes */}
                  <div className="space-y-4">
                    <Card className="bg-slate-800/30 border-slate-600/30">
                      <CardHeader>
                        <CardTitle className="text-white text-lg">
                          {t('sessions.misticasNotes')}
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-4">
                          {sessionNotes?.mistica_notes?.length > 0 ? (
                            sessionNotes.mistica_notes.map((note, index) => (
                              <div key={index} className="p-4 bg-amber-500/10 border border-amber-400/30 rounded-lg">
                                <p className="text-slate-300 whitespace-pre-wrap">
                                  {note.note_content}
                                </p>
                                <p className="text-xs text-amber-400 mt-2">
                                  {new Date(note.created_at).toLocaleDateString()}
                                </p>
                              </div>
                            ))
                          ) : (
                            <p className="text-slate-500 italic">
                              {t('sessions.noMisticasNotes')}
                            </p>
                          )}

                          {/* Admin can add new Mística notes */}
                          {user?.role === 'admin' && (
                            <div className="space-y-3 pt-4 border-t border-slate-600/30">
                              <Label className="text-slate-200">
                                {t('sessions.addMisticaNote')}
                              </Label>
                              <Textarea
                                placeholder="Add your professional insights for this client..."
                                value={misticaNote}
                                onChange={(e) => setMisticaNote(e.target.value)}
                                className="form-input min-h-[100px]"
                              />
                              <div className="flex items-center space-x-3">
                                <label className="flex items-center space-x-2 text-sm text-slate-300">
                                  <input
                                    type="checkbox"
                                    checked={misticaNoteVisible}
                                    onChange={(e) => setMisticaNoteVisible(e.target.checked)}
                                    className="rounded"
                                  />
                                  <span>Visible to client</span>
                                </label>
                              </div>
                              <Button
                                onClick={handleSaveMisticaNote}
                                disabled={misticaNoteMutation.isPending || !misticaNote.trim()}
                                className="btn-primary"
                                size="sm"
                              >
                                <Save className="w-4 h-4 mr-2" />
                                {misticaNoteMutation.isPending ? t('common.submitting') : t('sessions.saveNote')}
                              </Button>
                            </div>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center space-y-4">
        <div className="flex justify-center items-center space-x-3">
          <div className="w-12 h-12 rounded-full bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center animate-mystical-glow">
            <CalendarIcon className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-white font-mystical">
            {t('sessions.myBookings')}
          </h1>
        </div>
        <p className="text-slate-300 max-w-2xl mx-auto">
          {t('sessions.manageUpcoming')}
        </p>
      </div>

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-2 bg-slate-800/50 border border-slate-600/30 rounded-lg p-1">
          <TabsTrigger 
            value="list" 
            className="data-[state=active]:bg-amber-500/20 data-[state=active]:text-amber-400"
          >
            <Eye className="w-4 h-4 mr-2" />
            {t('sessions.listView')}
          </TabsTrigger>
          <TabsTrigger 
            value="calendar" 
            className="data-[state=active]:bg-amber-500/20 data-[state=active]:text-amber-400"
          >
            <CalendarIcon className="w-4 h-4 mr-2" />
            {t('sessions.calendarView')}
          </TabsTrigger>
        </TabsList>

        {/* List View */}
        <TabsContent value="list" className="mt-6">
          <div className="grid gap-6">
            {/* Upcoming Sessions */}
            <Card className="glass-card mystical-border">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2 text-white">
                  <Clock className="w-5 h-5 text-amber-400" />
                  <span>{t('sessions.upcomingBookings')}</span>
                </CardTitle>
                <CardDescription className="text-slate-300">
                  {t('sessions.manageUpcoming')}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {sessionsLoading ? (
                  <div className="text-center py-8">
                    <div className="loading-spinner mx-auto mb-4"></div>
                    <p className="text-slate-400">{t('common.loading')}</p>
                  </div>
                ) : upcomingSessions.length === 0 ? (
                  <div className="text-center py-12">
                    <CalendarIcon className="w-16 h-16 text-slate-600 mx-auto mb-4" />
                    <h3 className="text-xl font-semibold text-slate-300 mb-2">
                      {t('sessions.noUpcoming')}
                    </h3>
                    <p className="text-slate-400 mb-6">
                      {t('sessions.bookFirstSession')}
                    </p>
                    <Button 
                      onClick={() => window.location.href = '/tarot'}
                      className="btn-primary"
                    >
                      <Plus className="w-4 h-4 mr-2" />
                      {t('sessions.bookSession')}
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {upcomingSessions.map((session) => (
                      <SessionCard key={session.id} session={session} />
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Past Sessions */}
            <Card className="glass-card mystical-border">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2 text-white">
                  <CheckCircle className="w-5 h-5 text-amber-400" />
                  <span>{t('sessions.pastSessions')}</span>
                </CardTitle>
                <CardDescription className="text-slate-300">
                  {t('sessions.viewPastSessions')}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {pastSessions.length === 0 ? (
                  <div className="text-center py-8">
                    <CheckCircle className="w-16 h-16 text-slate-600 mx-auto mb-4" />
                    <h3 className="text-xl font-semibold text-slate-300 mb-2">
                      {t('sessions.noPast')}
                    </h3>
                    <p className="text-slate-400">
                      {t('sessions.viewPastSessions')}
                    </p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {pastSessions.map((session) => (
                      <SessionCard key={session.id} session={session} isPast={true} />
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Calendar View */}
        <TabsContent value="calendar" className="mt-6">
          <Card className="glass-card mystical-border">
            <CardHeader>
              <CardTitle className="text-white">{t('sessions.calendarView')}</CardTitle>
              <CardDescription className="text-slate-300">
                {t('sessions.manageUpcoming')}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid lg:grid-cols-3 gap-6">
                <div className="lg:col-span-1">
                  <Calendar
                    mode="single"
                    selected={selectedDate}
                    onSelect={setSelectedDate}
                    className="rounded-md border border-slate-600/30"
                  />
                </div>
                <div className="lg:col-span-2">
                  <h3 className="text-lg font-semibold text-white mb-4">
                    {format(selectedDate, 'MMMM d, yyyy')}
                  </h3>
                  <div className="space-y-3">
                    {sessions
                      .filter(session => isSameDay(new Date(session.start_at), selectedDate))
                      .map((session) => (
                        <SessionCard key={session.id} session={session} />
                      ))}
                    {sessions.filter(session => isSameDay(new Date(session.start_at), selectedDate)).length === 0 && (
                      <p className="text-slate-400 italic">
                        No sessions scheduled for this day
                      </p>
                    )}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default SessionsPage;