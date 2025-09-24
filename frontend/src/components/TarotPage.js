import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Textarea } from './ui/textarea';
import { Badge } from './ui/badge';
import { extractErrorMessage } from '../utils/errorHandler';
import { 
  Stars, 
  Calendar,
  Clock,
  Video,
  Sparkles,
  Moon,
  Sun,
  User,
  MessageSquare
} from 'lucide-react';
import { toast } from 'sonner';

const TarotPage = () => {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState('book');

  // Form state for booking sessions
  const [bookingForm, setBookingForm] = useState({
    service_type: '',
    preferred_date: '',
    preferred_time: '',
    message: '',
    duration: '60'
  });

  // Available services
  const services = [
    {
      id: 'tarot-reading',
      name: 'Personal Tarot Reading',
      duration: '60 minutes',
      description: 'In-depth tarot reading with personalized interpretations and guidance',
      price: '$85'
    },
    {
      id: 'birth-chart-reading',
      name: 'Birth Chart Analysis',
      duration: '90 minutes', 
      description: 'Complete natal chart reading with detailed planetary analysis',
      price: '$120'
    },
    {
      id: 'chart-tarot-combo',
      name: 'Birth Chart + Tarot Combo',
      duration: '120 minutes',
      description: 'Comprehensive session combining astrology and tarot insights',
      price: '$165'
    },
    {
      id: 'follow-up',
      name: 'Follow-up Session',
      duration: '30 minutes',
      description: 'Follow-up reading for previous clients',
      price: '$45'
    }
  ];

  // Create booking mutation
  const createBookingMutation = useMutation({
    mutationFn: (data) => {
      // For now, we'll create a session request
      const sessionData = {
        client_id: 'current-user', // This will be populated from auth
        service_type: data.service_type,
        start_at: new Date(`${data.preferred_date}T${data.preferred_time}`),
        end_at: new Date(`${data.preferred_date}T${data.preferred_time}`)
      };
      return axios.post('/sessions', sessionData);
    },
    onSuccess: () => {
      toast.success('Session request submitted! You will receive confirmation shortly.');
      queryClient.invalidateQueries(['sessions']);
      setBookingForm({
        service_type: '',
        preferred_date: '',
        preferred_time: '',
        message: '',
        duration: '60'
      });
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Failed to submit booking request');
    }
  });

  const handleBookingSubmit = (e) => {
    e.preventDefault();
    createBookingMutation.mutate(bookingForm);
  };

  const getServiceDetails = (serviceId) => {
    return services.find(s => s.id === serviceId);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <h1 className="font-serif text-3xl font-bold text-white mb-4 flex items-center justify-center">
          <Stars className="w-8 h-8 mr-3 text-purple-400" />
          Book Your Reading
        </h1>
        <p className="text-slate-400 max-w-2xl mx-auto">
          Schedule a personalized astrology or tarot session with professional guidance and insights.
        </p>
      </div>

      {/* Service Booking */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Booking Form */}
        <Card className="glass-card">
          <CardHeader>
            <CardTitle className="text-white font-serif flex items-center">
              <Calendar className="w-5 h-5 mr-2 text-purple-400" />
              Schedule Your Session
            </CardTitle>
            <CardDescription className="text-slate-400">
              Book a live reading session via Google Meet
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleBookingSubmit} className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="service_type" className="text-slate-200">
                  Select Service *
                </Label>
                <Select
                  value={bookingForm.service_type}
                  onValueChange={(value) => setBookingForm({ ...bookingForm, service_type: value })}
                >
                  <SelectTrigger className="form-input" data-testid="service-type-select">
                    <SelectValue placeholder="Choose your reading type" />
                  </SelectTrigger>
                  <SelectContent className="bg-slate-800 border-slate-600">
                    {services.map((service) => (
                      <SelectItem key={service.id} value={service.id}>
                        {service.name} - {service.duration}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {bookingForm.service_type && (
                <div className="p-4 rounded-lg bg-purple-500/10 border border-purple-500/20">
                  {(() => {
                    const service = getServiceDetails(bookingForm.service_type);
                    return service ? (
                      <div>
                        <h4 className="font-medium text-purple-300 mb-2">{service.name}</h4>
                        <div className="text-sm space-y-1">
                          <div className="flex items-center text-slate-300">
                            <Clock className="w-3 h-3 mr-2" />
                            Duration: {service.duration}
                          </div>
                          <div className="flex items-center text-slate-300">
                            <Video className="w-3 h-3 mr-2" />
                            Live session via Google Meet
                          </div>
                          <div className="flex items-center text-amber-300">
                            <span className="font-medium">Investment: {service.price}</span>
                          </div>
                        </div>
                        <p className="text-xs text-slate-400 mt-2">{service.description}</p>
                      </div>
                    ) : null;
                  })()}
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="preferred_date" className="text-slate-200">
                    Preferred Date *
                  </Label>
                  <Input
                    id="preferred_date"
                    type="date"
                    value={bookingForm.preferred_date}
                    onChange={(e) => setBookingForm({ ...bookingForm, preferred_date: e.target.value })}
                    className="form-input"
                    data-testid="preferred-date-input"
                    min={new Date().toISOString().split('T')[0]}
                    required
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="preferred_time" className="text-slate-200">
                    Preferred Time *
                  </Label>
                  <Select
                    value={bookingForm.preferred_time}
                    onValueChange={(value) => setBookingForm({ ...bookingForm, preferred_time: value })}
                  >
                    <SelectTrigger className="form-input" data-testid="preferred-time-select">
                      <SelectValue placeholder="Choose time" />
                    </SelectTrigger>
                    <SelectContent className="bg-slate-800 border-slate-600">
                      <SelectItem value="09:00">9:00 AM</SelectItem>
                      <SelectItem value="10:00">10:00 AM</SelectItem>
                      <SelectItem value="11:00">11:00 AM</SelectItem>
                      <SelectItem value="12:00">12:00 PM</SelectItem>
                      <SelectItem value="13:00">1:00 PM</SelectItem>
                      <SelectItem value="14:00">2:00 PM</SelectItem>
                      <SelectItem value="15:00">3:00 PM</SelectItem>
                      <SelectItem value="16:00">4:00 PM</SelectItem>
                      <SelectItem value="17:00">5:00 PM</SelectItem>
                      <SelectItem value="18:00">6:00 PM</SelectItem>
                      <SelectItem value="19:00">7:00 PM</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="message" className="text-slate-200">
                  Message (Optional)
                </Label>
                <Textarea
                  id="message"
                  placeholder="Share any specific questions or areas you'd like to explore..."
                  value={bookingForm.message}
                  onChange={(e) => setBookingForm({ ...bookingForm, message: e.target.value })}
                  className="form-input min-h-[100px]"
                  data-testid="message-textarea"
                />
              </div>

              <Button
                type="submit"
                className="w-full btn-primary"
                disabled={createBookingMutation.isPending}
                data-testid="submit-booking-button"
              >
                {createBookingMutation.isPending ? (
                  <div className="flex items-center space-x-2">
                    <div className="loading-spinner"></div>
                    <span>Submitting request...</span>
                  </div>
                ) : (
                  <>
                    <Calendar className="w-4 h-4 mr-2" />
                    Request Session
                  </>
                )}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Services Overview */}
        <div className="space-y-6">
          <Card className="glass-card">
            <CardHeader>
              <CardTitle className="text-white font-serif flex items-center">
                <Sparkles className="w-5 h-5 mr-2 text-amber-400" />
                Available Services
              </CardTitle>
              <CardDescription className="text-slate-400">
                Professional readings tailored to your needs
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {services.map((service) => (
                  <div 
                    key={service.id}
                    className="p-4 rounded-lg bg-slate-800/30 border border-slate-600/30 hover:border-purple-500/40 transition-all"
                  >
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="font-medium text-white">{service.name}</h3>
                      <Badge className="bg-amber-500/20 text-amber-400 border-amber-500/30">
                        {service.price}
                      </Badge>
                    </div>
                    <div className="flex items-center space-x-4 text-sm text-slate-400 mb-2">
                      <span className="flex items-center">
                        <Clock className="w-3 h-3 mr-1" />
                        {service.duration}
                      </span>
                      <span className="flex items-center">
                        <Video className="w-3 h-3 mr-1" />
                        Google Meet
                      </span>
                    </div>
                    <p className="text-xs text-slate-300">{service.description}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card className="glass-card">
            <CardHeader>
              <CardTitle className="text-white font-serif flex items-center">
                <Moon className="w-5 h-5 mr-2 text-blue-400" />
                What to Expect
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/20">
                  <h4 className="text-sm font-medium text-blue-300 mb-1 flex items-center">
                    <User className="w-3 h-3 mr-2" />
                    Personalized Experience
                  </h4>
                  <p className="text-xs text-slate-300">
                    Each session is tailored to your unique energy and questions.
                  </p>
                </div>

                <div className="p-3 rounded-lg bg-purple-500/10 border border-purple-500/20">
                  <h4 className="text-sm font-medium text-purple-300 mb-1 flex items-center">
                    <Video className="w-3 h-3 mr-2" />
                    Live Interactive Session
                  </h4>
                  <p className="text-xs text-slate-300">
                    Real-time reading via Google Meet with screen sharing and discussion.
                  </p>
                </div>

                <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                  <h4 className="text-sm font-medium text-emerald-300 mb-1 flex items-center">
                    <MessageSquare className="w-3 h-3 mr-2" />
                    Recording & Notes
                  </h4>
                  <p className="text-xs text-slate-300">
                    Receive session notes and key insights for future reference.
                  </p>
                </div>

                <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
                  <h4 className="text-sm font-medium text-amber-300 mb-1 flex items-center">
                    <Stars className="w-3 h-3 mr-2" />
                    Professional Guidance
                  </h4>
                  <p className="text-xs text-slate-300">
                    Expert interpretation with compassionate, insightful guidance.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default TarotPage;