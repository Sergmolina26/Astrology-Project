import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Badge } from './ui/badge';
import { 
  Stars, 
  Shuffle, 
  Eye,
  RotateCcw,
  Sparkles,
  Moon,
  Sun
} from 'lucide-react';
import { toast } from 'sonner';

const TarotPage = () => {
  const queryClient = useQueryClient();
  const [selectedSpread, setSelectedSpread] = useState('');
  const [activeTab, setActiveTab] = useState('draw');

  // Fetch tarot spreads
  const { data: spreads = [], isLoading: spreadsLoading } = useQuery({
    queryKey: ['tarot-spreads'],
    queryFn: () => axios.get('/tarot/spreads').then(res => res.data)
  });

  // Fetch tarot cards
  const { data: cards = [], isLoading: cardsLoading } = useQuery({
    queryKey: ['tarot-cards'],
    queryFn: () => axios.get('/tarot/cards').then(res => res.data)
  });

  // Create reading mutation
  const createReadingMutation = useMutation({
    mutationFn: (spreadId) => axios.post('/tarot/reading', {}, {
      params: { spread_id: spreadId }
    }),
    onSuccess: (response) => {
      toast.success('Cards drawn! The universe has spoken.');
      queryClient.invalidateQueries(['tarot-readings']);
      setActiveTab('readings');
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Failed to draw cards');
    }
  });

  // Fetch readings (mock for now)
  const { data: readings = [], isLoading: readingsLoading } = useQuery({
    queryKey: ['tarot-readings'],
    queryFn: async () => {
      // Since we don't have a specific endpoint to get user readings, we'll mock this
      return [];
    }
  });

  const handleDrawCards = () => {
    if (!selectedSpread) {
      toast.error('Please select a spread first');
      return;
    }
    createReadingMutation.mutate(selectedSpread);
  };

  const getCardMeaning = (cardId, isReversed) => {
    const card = cards.find(c => c.id === cardId);
    if (!card) return 'Card meaning not found';
    return isReversed ? card.reversed_meaning : card.upright_meaning;
  };

  const CardDisplay = ({ card, position }) => (
    <div className="group relative">
      <div className={`
        w-24 h-36 md:w-32 md:h-48 rounded-lg border-2 border-amber-400/30 
        bg-gradient-to-b from-slate-800 to-slate-900 
        flex flex-col items-center justify-center p-2 
        hover:border-amber-400/60 transition-all duration-300
        ${card.is_reversed ? 'rotate-180' : ''}
        card-hover
      `}>
        <div className="text-center space-y-2">
          <Stars className="w-6 h-6 mx-auto text-amber-400" />
          <div className="text-xs font-medium text-white">
            {card.card_name}
          </div>
          {card.is_reversed && (
            <Badge variant="outline" className="text-xs">
              <RotateCcw className="w-3 h-3 mr-1" />
              Reversed
            </Badge>
          )}
        </div>
      </div>
      
      <div className="mt-2 text-center">
        <div className="text-sm font-medium text-amber-400">
          {position.position_name}
        </div>
        <div className="text-xs text-slate-400 mt-1">
          {position.position_meaning}
        </div>
      </div>
      
      <div className="mt-3 p-3 bg-slate-800/50 rounded-lg border border-slate-600/30">
        <div className="text-xs text-slate-200">
          {getCardMeaning(card.card_id, card.is_reversed)}
        </div>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <h1 className="font-serif text-3xl font-bold text-white mb-4 flex items-center justify-center">
          <Stars className="w-8 h-8 mr-3 text-purple-400" />
          Tarot Oracle
        </h1>
        <p className="text-slate-400 max-w-2xl mx-auto">
          Draw cards from the cosmic deck and uncover the wisdom the universe holds for you.
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-3 bg-slate-800/50">
          <TabsTrigger 
            value="draw" 
            className="data-[state=active]:bg-purple-500/20 data-[state=active]:text-purple-400"
            data-testid="draw-cards-tab"
          >
            <Shuffle className="w-4 h-4 mr-2" />
            Draw Cards
          </TabsTrigger>
          <TabsTrigger 
            value="readings" 
            className="data-[state=active]:bg-purple-500/20 data-[state=active]:text-purple-400"
            data-testid="my-readings-tab"
          >
            <Eye className="w-4 h-4 mr-2" />
            My Readings
          </TabsTrigger>
          <TabsTrigger 
            value="deck" 
            className="data-[state=active]:bg-purple-500/20 data-[state=active]:text-purple-400"
            data-testid="view-deck-tab"
          >
            <Stars className="w-4 h-4 mr-2" />
            View Deck
          </TabsTrigger>
        </TabsList>

        {/* Draw Cards Tab */}
        <TabsContent value="draw">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Spread Selection */}
            <Card className="glass-card">
              <CardHeader>
                <CardTitle className="text-white font-serif flex items-center">
                  <Sparkles className="w-5 h-5 mr-2 text-purple-400" />
                  Choose Your Spread
                </CardTitle>
                <CardDescription className="text-slate-400">
                  Select a card layout that resonates with your question
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {spreadsLoading ? (
                  <div className="space-y-3">
                    {[1, 2, 3].map(i => (
                      <div key={i} className="animate-pulse p-4 rounded-lg bg-slate-700/30">
                        <div className="h-4 bg-slate-600/50 rounded mb-2"></div>
                        <div className="h-3 bg-slate-600/30 rounded w-3/4"></div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <>
                    <Select
                      value={selectedSpread}
                      onValueChange={setSelectedSpread}
                    >
                      <SelectTrigger className="form-input" data-testid="spread-select">
                        <SelectValue placeholder="Select a tarot spread" />
                      </SelectTrigger>
                      <SelectContent className="bg-slate-800 border-slate-600">
                        {spreads.map((spread) => (
                          <SelectItem key={spread.id} value={spread.id}>
                            {spread.name} ({spread.positions.length} cards)
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>

                    {selectedSpread && (
                      <div className="space-y-4">
                        {(() => {
                          const spread = spreads.find(s => s.id === selectedSpread);
                          return spread ? (
                            <div className="p-4 rounded-lg bg-slate-800/30 border border-slate-600/30">
                              <h3 className="font-medium text-white mb-2">{spread.name}</h3>
                              <p className="text-sm text-slate-400 mb-3">{spread.description}</p>
                              <div className="space-y-2">
                                {spread.positions.map((position, index) => (
                                  <div key={index} className="flex items-start space-x-3">
                                    <Badge variant="outline" className="mt-0.5">
                                      {position.index}
                                    </Badge>
                                    <div>
                                      <div className="text-sm font-medium text-slate-200">
                                        {position.name}
                                      </div>
                                      <div className="text-xs text-slate-400">
                                        {position.meaning}
                                      </div>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          ) : null;
                        })()}

                        <Button
                          onClick={handleDrawCards}
                          disabled={createReadingMutation.isPending}
                          className="w-full btn-primary"
                          data-testid="draw-cards-button"
                        >
                          {createReadingMutation.isPending ? (
                            <div className="flex items-center space-x-2">
                              <div className="loading-spinner"></div>
                              <span>Shuffling the cosmic deck...</span>
                            </div>
                          ) : (
                            <>
                              <Shuffle className="w-4 h-4 mr-2" />
                              Draw Cards
                            </>
                          )}
                        </Button>
                      </div>
                    )}
                  </>
                )}
              </CardContent>
            </Card>

            {/* Instructions */}
            <Card className="glass-card">
              <CardHeader>
                <CardTitle className="text-white font-serif flex items-center">
                  <Moon className="w-5 h-5 mr-2 text-blue-400" />
                  Tarot Guidance
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="p-3 rounded-lg bg-purple-500/10 border border-purple-500/20">
                    <h4 className="text-sm font-medium text-purple-300 mb-1">
                      Before You Draw
                    </h4>
                    <p className="text-xs text-slate-300">
                      Take a moment to center yourself and focus on your question or intention.
                    </p>
                  </div>

                  <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
                    <h4 className="text-sm font-medium text-amber-300 mb-1">
                      Card Positions
                    </h4>
                    <p className="text-xs text-slate-300">
                      Each position in your chosen spread represents a different aspect of your question.
                    </p>
                  </div>

                  <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                    <h4 className="text-sm font-medium text-emerald-300 mb-1">
                      Reversed Cards
                    </h4>
                    <p className="text-xs text-slate-300">
                      Reversed cards offer alternative perspectives and internal reflections on the card's energy.
                    </p>
                  </div>

                  <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20">
                    <h4 className="text-sm font-medium text-rose-300 mb-1">
                      Trust Your Intuition
                    </h4>
                    <p className="text-xs text-slate-300">
                      While meanings guide you, trust your intuitive response to the cards drawn.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* My Readings Tab */}
        <TabsContent value="readings">
          <Card className="glass-card">
            <CardHeader>
              <CardTitle className="text-white font-serif flex items-center">
                <Eye className="w-5 h-5 mr-2 text-purple-400" />
                Your Tarot Readings
              </CardTitle>
              <CardDescription className="text-slate-400">
                Review your past card draws and their interpretations
              </CardDescription>
            </CardHeader>
            <CardContent>
              {readingsLoading ? (
                <div className="space-y-4">
                  {[1, 2].map(i => (
                    <div key={i} className="animate-pulse p-4 rounded-lg bg-slate-700/30">
                      <div className="h-4 bg-slate-600/50 rounded mb-2"></div>
                      <div className="h-20 bg-slate-600/30 rounded"></div>
                    </div>
                  ))}
                </div>
              ) : readings.length > 0 ? (
                <div className="space-y-6">
                  {readings.map((reading) => (
                    <div key={reading.id} className="p-6 rounded-lg bg-slate-800/30 border border-slate-600/30">
                      <div className="mb-4">
                        <h3 className="font-medium text-white mb-1">
                          {spreads.find(s => s.id === reading.spread_id)?.name || 'Unknown Spread'}
                        </h3>
                        <p className="text-sm text-slate-400">
                          Drawn on {new Date(reading.created_at).toLocaleDateString()}
                        </p>
                      </div>
                      
                      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                        {reading.cards.map((cardDraw, index) => (
                          <CardDisplay 
                            key={index}
                            card={cardDraw}
                            position={{
                              position_name: cardDraw.position_name,
                              position_meaning: cardDraw.position_meaning
                            }}
                          />
                        ))}
                      </div>
                      
                      {reading.interpretation && (
                        <div className="mt-4 p-4 rounded-lg bg-slate-700/30">
                          <h4 className="text-sm font-medium text-white mb-2">Interpretation</h4>
                          <p className="text-sm text-slate-300">{reading.interpretation}</p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12">
                  <Stars className="w-16 h-16 mx-auto mb-4 text-slate-400 opacity-50" />
                  <h3 className="text-white font-medium mb-2">No Readings Yet</h3>
                  <p className="text-slate-400 mb-6">
                    Draw your first cards to begin your tarot journey.
                  </p>
                  <Button 
                    onClick={() => setActiveTab('draw')}
                    className="btn-primary"
                  >
                    <Shuffle className="w-4 h-4 mr-2" />
                    Draw Your First Cards
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* View Deck Tab */}
        <TabsContent value="deck">
          <Card className="glass-card">
            <CardHeader>
              <CardTitle className="text-white font-serif flex items-center">
                <Stars className="w-5 h-5 mr-2 text-purple-400" />
                Tarot Deck
              </CardTitle>
              <CardDescription className="text-slate-400">
                Explore the cards and their meanings
              </CardDescription>
            </CardHeader>
            <CardContent>
              {cardsLoading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {[1, 2, 3, 4, 5, 6].map(i => (
                    <div key={i} className="animate-pulse p-4 rounded-lg bg-slate-700/30">
                      <div className="h-4 bg-slate-600/50 rounded mb-2"></div>
                      <div className="h-3 bg-slate-600/30 rounded mb-2"></div>
                      <div className="h-20 bg-slate-600/30 rounded"></div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {cards.map((card) => (
                    <div key={card.id} className="p-4 rounded-lg bg-slate-800/30 border border-slate-600/30 card-hover">
                      <div className="mb-3">
                        <h3 className="font-medium text-white flex items-center">
                          {card.arcana === 'major' ? (
                            <Sun className="w-4 h-4 mr-2 text-amber-400" />
                          ) : (
                            <Moon className="w-4 h-4 mr-2 text-blue-400" />
                          )}
                          {card.name}
                        </h3>
                        <div className="flex items-center space-x-2 mt-1">
                          <Badge variant="outline" className="text-xs">
                            {card.arcana}
                          </Badge>
                          {card.suit && (
                            <Badge variant="outline" className="text-xs">
                              {card.suit}
                            </Badge>
                          )}
                          {card.number !== null && (
                            <Badge variant="outline" className="text-xs">
                              {card.number}
                            </Badge>
                          )}
                        </div>
                      </div>
                      
                      <div className="space-y-3">
                        <div>
                          <h4 className="text-sm font-medium text-emerald-300 mb-1">
                            Upright Meaning
                          </h4>
                          <p className="text-xs text-slate-300">
                            {card.upright_meaning}
                          </p>
                        </div>
                        
                        <div>
                          <h4 className="text-sm font-medium text-rose-300 mb-1">
                            Reversed Meaning
                          </h4>
                          <p className="text-xs text-slate-300">
                            {card.reversed_meaning}
                          </p>
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

export default TarotPage;