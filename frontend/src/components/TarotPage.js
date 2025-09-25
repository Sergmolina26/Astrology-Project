import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Textarea } from './ui/textarea';
import { Alert, AlertDescription } from './ui/alert';
import { Badge } from './ui/badge';
import { extractErrorMessage } from '../utils/errorHandler';
import { 
  Calendar,
  Clock,
  Sparkles,
  Star,
  Moon,
  Sun,
  Heart,
  DollarSign
} from 'lucide-react';
import { toast } from 'sonner';

const TarotPage = () => {
  const queryClient = useQueryClient();
  const { t } = useTranslation();
  
  const [sessionForm, setSessionForm] = useState({
    service_type: '',
    start_at: '',
    end_at: '',
    client_message: ''
  });

  // Available services with prices
  const services = [
    {
      id: 'general-purpose-reading',
      name: t('services.generalReading'),
      description: t('services.generalDescription'),
      price: 65,
      duration: 45,
      icon: Star
    },
    {
      id: 'astrological-tarot-session',
      name: t('services.astrologicalTarot'),
      description: t('services.astrologicalTarotDescription'),
      price: 85,
      duration: 60,
      icon: Moon
    },
    {
      id: 'birth-chart-reading',
      name: t('services.birthChart'),
      description: t('services.chartDescription'),
      price: 120,
      duration: 90,
      icon: Sun
    },
    {
      id: 'follow-up',
      name: t('services.followUp'),
      description: t('services.followUpDescription'),
      price: 45,
      duration: 30,
      icon: Heart
    }
  ];

  const selectedService = services.find(s => s.id === sessionForm.service_type);

  // Create session mutation
  const createSessionMutation = useMutation({
    mutationFn: async (sessionData) => {
      const response = await axios.post('/sessions', sessionData);
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries(['sessions']);
      setSessionForm({
        service_type: '',
        start_at: '',
        end_at: '',
        client_message: ''
      });
      toast.success(t('services.sessionRequested'));
    },
    onError: (error) => {
      const errorMessage = extractErrorMessage(error);
      toast.error(errorMessage);
    }
  });

  const handleServiceSelect = (serviceId) => {
    const service = services.find(s => s.id === serviceId);
    if (!service) return;
    
    setSessionForm(prev => ({
      ...prev,
      service_type: serviceId,
      // Auto-calculate end time based on duration
      end_at: prev.start_at ? calculateEndTime(prev.start_at, service.duration) : ''
    }));
  };

  const calculateEndTime = (startTime, durationMinutes) => {
    if (!startTime || !durationMinutes) return '';
    
    // Parse the datetime-local input correctly
    const start = new Date(startTime);
    
    // Add duration in minutes
    const end = new Date(start);
    end.setMinutes(start.getMinutes() + durationMinutes);
    
    // Format back to datetime-local format (YYYY-MM-DDTHH:mm)
    const year = end.getFullYear();
    const month = String(end.getMonth() + 1).padStart(2, '0');
    const day = String(end.getDate()).padStart(2, '0');
    const hours = String(end.getHours()).padStart(2, '0');
    const minutes = String(end.getMinutes()).padStart(2, '0');
    
    return `${year}-${month}-${day}T${hours}:${minutes}`;
  };

  const handleStartTimeChange = (startTime) => {
    setSessionForm(prev => ({
      ...prev,
      start_at: startTime,
      end_at: selectedService ? calculateEndTime(startTime, selectedService.duration) : ''
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (!sessionForm.service_type || !sessionForm.start_at) {
      toast.error(t('common.required'));
      return;
    }

    // Convert datetime-local to ISO string
    const sessionData = {
      ...sessionForm,
      start_at: new Date(sessionForm.start_at).toISOString(),
      end_at: new Date(sessionForm.end_at).toISOString()
    };

    createSessionMutation.mutate(sessionData);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center space-y-4">
        <div className="flex justify-center items-center space-x-3">
          <div className="w-12 h-12 rounded-full bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center animate-mystical-glow">
            <Star className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-white font-mystical">
            {t('services.bookReading')}
          </h1>
        </div>
        <p className="text-slate-300 max-w-2xl mx-auto">
          {t('services.schedulePersonalized')}
        </p>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Available Services */}
        <div className="lg:col-span-1">
          <Card className="glass-card mystical-border">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2 text-white">
                <Sparkles className="w-5 h-5 text-amber-400" />
                <span>{t('services.availableServices')}</span>
              </CardTitle>
              <CardDescription className="text-slate-300">
                {t('services.professionalReadings')}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {services.map((service) => {
                  const Icon = service.icon;
                  return (
                    <button
                      key={service.id}
                      onClick={() => handleServiceSelect(service.id)}
                      className={`w-full p-4 rounded-lg border transition-all text-left ${
                        sessionForm.service_type === service.id
                          ? 'border-amber-400 bg-amber-500/10'
                          : 'border-slate-600/30 bg-slate-800/30 hover:border-slate-500/50'
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex items-start space-x-3">
                          <Icon className={`w-5 h-5 mt-0.5 ${
                            sessionForm.service_type === service.id ? 'text-amber-400' : 'text-slate-400'
                          }`} />
                          <div className="space-y-1">
                            <h3 className={`font-medium ${
                              sessionForm.service_type === service.id ? 'text-amber-400' : 'text-white'
                            }`}>
                              {service.name}
                            </h3>
                            <p className="text-sm text-slate-400">
                              {service.description}
                            </p>
                            <div className="flex items-center space-x-4 text-sm">
                              <Badge variant="outline" className="text-amber-400 border-amber-400/30">
                                ${service.price}
                              </Badge>
                              <span className="text-slate-400 flex items-center">
                                <Clock className="w-3 h-3 mr-1" />
                                {service.duration}m
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          {/* What to Expect */}
          <Card className="glass-card mystical-border mt-6">
            <CardHeader>
              <CardTitle className="text-white text-lg">{t('services.whatToExpect')}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 text-sm">
              <div className="flex items-start space-x-3">
                <Star className="w-4 h-4 text-amber-400 mt-0.5" />
                <div>
                  <h4 className="font-medium text-white">{t('services.personalizedExperience')}</h4>
                  <p className="text-slate-400">{t('services.uniqueEnergy')}</p>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <Moon className="w-4 h-4 text-amber-400 mt-0.5" />
                <div>
                  <h4 className="font-medium text-white">{t('services.liveSession')}</h4>
                  <p className="text-slate-400">{t('services.realTimeReading')}</p>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <Sun className="w-4 h-4 text-amber-400 mt-0.5" />
                <div>
                  <h4 className="font-medium text-white">{t('services.recordingNotes')}</h4>
                  <p className="text-slate-400">{t('services.sessionNotes')}</p>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <Heart className="w-4 h-4 text-amber-400 mt-0.5" />
                <div>
                  <h4 className="font-medium text-white">{t('services.professionalGuidance')}</h4>
                  <p className="text-slate-400">{t('services.expertInterpretation')}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Booking Form */}
        <div className="lg:col-span-2">
          <Card className="glass-card mystical-border">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2 text-white">
                <Calendar className="w-5 h-5 text-amber-400" />
                <span>{t('services.scheduleSession')}</span>
              </CardTitle>
              <CardDescription className="text-slate-300">
                {t('services.liveMeet')}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-6">
                {/* Service Selection */}
                <div className="space-y-2">
                  <Label className="text-slate-200">{t('services.selectService')}</Label>
                  <Select 
                    value={sessionForm.service_type} 
                    onValueChange={handleServiceSelect}
                  >
                    <SelectTrigger className="form-input">
                      <SelectValue placeholder={t('services.chooseReading')} />
                    </SelectTrigger>
                    <SelectContent>
                      {services.map((service) => (
                        <SelectItem key={service.id} value={service.id}>
                          <div className="flex items-center justify-between w-full">
                            <span>{service.name}</span>
                            <span className="ml-2 text-amber-400">${service.price}</span>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Selected Service Info */}
                {selectedService && (
                  <Alert className="border-amber-500/50 bg-amber-500/10">
                    <DollarSign className="w-4 h-4 text-amber-400" />
                    <AlertDescription className="text-amber-400">
                      <div className="flex items-center justify-between">
                        <span>{selectedService.name}</span>
                        <div className="flex items-center space-x-4">
                          <span>${selectedService.price}</span>
                          <span className="text-sm">({selectedService.duration} {t('common.minutes')})</span>
                        </div>
                      </div>
                    </AlertDescription>
                  </Alert>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Preferred Date */}
                  <div className="space-y-2">
                    <Label htmlFor="preferred-date" className="text-slate-200">
                      {t('services.preferredDate')}
                    </Label>
                    <Input
                      id="preferred-date"
                      type="datetime-local"
                      value={sessionForm.start_at}
                      onChange={(e) => handleStartTimeChange(e.target.value)}
                      className="form-input"
                      min={new Date().toISOString().slice(0, 16)}
                      required
                    />
                  </div>

                  {/* End Time (Auto-calculated) */}
                  {sessionForm.end_at && (
                    <div className="space-y-2">
                      <Label className="text-slate-200">
                        {t('common.endTime')}
                      </Label>
                      <Input
                        type="datetime-local"
                        value={sessionForm.end_at}
                        className="form-input bg-slate-700/50"
                        disabled
                      />
                    </div>
                  )}
                </div>

                {/* Message */}
                <div className="space-y-2">
                  <Label htmlFor="message" className="text-slate-200">
                    {t('services.message')}
                  </Label>
                  <Textarea
                    id="message"
                    placeholder={t('services.shareQuestions')}
                    value={sessionForm.client_message}
                    onChange={(e) => setSessionForm({ ...sessionForm, client_message: e.target.value })}
                    className="form-input"
                    rows={4}
                  />
                </div>

                <Button 
                  type="submit" 
                  className="w-full btn-primary"
                  disabled={createSessionMutation.isPending}
                >
                  {createSessionMutation.isPending ? (
                    <div className="flex items-center space-x-2">
                      <div className="loading-spinner"></div>
                      <span>{t('common.submitting')}</span>
                    </div>
                  ) : (
                    <div className="flex items-center space-x-2">
                      <Calendar className="w-4 h-4" />
                      <span>{t('services.requestSession')}</span>
                    </div>
                  )}
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default TarotPage;