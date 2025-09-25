import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Alert, AlertDescription } from './ui/alert';
import { Badge } from './ui/badge';
import { extractErrorMessage } from '../utils/errorHandler';
import { 
  Sparkles, 
  Calendar,
  MapPin, 
  Clock,
  Star,
  Stars,
  Moon,
  Sun,
  Plus
} from 'lucide-react';
import { toast } from 'sonner';

const AstrologyPage = () => {
  const queryClient = useQueryClient();
  const { t } = useTranslation();
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
        console.error('Error fetching birth data:', error);
        return [];
      }
    }
  });

  // Fetch charts
  const { data: charts = [], isLoading: chartsLoading } = useQuery({
    queryKey: ['charts'],
    queryFn: async () => {
      try {
        const response = await axios.get('/auth/me');
        const userId = response.data.id;
        const chartsResponse = await axios.get(`/astrology/charts/${userId}`);
        return chartsResponse.data;
      } catch (error) {
        console.error('Error fetching charts:', error);
        return [];
      }
    }
  });

  // Save birth data mutation
  const saveBirthDataMutation = useMutation({
    mutationFn: async (birthData) => {
      const response = await axios.post('/birth-data', birthData);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['birth-data']);
      setBirthForm({
        birth_date: '',
        birth_time: '',
        time_accuracy: 'exact',
        birth_place: '',
        latitude: '',
        longitude: ''
      });
      toast.success(t('common.save') + ' ' + t('common.success'));
    },
    onError: (error) => {
      const errorMessage = extractErrorMessage(error);
      toast.error(errorMessage);
    }
  });

  // Mutation for generating chart map
  const generateMapMutation = useMutation({
    mutationFn: async (chartId) => {
      const response = await axios.post(`/charts/${chartId}/generate-map`);
      return { chartId, ...response.data };
    },
    onSuccess: (data) => {
      // Invalidate and refetch charts to get updated SVG content
      queryClient.invalidateQueries(['charts']);
      
      if (data.has_svg) {
        toast.success('Astrological map generated successfully! View it below the chart data.');
      } else {
        toast.error('Failed to generate map - please try again.');
      }
    },
    onError: (error) => {
      toast.error(`Failed to generate map: ${extractErrorMessage(error)}`);
    }
  });

  // Generate chart mutation
  const generateChartMutation = useMutation({
    mutationFn: async (birthDataId) => {
      const response = await axios.post(`/astrology/chart?birth_data_id=${birthDataId}`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['charts']);
      toast.success(t('astrology.generateChart') + ' ' + t('common.success'));
    },
    onError: (error) => {
      const errorMessage = extractErrorMessage(error);
      toast.error(errorMessage);
    }
  });

  const handleSaveBirthData = (e) => {
    e.preventDefault();
    saveBirthDataMutation.mutate(birthForm);
  };

  const handleGenerateChart = (birthDataId) => {
    generateChartMutation.mutate(birthDataId);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center space-y-4">
        <div className="flex justify-center items-center space-x-3">
          <div className="w-12 h-12 rounded-full bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center animate-mystical-glow">
            <Sparkles className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-white font-mystical">
            {t('astrology.portal')}
          </h1>
        </div>
        <p className="text-slate-300 max-w-2xl mx-auto">
          {t('astrology.generateCharts')}
        </p>
      </div>

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-3 bg-slate-800/50 border border-slate-600/30 rounded-lg p-1">
          <TabsTrigger 
            value="create" 
            className="data-[state=active]:bg-amber-500/20 data-[state=active]:text-amber-400 transition-all duration-200 rounded-md"
          >
            <Plus className="w-4 h-4 mr-2" />
            {t('astrology.addBirthData')}
          </TabsTrigger>
          <TabsTrigger 
            value="generate" 
            className="data-[state=active]:bg-amber-500/20 data-[state=active]:text-amber-400 transition-all duration-200 rounded-md"
          >
            <Star className="w-4 h-4 mr-2" />
            {t('astrology.generateChart')}
          </TabsTrigger>
          <TabsTrigger 
            value="charts" 
            className="data-[state=active]:bg-amber-500/20 data-[state=active]:text-amber-400 transition-all duration-200 rounded-md"
          >
            <Calendar className="w-4 h-4 mr-2" />
            {t('astrology.myCharts')}
          </TabsTrigger>
        </TabsList>

        {/* Create Birth Data Tab */}
        <TabsContent value="create" className="mt-6">
          <Card className="glass-card mystical-border">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2 text-white">
                <Sparkles className="w-5 h-5 text-amber-400" />
                <span>{t('astrology.birthInformation')}</span>
              </CardTitle>
              <CardDescription className="text-slate-300">
                {t('astrology.preciseBirthDetails')}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSaveBirthData} className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Birth Date */}
                  <div className="space-y-2">
                    <Label htmlFor="birth-date" className="text-slate-200 flex items-center">
                      <Calendar className="w-4 h-4 mr-2 text-amber-400" />
                      {t('astrology.birthDate')}
                    </Label>
                    <Input
                      id="birth-date"
                      type="date"
                      value={birthForm.birth_date}
                      onChange={(e) => setBirthForm({ ...birthForm, birth_date: e.target.value })}
                      className="form-input"
                      required
                    />
                  </div>

                  {/* Birth Time */}
                  <div className="space-y-2">
                    <Label htmlFor="birth-time" className="text-slate-200 flex items-center">
                      <Clock className="w-4 h-4 mr-2 text-amber-400" />
                      {t('astrology.birthTime')}
                    </Label>
                    <Input
                      id="birth-time"
                      type="time"
                      value={birthForm.birth_time}
                      onChange={(e) => setBirthForm({ ...birthForm, birth_time: e.target.value })}
                      className="form-input"
                    />
                  </div>

                  {/* Time Accuracy */}
                  <div className="space-y-2">
                    <Label className="text-slate-200">{t('astrology.timeAccuracy')}</Label>
                    <Select value={birthForm.time_accuracy} onValueChange={(value) => setBirthForm({ ...birthForm, time_accuracy: value })}>
                      <SelectTrigger className="form-input">
                        <SelectValue placeholder={t('astrology.selectTimeAccuracy')} />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="exact">{t('astrology.exactTime')}</SelectItem>
                        <SelectItem value="approx">{t('astrology.approxTime')}</SelectItem>
                        <SelectItem value="unknown">{t('astrology.timeUnknown')}</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Birth Place */}
                  <div className="space-y-2">
                    <Label htmlFor="birth-place" className="text-slate-200 flex items-center">
                      <MapPin className="w-4 h-4 mr-2 text-amber-400" />
                      {t('astrology.birthPlace')}
                    </Label>
                    <Input
                      id="birth-place"
                      type="text"
                      placeholder={t('astrology.enterBirthPlace')}
                      value={birthForm.birth_place}
                      onChange={(e) => setBirthForm({ ...birthForm, birth_place: e.target.value })}
                      className="form-input"
                      required
                    />
                  </div>
                </div>

                <div className="space-y-3">
                  <p className="text-sm text-slate-400">
                    {t('astrology.enterLocation')}
                  </p>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Latitude */}
                    <div className="space-y-2">
                      <Label htmlFor="latitude" className="text-slate-200">
                        {t('astrology.latitude')}
                      </Label>
                      <Input
                        id="latitude"
                        type="text"
                        placeholder="e.g., 40.7128"
                        value={birthForm.latitude}
                        onChange={(e) => setBirthForm({ ...birthForm, latitude: e.target.value })}
                        className="form-input"
                      />
                    </div>

                    {/* Longitude */}
                    <div className="space-y-2">
                      <Label htmlFor="longitude" className="text-slate-200">
                        {t('astrology.longitude')}
                      </Label>
                      <Input
                        id="longitude"
                        type="text"
                        placeholder="e.g., -74.0060"
                        value={birthForm.longitude}
                        onChange={(e) => setBirthForm({ ...birthForm, longitude: e.target.value })}
                        className="form-input"
                      />
                    </div>
                  </div>
                </div>

                <Button 
                  type="submit" 
                  className="w-full btn-primary"
                  disabled={saveBirthDataMutation.isPending}
                >
                  {saveBirthDataMutation.isPending ? (
                    <div className="flex items-center space-x-2">
                      <div className="loading-spinner"></div>
                      <span>{t('astrology.saving')}</span>
                    </div>
                  ) : (
                    <div className="flex items-center space-x-2">
                      <Sparkles className="w-4 h-4" />
                      <span>{t('astrology.saveBirthData')}</span>
                    </div>
                  )}
                </Button>
              </form>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Generate Chart Tab */}
        <TabsContent value="generate" className="mt-6">
          <Card className="glass-card mystical-border">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2 text-white">
                <Star className="w-5 h-5 text-amber-400" />
                <span>{t('astrology.generateChart')}</span>
              </CardTitle>
              <CardDescription className="text-slate-300">
                {t('astrology.selectBirthData')}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {birthDataLoading ? (
                <div className="text-center py-8">
                  <div className="loading-spinner mx-auto mb-4"></div>
                  <p className="text-slate-400">{t('common.loading')}</p>
                </div>
              ) : birthDataList.length === 0 ? (
                <Alert className="border-amber-500/50 bg-amber-500/10">
                  <AlertDescription className="text-amber-400">
                    {t('astrology.noBirthData')}
                  </AlertDescription>
                </Alert>
              ) : (
                <div className="grid gap-4">
                  {birthDataList.map((birthData, index) => (
                    <Card key={birthData.id} className="glass-card border-slate-600/30 hover:border-amber-400/50 transition-colors">
                      <CardContent className="pt-6">
                        <div className="flex items-center justify-between">
                          <div className="space-y-2">
                            <div className="flex items-center space-x-2">
                              <Calendar className="w-4 h-4 text-amber-400" />
                              <span className="text-white font-medium">
                                {new Date(birthData.birth_date).toLocaleDateString()}
                              </span>
                              {birthData.birth_time && (
                                <>
                                  <Clock className="w-4 h-4 text-amber-400 ml-4" />
                                  <span className="text-slate-300">{birthData.birth_time}</span>
                                </>
                              )}
                            </div>
                            <div className="flex items-center space-x-2">
                              <MapPin className="w-4 h-4 text-amber-400" />
                              <span className="text-slate-300">{birthData.birth_place}</span>
                            </div>
                            <Badge variant="secondary" className="bg-slate-700/50 text-slate-300">
                              {birthData.time_accuracy}
                            </Badge>
                          </div>
                          <Button
                            onClick={() => handleGenerateChart(birthData.id)}
                            className="btn-primary"
                            disabled={generateChartMutation.isPending}
                          >
                            {generateChartMutation.isPending ? (
                              <div className="flex items-center space-x-2">
                                <div className="loading-spinner"></div>
                                <span>{t('astrology.generating')}</span>
                              </div>
                            ) : (
                              <div className="flex items-center space-x-2">
                                <Star className="w-4 h-4" />
                                <span>{t('astrology.generateChart')}</span>
                              </div>
                            )}
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Charts Tab */}
        <TabsContent value="charts" className="mt-6">
          <Card className="glass-card mystical-border">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2 text-white">
                <Calendar className="w-5 h-5 text-amber-400" />
                <span>{t('astrology.myCharts')}</span>
              </CardTitle>
              <CardDescription className="text-slate-300">
                {t('astrology.generatedOn')}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {chartsLoading ? (
                <div className="text-center py-8">
                  <div className="loading-spinner mx-auto mb-4"></div>
                  <p className="text-slate-400">{t('common.loading')}</p>
                </div>
              ) : charts.length === 0 ? (
                <div className="text-center py-12">
                  <Stars className="w-16 h-16 text-slate-600 mx-auto mb-4" />
                  <h3 className="text-xl font-semibold text-slate-300 mb-2">
                    {t('astrology.noCharts')}
                  </h3>
                  <p className="text-slate-400 mb-6">
                    {t('astrology.generateFirst')}
                  </p>
                  <Button 
                    onClick={() => setActiveTab('create')}
                    className="btn-primary"
                  >
                    <Plus className="w-4 h-4 mr-2" />
                    {t('astrology.addBirthData')}
                  </Button>
                </div>
              ) : (
                <div className="grid gap-6">
                  {charts.map((chart) => (
                    <Card key={chart.id} className="glass-card border-slate-600/30">
                      <CardContent className="pt-6">
                        <div className="space-y-4">
                          <div className="flex items-center justify-between">
                            <h3 className="text-lg font-semibold text-white">
                              {t('astrology.natalChart')}
                            </h3>
                            <div className="flex items-center space-x-3">
                              <Badge variant="secondary" className="bg-amber-500/20 text-amber-400">
                                {new Date(chart.created_at).toLocaleDateString()}
                              </Badge>
                              <div className="flex space-x-2">
                                <Button
                                  onClick={() => generateMapMutation.mutate(chart.id)}
                                  disabled={generateMapMutation.isPending}
                                  variant="outline"
                                  size="sm"
                                  className="text-emerald-400 border-emerald-400/50 hover:bg-emerald-400/10"
                                >
                                  {generateMapMutation.isPending ? (
                                    <>
                                      <div className="loading-spinner w-4 h-4 mr-2"></div>
                                      Generating...
                                    </>
                                  ) : (
                                    <>
                                      <Stars className="w-4 h-4 mr-2" />
                                      {chart.chart_svg ? 'Regenerate Map' : 'Generate Map'}
                                    </>
                                  )}
                                </Button>
                              </div>
                            </div>
                          </div>

                          {/* Planetary Positions */}
                          <div className="space-y-3">
                            <h4 className="font-medium text-amber-400 flex items-center">
                              <Sun className="w-4 h-4 mr-2" />
                              {t('astrology.planetaryPositions')}
                            </h4>
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                              {Object.entries(chart.planets || {}).map(([planet, data]) => (
                                <div key={planet} className="bg-slate-800/30 rounded-lg p-3 border border-slate-600/30">
                                  <div className="flex items-center justify-between">
                                    <span className="font-medium text-white">{planet}</span>
                                    <Badge variant="outline" className="text-xs">
                                      {data.sign}
                                    </Badge>
                                  </div>
                                  <div className="text-xs text-slate-400 mt-1">
                                    {data.longitude?.toFixed(2)}° {data.house && `• House ${data.house}`}
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>

                          {/* House Cusps */}
                          <div className="space-y-3">
                            <h4 className="font-medium text-amber-400 flex items-center">
                              <Moon className="w-4 h-4 mr-2" />
                              {t('astrology.houseCusps')}
                            </h4>
                            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
                              {Object.entries(chart.houses || {}).map(([house, data]) => (
                                <div key={house} className="bg-slate-800/30 rounded-lg p-3 border border-slate-600/30 text-center">
                                  <div className="font-medium text-white text-sm">
                                    {house.replace('house_', 'H')}
                                  </div>
                                  <div className="text-xs text-amber-400">{data.sign}</div>
                                  <div className="text-xs text-slate-400">
                                    {data.cusp?.toFixed(1)}°
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>

                          {/* Astrological Map */}
                          {chart.chart_svg && (
                            <div className="space-y-3">
                              <h4 className="font-medium text-amber-400 flex items-center">
                                <Stars className="w-4 h-4 mr-2" />
                                Astrological Map
                              </h4>
                              <div className="bg-slate-800/30 rounded-lg p-4 border border-slate-600/30">
                                <div 
                                  className="w-full overflow-auto"
                                  style={{ maxHeight: '600px' }}
                                  dangerouslySetInnerHTML={{ __html: chart.chart_svg }}
                                />
                              </div>
                            </div>
                          )}
                        </div>
                      </CardContent>
                    </Card>
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

export default AstrologyPage;