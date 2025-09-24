import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Alert, AlertDescription } from './ui/alert';
import { Badge } from './ui/badge';
import PlacesAutocomplete from './PlacesAutocomplete';
import { 
  Sparkles, 
  Calendar,
  MapPin, 
  Clock,
  Star,
  Moon,
  Sun,
  Plus
} from 'lucide-react';
import { toast } from 'sonner';

const AstrologyPage = () => {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState('create');

  // Form state for birth data
  const [birthForm, setBirthForm] = useState({
    birth_date: '',
    birth_time: '',
    time_accuracy: 'exact',
    birth_place: '',
    latitude: '',
    longitude: ''
  });

  const [selectedBirthData, setSelectedBirthData] = useState(null);

  // Fetch user's birth data
  const { data: birthDataList = [], isLoading: birthDataLoading } = useQuery({
    queryKey: ['birth-data'],
    queryFn: async () => {
      try {
        // For now, fetch current user's birth data
        const response = await axios.get('/auth/me');
        const userId = response.data.id;
        const birthDataResponse = await axios.get(`/birth-data/${userId}`);
        return birthDataResponse.data;
      } catch (error) {
        return [];
      }
    }
  });

  // Fetch user's charts
  const { data: charts = [], isLoading: chartsLoading } = useQuery({
    queryKey: ['charts'],
    queryFn: async () => {
      try {
        const response = await axios.get('/auth/me');
        const userId = response.data.id;
        const chartsResponse = await axios.get(`/astrology/charts/${userId}`);
        return chartsResponse.data;
      } catch (error) {
        return [];
      }
    }
  });

  // Create birth data mutation
  const createBirthDataMutation = useMutation({
    mutationFn: (data) => axios.post('/birth-data', data),
    onSuccess: (response) => {
      toast.success('Birth data saved successfully!');
      queryClient.invalidateQueries(['birth-data']);
      setBirthForm({
        birth_date: '',
        birth_time: '',
        time_accuracy: 'exact',
        birth_place: '',
        latitude: '',
        longitude: ''
      });
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Failed to save birth data');
    }
  });

  // Generate chart mutation
  const generateChartMutation = useMutation({
    mutationFn: (birthDataId) => axios.post(`/astrology/chart?birth_data_id=${birthDataId}`),
    onSuccess: (response) => {
      toast.success('Birth chart generated successfully!');
      queryClient.invalidateQueries(['charts']);
      setActiveTab('charts');
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Failed to generate chart');
    }
  });

  const handleBirthFormSubmit = (e) => {
    e.preventDefault();
    createBirthDataMutation.mutate(birthForm);
  };

  const handleGenerateChart = (birthDataId) => {
    generateChartMutation.mutate(birthDataId);
  };

  const formatPlanetPosition = (planet) => {
    const signs = [
      'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
      'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
    ];
    
    const degree = Math.floor(planet.longitude);
    const signIndex = Math.floor(planet.longitude / 30);
    const signDegree = Math.floor(planet.longitude % 30);
    
    return `${degree}° ${signs[signIndex]} ${signDegree}°`;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <h1 className="font-serif text-3xl font-bold text-white mb-4 flex items-center justify-center">
          <Sparkles className="w-8 h-8 mr-3 text-amber-400" />
          Astrology Portal
        </h1>
        <p className="text-slate-400 max-w-2xl mx-auto">
          Generate precise natal charts and explore the celestial influences that shaped your birth moment.
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-3 bg-slate-800/50">
          <TabsTrigger 
            value="create" 
            className="data-[state=active]:bg-amber-500/20 data-[state=active]:text-amber-400"
            data-testid="create-birth-data-tab"
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Birth Data
          </TabsTrigger>
          <TabsTrigger 
            value="generate" 
            className="data-[state=active]:bg-amber-500/20 data-[state=active]:text-amber-400"
            data-testid="generate-chart-tab"
          >
            <Star className="w-4 h-4 mr-2" />
            Generate Chart
          </TabsTrigger>
          <TabsTrigger 
            value="charts" 
            className="data-[state=active]:bg-amber-500/20 data-[state=active]:text-amber-400"
            data-testid="view-charts-tab"
          >
            <Sun className="w-4 h-4 mr-2" />
            My Charts
          </TabsTrigger>
        </TabsList>

        {/* Create Birth Data Tab */}
        <TabsContent value="create">
          <Card className="glass-card">
            <CardHeader>
              <CardTitle className="text-white font-serif flex items-center">
                <Calendar className="w-5 h-5 mr-2 text-amber-400" />
                Birth Information
              </CardTitle>
              <CardDescription className="text-slate-400">
                Enter precise birth details for accurate astrological calculations
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleBirthFormSubmit} className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="birth_date" className="text-slate-200">
                      Birth Date *
                    </Label>
                    <Input
                      id="birth_date"
                      type="date"
                      value={birthForm.birth_date}
                      onChange={(e) => setBirthForm({ ...birthForm, birth_date: e.target.value })}
                      className="form-input"
                      data-testid="birth-date-input"
                      required
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="birth_time" className="text-slate-200">
                      Birth Time
                    </Label>
                    <Input
                      id="birth_time"
                      type="time"
                      value={birthForm.birth_time}
                      onChange={(e) => setBirthForm({ ...birthForm, birth_time: e.target.value })}
                      className="form-input"
                      data-testid="birth-time-input"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="time_accuracy" className="text-slate-200">
                    Time Accuracy
                  </Label>
                  <Select
                    value={birthForm.time_accuracy}
                    onValueChange={(value) => setBirthForm({ ...birthForm, time_accuracy: value })}
                  >
                    <SelectTrigger className="form-input" data-testid="time-accuracy-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-slate-800 border-slate-600">
                      <SelectItem value="exact">Exact time known</SelectItem>
                      <SelectItem value="approx">Approximate time</SelectItem>
                      <SelectItem value="unknown">Time unknown</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="birth_place" className="text-slate-200 flex items-center">
                    <MapPin className="w-4 h-4 mr-1" />
                    Birth Place *
                  </Label>
                  <Input
                    id="birth_place"
                    type="text"
                    placeholder="City, State, Country"
                    value={birthForm.birth_place}
                    onChange={(e) => setBirthForm({ ...birthForm, birth_place: e.target.value })}
                    className="form-input"
                    data-testid="birth-place-input"
                    required
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="latitude" className="text-slate-200">
                      Latitude (Optional)
                    </Label>
                    <Input
                      id="latitude"
                      type="number"
                      step="any"
                      placeholder="e.g., 40.7128"
                      value={birthForm.latitude}
                      onChange={(e) => setBirthForm({ ...birthForm, latitude: e.target.value })}
                      className="form-input"
                      data-testid="latitude-input"
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="longitude" className="text-slate-200">
                      Longitude (Optional)
                    </Label>
                    <Input
                      id="longitude"
                      type="number"
                      step="any"
                      placeholder="e.g., -74.0060"
                      value={birthForm.longitude}
                      onChange={(e) => setBirthForm({ ...birthForm, longitude: e.target.value })}
                      className="form-input"
                      data-testid="longitude-input"
                    />
                  </div>
                </div>

                <Button
                  type="submit"
                  className="btn-primary w-full"
                  disabled={createBirthDataMutation.isPending}
                  data-testid="save-birth-data-button"
                >
                  {createBirthDataMutation.isPending ? (
                    <div className="flex items-center space-x-2">
                      <div className="loading-spinner"></div>
                      <span>Saving birth data...</span>
                    </div>
                  ) : (
                    <>
                      <Star className="w-4 h-4 mr-2" />
                      Save Birth Data
                    </>
                  )}
                </Button>
              </form>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Generate Chart Tab */}
        <TabsContent value="generate">
          <Card className="glass-card">
            <CardHeader>
              <CardTitle className="text-white font-serif flex items-center">
                <Star className="w-5 h-5 mr-2 text-amber-400" />
                Generate Birth Chart
              </CardTitle>
              <CardDescription className="text-slate-400">
                Select birth data to generate a detailed astrological chart
              </CardDescription>
            </CardHeader>
            <CardContent>
              {birthDataLoading ? (
                <div className="space-y-4">
                  {[1, 2].map(i => (
                    <div key={i} className="animate-pulse p-4 rounded-lg bg-slate-700/30">
                      <div className="h-4 bg-slate-600/50 rounded mb-2"></div>
                      <div className="h-3 bg-slate-600/30 rounded w-3/4"></div>
                    </div>
                  ))}
                </div>
              ) : birthDataList.length > 0 ? (
                <div className="space-y-4">
                  {birthDataList.map((birthData) => (
                    <div 
                      key={birthData.id} 
                      className="p-4 rounded-lg bg-slate-800/30 border border-slate-600/30 hover:border-amber-500/50 transition-all"
                    >
                      <div className="flex justify-between items-start">
                        <div className="space-y-2">
                          <h3 className="font-medium text-white flex items-center">
                            <Calendar className="w-4 h-4 mr-2 text-amber-400" />
                            {birthData.birth_date}
                            {birthData.birth_time && (
                              <>
                                <Clock className="w-4 h-4 ml-4 mr-1 text-blue-400" />
                                {birthData.birth_time}
                              </>
                            )}
                          </h3>
                          <p className="text-sm text-slate-400 flex items-center">
                            <MapPin className="w-3 h-3 mr-1" />
                            {birthData.birth_place}
                          </p>
                          <div className="flex items-center space-x-2">
                            <Badge variant="outline" className="text-xs">
                              {birthData.time_accuracy}
                            </Badge>
                          </div>
                        </div>
                        <Button
                          onClick={() => handleGenerateChart(birthData.id)}
                          disabled={generateChartMutation.isPending}
                          className="btn-primary"
                          data-testid={`generate-chart-button-${birthData.id}`}
                        >
                          {generateChartMutation.isPending ? (
                            <div className="loading-spinner w-4 h-4"></div>
                          ) : (
                            <>
                              <Sparkles className="w-4 h-4 mr-2" />
                              Generate Chart
                            </>
                          )}
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <Alert className="border-amber-500/50 bg-amber-500/10">
                  <Star className="w-4 h-4 text-amber-400" />
                  <AlertDescription className="text-amber-200">
                    No birth data found. Please add your birth information first.
                  </AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Charts Tab */}
        <TabsContent value="charts">
          <div className="space-y-4">
            {chartsLoading ? (
              <Card className="glass-card">
                <CardContent className="p-6">
                  <div className="animate-pulse space-y-4">
                    <div className="h-6 bg-slate-600/50 rounded w-1/4"></div>
                    <div className="grid grid-cols-3 gap-4">
                      {[1, 2, 3].map(i => (
                        <div key={i} className="h-20 bg-slate-600/30 rounded"></div>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ) : charts.length > 0 ? (
              charts.map((chart) => (
                <Card key={chart.id} className="glass-card">
                  <CardHeader>
                    <CardTitle className="text-white font-serif flex items-center">
                      <Sun className="w-5 h-5 mr-2 text-amber-400" />
                      Natal Chart - {chart.birth_data.birth_date}
                    </CardTitle>
                    <CardDescription className="text-slate-400">
                      Generated on {new Date(chart.created_at).toLocaleDateString()}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      {/* Planets */}
                      <div>
                        <h4 className="font-semibold text-white mb-4 flex items-center">
                          <Star className="w-4 h-4 mr-2 text-purple-400" />
                          Planetary Positions
                        </h4>
                        <div className="space-y-2">
                          {Object.entries(chart.planets).map(([name, planet]) => (
                            <div 
                              key={name} 
                              className="flex justify-between items-center p-2 rounded bg-slate-800/30"
                            >
                              <span className="text-slate-200 capitalize">{name}</span>
                              <div className="text-right">
                                <span className="text-amber-400 font-mono text-sm">
                                  {formatPlanetPosition(planet)}
                                </span>
                                <div className="text-xs text-slate-400">
                                  {planet.sign}
                                  {planet.house && ` • House ${planet.house}`}
                                  {planet.retrograde && ' • R'}
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Houses */}
                      <div>
                        <h4 className="font-semibold text-white mb-4 flex items-center">
                          <Moon className="w-4 h-4 mr-2 text-blue-400" />
                          House Cusps
                        </h4>
                        <div className="space-y-2">
                          {Object.entries(chart.houses).map(([houseName, house]) => {
                            const houseNumber = houseName.replace('house_', '');
                            return (
                              <div 
                                key={houseName} 
                                className="flex justify-between items-center p-2 rounded bg-slate-800/30"
                              >
                                <span className="text-slate-200">House {houseNumber}</span>
                                <div className="text-right">
                                  <span className="text-blue-400 font-mono text-sm">
                                    {Math.floor(house.cusp)}°
                                  </span>
                                  <div className="text-xs text-slate-400">
                                    {house.sign}
                                  </div>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))
            ) : (
              <Card className="glass-card">
                <CardContent className="p-6 text-center">
                  <Sun className="w-12 h-12 mx-auto mb-4 text-slate-400 opacity-50" />
                  <h3 className="text-white font-medium mb-2">No Charts Generated</h3>
                  <p className="text-slate-400 mb-4">
                    Generate your first birth chart to see planetary positions and aspects.
                  </p>
                  <Button 
                    onClick={() => setActiveTab('generate')}
                    className="btn-primary"
                  >
                    Generate Chart
                  </Button>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AstrologyPage;