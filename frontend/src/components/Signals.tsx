'use client';

import { useState, useEffect } from 'react';
import { Play, RefreshCw, TrendingUp, TrendingDown, AlertCircle, Eye, Plus, BarChart3, X, Target } from 'lucide-react';
import { signalApi, tickerApi, watchlistApi, tradeApi, Ticker } from '@/lib/api';

interface Signal {
  id?: number;
  ticker_id: number;
  ticker_symbol?: string;
  signal_type: 'buy' | 'sell' | 'hold';
  signal_strength: 'weak' | 'moderate' | 'strong';
  price: number;
  volume?: number;
  confidence_score: number;
  signal_data?: string; // JSON string from backend
  signal_date?: string; // Date of signal
  details?: any; // Parsed from signal_data
  generated_at: string;
  is_processed?: boolean;
  ticker?: Ticker;
}

export default function Signals() {
  // Tab state
  const [activeTab, setActiveTab] = useState<'current' | 'historical'>('current');
  
  // Current signals state
  const [currentSignals, setCurrentSignals] = useState<Signal[]>([]);
  const [currentLoading, setCurrentLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [processStatus, setProcessStatus] = useState('');
  const [currentError, setCurrentError] = useState<string | null>(null);
  
  // Historical signals state
  const [historicalSignals, setHistoricalSignals] = useState<Signal[]>([]);
  const [historicalLoading, setHistoricalLoading] = useState(false);
  const [historicalError, setHistoricalError] = useState<string | null>(null);
  const [historicalPage, setHistoricalPage] = useState(1);
  const [historicalTotalPages, setHistoricalTotalPages] = useState(0);
  const [historicalTotalCount, setHistoricalTotalCount] = useState(0);
  const ITEMS_PER_PAGE = 20;
  const [debouncedHistoricalTicker, setDebouncedHistoricalTicker] = useState('');
  
  // Common state
  const [tickers, setTickers] = useState<Ticker[]>([]);
  const [error, setError] = useState<string | null>(null);
  
  // Current signals filters
  const [selectedMarket, setSelectedMarket] = useState<string>('');
  const [selectedExchange, setSelectedExchange] = useState<string>('');
  const [selectedBaseAsset, setSelectedBaseAsset] = useState<string>('USDT');
  const [selectedSignalType, setSelectedSignalType] = useState<string>('confirmed_buy');
  
  // Historical signals filters
  const [historicalMarket, setHistoricalMarket] = useState<string>('');
  const [historicalExchange, setHistoricalExchange] = useState<string>('');
  const [historicalTicker, setHistoricalTicker] = useState<string>('');
  const [historicalSignalType, setHistoricalSignalType] = useState<string>('');
  const [historicalSignalStrength, setHistoricalSignalStrength] = useState<string>('');
  const [historicalBaseAsset, setHistoricalBaseAsset] = useState<string>('');
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');
  const [historicalProcessed, setHistoricalProcessed] = useState<string>('');
  const [showTradeForm, setShowTradeForm] = useState(false);
  const [selectedSignalForTrade, setSelectedSignalForTrade] = useState<Signal | null>(null);
  const [tradeFormData, setTradeFormData] = useState({
    entry_price: '',
    quantity: '',
    stop_loss: '',
    take_profit: '',
    notes: ''
  });
  
  // Watchlist modal state
  const [showWatchlistForm, setShowWatchlistForm] = useState(false);
  const [selectedSignalForWatchlist, setSelectedSignalForWatchlist] = useState<Signal | null>(null);
  const [watchlistFormData, setWatchlistFormData] = useState({
    support_price: '',
    resistance_price: '',
    target_min: '',
    target_max: '',
    notes: ''
  });

  useEffect(() => {
    fetchTickers();
    // Don't auto-fetch signals on mount for current tab
  }, []);

  // Clear current signals only when market or exchange filters actually change (not when switching tabs)
  useEffect(() => {
    // Only clear if we have existing signals and the filters changed
    if (currentSignals.length > 0) {
      setCurrentSignals([]);
    }
  }, [selectedMarket, selectedExchange]);
  
  // Debounce ticker symbol input to avoid API calls on every keystroke
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedHistoricalTicker(historicalTicker);
    }, 500); // 500ms delay
    
    return () => clearTimeout(timer);
  }, [historicalTicker]);
  
  // Fetch historical signals when historical filters change (using debounced ticker)
  useEffect(() => {
    if (activeTab === 'historical') {
      setHistoricalPage(1); // Reset to first page when filters change
      fetchHistoricalSignals(1);
    }
  }, [activeTab, historicalMarket, historicalExchange, debouncedHistoricalTicker, historicalSignalType, historicalSignalStrength, startDate, endDate, historicalProcessed]);
  
  // Handle pagination changes
  const handlePageChange = (newPage: number) => {
    if (newPage >= 1 && newPage <= historicalTotalPages) {
      fetchHistoricalSignals(newPage);
    }
  };

  const fetchTickers = async () => {
    try {
      const response = await tickerApi.getAll();
      setTickers(response.data);
    } catch (err) {
      console.error('Failed to fetch tickers:', err);
    }
  };

  const fetchCurrentSignals = async (marketType?: string, exchange?: string) => {
    try {
      setCurrentLoading(true);
      
      // Use parameters if provided, otherwise use current state
      const market = marketType !== undefined ? marketType : selectedMarket;
      const exch = exchange !== undefined ? exchange : selectedExchange;
      
      // Build query parameters based on selected market and exchange
      const queryParams: any = { limit: 25 };
      
      if (market) {
        queryParams.market_type = market;
      }
      
      if (exch) {
        queryParams.exchange = exch;
      }
      
      console.log('Fetching current signals with params:', queryParams);
      
      const response = await signalApi.getAll(queryParams);
      
      // Parse signal_data JSON string into details object
      const parsedSignals = response.data.map((signal: any) => ({
        ...signal,
        details: signal.signal_data ? JSON.parse(signal.signal_data) : {}
      }));
      
      setCurrentSignals(parsedSignals);
      return parsedSignals; // Return signals for completion detection
    } catch (err) {
      console.error('Failed to fetch current signals:', err);
      setCurrentSignals([]); // Set empty array for mock mode
      return []; // Return empty array on error
    } finally {
      setCurrentLoading(false);
    }
  };
  
  const fetchHistoricalSignals = async (page: number = historicalPage) => {
    try {
      setHistoricalLoading(true);
      setHistoricalError(null);
      
      // Build request for historical signals endpoint with pagination
      const requestBody: any = {
        skip: (page - 1) * ITEMS_PER_PAGE,
        limit: ITEMS_PER_PAGE
      };
      
      if (historicalMarket) {
        requestBody.market_type = historicalMarket;
      }
      
      if (historicalExchange) {
        requestBody.exchange = historicalExchange;
      }
      
      if (debouncedHistoricalTicker) {
        requestBody.ticker_symbol = debouncedHistoricalTicker;
      }
      
      if (historicalSignalType) {
        requestBody.signal_type = historicalSignalType;
      }
      
      if (historicalSignalStrength) {
        requestBody.signal_strength = historicalSignalStrength;
      }
      
      if (startDate) {
        requestBody.start_date = startDate;
      }
      
      if (endDate) {
        requestBody.end_date = endDate;
      }
      
      if (historicalBaseAsset) {
        requestBody.base_asset = historicalBaseAsset;
      }
      
      if (historicalProcessed !== '') {
        requestBody.is_processed = historicalProcessed === 'true';
      }
      
      console.log('Fetching historical signals with params:', requestBody);
      
      const response = await signalApi.getHistorical(requestBody);
      
      // Parse signal_data JSON string into details object
      // Backend now returns paginated response: {signals, total, page, per_page, total_pages}
      const parsedSignals = response.data.signals?.map((signal: any) => ({
        ...signal,
        details: signal.signal_data ? JSON.parse(signal.signal_data) : {}
      })) || [];
      
      setHistoricalSignals(parsedSignals);
      setHistoricalTotalCount(response.data.total || 0);
      setHistoricalTotalPages(response.data.total_pages || 0);
      setHistoricalPage(page);
    } catch (err: any) {
      console.error('Failed to fetch historical signals:', err);
      setHistoricalError(err.message || 'Failed to fetch historical signals');
      setHistoricalSignals([]);
    } finally {
      setHistoricalLoading(false);
    }
  };

  const generateConfirmedBuySignals = async () => {
    try {
      setGenerating(true);
      setError(null);

      // Check if this is a crypto workflow
      const isCryptoWorkflow = (
        selectedMarket === 'crypto' &&
        selectedExchange === 'Binance' &&
        (selectedBaseAsset === 'ETH' || selectedBaseAsset === 'BTC') &&
        selectedSignalType === 'confirmed_buy'
      );

      if (isCryptoWorkflow) {
        // Use crypto-specific endpoint
        const cryptoParams = {
          market: 'crypto',
          exchange: 'binance',
          base_asset: selectedBaseAsset,
          signal_type: 'confirmed_buy',
          limit_pairs: null // No limit - fetch all qualifying pairs
        };

        console.log('Generating crypto signals with params:', cryptoParams);
        
        // Clear previous signals and show processing status for crypto
        setCurrentSignals([]);
        setProcessing(true);
        setProcessStatus(`Processing ${selectedBaseAsset} pairs from Binance... Fetching market data...`);
        
        const response = await signalApi.generateCrypto(cryptoParams);
        
        // Clear processing status
        setProcessing(false);
        setProcessStatus('');
        
        if (response.data.success) {
          // Parse signal_data JSON string into details object for crypto signals
          const parsedSignals = response.data.signals.map((signal: any) => ({
            ...signal,
            details: signal.signal_data ? JSON.parse(signal.signal_data) : {}
          }));
          
          setCurrentSignals(parsedSignals);
          
          // Show success message
          if (response.data.signals.length > 0) {
            alert(`Crypto signal generation completed! Generated ${response.data.signals.length} signals from ${response.data.total_pairs_checked} ${selectedBaseAsset} pairs.`);
          } else {
            alert(`Crypto signal generation completed! No ${selectedBaseAsset} pairs currently meet confirmed buy criteria. Checked ${response.data.total_pairs_checked} pairs.`);
          }
        } else {
          setError('Failed to generate crypto signals');
        }
        
        return; // Exit early for crypto workflow
      }

      // Standard stock workflow
      const requestParams = {
        market_type: selectedMarket as 'crypto' | 'stock' || undefined,
        exchange: selectedExchange || undefined
      };

      const response = await signalApi.generateConfirmedBuy(requestParams);
      
      if (response.data.status === 'processing') {
        setError(null);
        setProcessing(true);
        setProcessStatus(`Processing ${response.data.ticker_count} tickers... Estimated time: ${response.data.estimated_time}`);
        
        // Poll for completion status every 10 seconds (less aggressive)
        const pollInterval = setInterval(async () => {
          try {
            const statusResponse = await signalApi.getGenerationStatus();
            const status = statusResponse.data;
            
            if (status.status === 'completed') {
              // Generation completed - refresh signals once and stop polling
              clearInterval(pollInterval);
              setProcessing(false);
              setProcessStatus('');
              
              // Fetch the new signals
              await fetchCurrentSignals(selectedMarket, selectedExchange);
              
              // Show success message
              alert(`Signal generation completed! Generated ${status.signals_generated} signals for ${status.ticker_count} tickers.`);
              
            } else if (status.status === 'error') {
              // Generation failed
              clearInterval(pollInterval);
              setProcessing(false);
              setProcessStatus('');
              setError('Signal generation failed. Please try again.');
              
            } else if (status.status === 'running') {
              // Still running - update status
              const elapsed = Math.round((new Date().getTime() - new Date(status.started_at).getTime()) / 1000);
              setProcessStatus(`Processing ${status.ticker_count} tickers... Running for ${Math.floor(elapsed/60)}:${(elapsed%60).toString().padStart(2,'0')}`);
              
            } else {
              // Status is idle or unknown - stop polling
              clearInterval(pollInterval);
              setProcessing(false);
              setProcessStatus('');
              setError('Signal generation status unknown. Please refresh to see if signals were generated.');
            }
            
          } catch (err) {
            console.error('Error checking generation status:', err);
            // Continue polling on status check errors
          }
        }, 10000); // Poll every 10 seconds
        
      } else {
        setError('Failed to start signal generation');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to generate confirmed buy signals');
    } finally {
      setGenerating(false);
    }
  };

  const processSignal = async (signalId: number, action: string) => {
    try {
      await signalApi.process(signalId, action as any);
      // Refresh signals after processing
      await fetchCurrentSignals(selectedMarket, selectedExchange);
    } catch (err) {
      console.error('Failed to process signal:', err);
    }
  };

  const openTradeForm = (signal: Signal) => {
    console.log('Opening trade form for signal:', signal);
    setSelectedSignalForTrade(signal);
    setTradeFormData({
      entry_price: signal.price.toString(),
      quantity: '',
      stop_loss: '',
      take_profit: '',
      notes: ''
    });
    setShowTradeForm(true);
  };

  const openWatchlistForm = (signal: Signal) => {
    console.log('Opening watchlist form for signal:', signal);
    setSelectedSignalForWatchlist(signal);
    setWatchlistFormData({
      support_price: (signal.price * 0.95).toFixed(2), // Default support at 5% below signal price
      resistance_price: (signal.price * 1.05).toFixed(2), // Default resistance at 5% above signal price
      target_min: (signal.price * 1.02).toFixed(2), // Default target min at 2% above signal price
      target_max: (signal.price * 1.08).toFixed(2), // Default target max at 8% above signal price
      notes: ''
    });
    setShowWatchlistForm(true);
  };

  const submitTrade = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedSignalForTrade) return;

    try {
      // Create the trade entry
      const tradeData = {
        ticker_id: selectedSignalForTrade.ticker_id,
        entry_price: parseFloat(tradeFormData.entry_price),
        quantity: parseFloat(tradeFormData.quantity),
        stop_loss: tradeFormData.stop_loss ? parseFloat(tradeFormData.stop_loss) : undefined,
        take_profit: tradeFormData.take_profit ? parseFloat(tradeFormData.take_profit) : undefined,
        notes: tradeFormData.notes,
        signal_id: selectedSignalForTrade.id
      };

      // Create the trade via API
      await tradeApi.create(tradeData);
      
      setShowTradeForm(false);
      setSelectedSignalForTrade(null);
      
      // Show success message
      alert('Trade opened successfully!');
    } catch (err) {
      console.error('Failed to submit trade:', err);
      alert('Failed to open trade. Please try again.');
    }
  };

  const submitWatchlist = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedSignalForWatchlist) return;

    // Validate that at least one group (support/resistance OR target range) is filled
    const hasSupResValues = watchlistFormData.support_price || watchlistFormData.resistance_price;
    const hasTargetValues = watchlistFormData.target_min || watchlistFormData.target_max;
    
    if (!hasSupResValues && !hasTargetValues) {
      alert('Please fill in either Support/Resistance levels OR Target Range values (or both).');
      return;
    }

    try {
      // Create the watchlist entry
      const watchlistData = {
        ticker_id: selectedSignalForWatchlist.ticker_id,
        support_price: watchlistFormData.support_price ? parseFloat(watchlistFormData.support_price) : null,
        resistance_price: watchlistFormData.resistance_price ? parseFloat(watchlistFormData.resistance_price) : null,
        target_min: watchlistFormData.target_min ? parseFloat(watchlistFormData.target_min) : null,
        target_max: watchlistFormData.target_max ? parseFloat(watchlistFormData.target_max) : null,
        signal_type: selectedSignalForWatchlist.signal_type,
        signal_date: selectedSignalForWatchlist.signal_date || selectedSignalForWatchlist.generated_at.split('T')[0], // Use signal_date or extract date from generated_at
        signal_price: selectedSignalForWatchlist.price,
        notes: watchlistFormData.notes,
        signal_id: selectedSignalForWatchlist.id
      };

      // Create the watchlist item via API
      const response = await watchlistApi.create(watchlistData);
      
      setShowWatchlistForm(false);
      setSelectedSignalForWatchlist(null);
      
      // Show success message
      alert('Added to watchlist successfully!');
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Unknown error';
      
      // Provide user-friendly error messages
      if (errorMessage.includes('already in watchlist')) {
        console.warn('Attempted to add duplicate ticker to watchlist:', selectedSignalForWatchlist.ticker.symbol);
        alert(`${selectedSignalForWatchlist.ticker.symbol} is already in your watchlist. You can update it from the Watchlist page.`);
      } else if (errorMessage.includes('Ticker not found')) {
        console.warn('Ticker not found when adding to watchlist');
        alert('The selected ticker was not found. Please try again.');
      } else {
        console.error('Failed to add to watchlist:', errorMessage);
        alert(`Failed to add to watchlist: ${errorMessage}`);
      }
    }
  };

  const getSignalIcon = (type: string) => {
    switch (type) {
      case 'buy':
        return <TrendingUp className="w-4 h-4 text-green-600" />;
      case 'sell':
        return <TrendingDown className="w-4 h-4 text-red-600" />;
      default:
        return <AlertCircle className="w-4 h-4 text-gray-600" />;
    }
  };

  const getSignalColor = (type: string) => {
    switch (type) {
      case 'buy':
        return 'bg-green-100 text-green-800';
      case 'sell':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStrengthColor = (strength: string) => {
    switch (strength) {
      case 'strong':
        return 'bg-green-100 text-green-800';
      case 'moderate':
        return 'bg-yellow-100 text-yellow-800';
      case 'weak':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold mb-2">Signal Management</h1>
        
        {/* Tab Navigation */}
        <div className="border-b border-gray-200 mb-6">
          <nav className="-mb-px flex space-x-8" aria-label="Tabs">
            <button
              onClick={() => setActiveTab('current')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'current'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Current Signals
            </button>
            <button
              onClick={() => setActiveTab('historical')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'historical'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Historical Signals
            </button>
          </nav>
        </div>
        
        {/* Tab Content */}
        {activeTab === 'current' && (
          <div className="space-y-6">
            {/* Generation Controls */}
            <div className="w-full bg-white p-4 rounded-lg shadow border">
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-4 mb-4">
                {/* Market Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Market</label>
                  <select
                    value={selectedMarket}
                    onChange={(e) => {
                      setSelectedMarket(e.target.value);
                      setSelectedExchange('');
                      if (e.target.value === 'stock') {
                        setSelectedBaseAsset('USD');
                      } else if (e.target.value === 'crypto') {
                        setSelectedBaseAsset('USDT');
                      }
                    }}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">All Markets</option>
                    <option value="crypto">Crypto</option>
                    <option value="stock">Stock</option>
                  </select>
                </div>
                
                {/* Exchange Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Exchange</label>
                  <select
                    value={selectedExchange}
                    onChange={(e) => setSelectedExchange(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    disabled={!selectedMarket}
                  >
                    <option value="">All Exchanges</option>
                    {selectedMarket === 'crypto' && (
                      <>
                        <option value="Binance">Binance</option>
                        <option value="Bybit">Bybit</option>
                        <option value="Kraken">Kraken</option>
                        <option value="KuCoin">KuCoin</option>
                      </>
                    )}
                    {selectedMarket === 'stock' && (
                      <>
                        <option value="NYSE">NYSE</option>
                        <option value="NASDAQ">NASDAQ</option>
                        <option value="ASX">ASX</option>
                      </>
                    )}
                  </select>
                </div>

                {/* Base Asset Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Base Asset</label>
                  <select
                    value={selectedBaseAsset}
                    onChange={(e) => setSelectedBaseAsset(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    {selectedMarket === 'stock' ? (
                      <option value="USD">USD</option>
                    ) : (
                      <>
                        <option value="USDT">USDT</option>
                        <option value="BTC">BTC</option>
                        <option value="ETH">ETH</option>
                        <option value="PAXG">PAXG</option>
                      </>
                    )}
                  </select>
                </div>
                
                {/* Signal Type Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Signal Type</label>
                  <select
                    value={selectedSignalType}
                    onChange={(e) => setSelectedSignalType(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="confirmed_buy">Confirmed Buy</option>
                    {/* Additional signal types will be added here in future */}
                  </select>
                </div>
                
                {/* Generate Button */}
                <div className="flex items-end">
                  <button
                    onClick={generateConfirmedBuySignals}
                    disabled={generating || (!selectedMarket || !selectedExchange)}
                    className="w-full bg-green-600 text-white px-4 py-2 rounded-lg flex items-center justify-center gap-2 hover:bg-green-700 disabled:opacity-50"
                  >
                    <TrendingUp className={`w-4 h-4 ${generating ? 'animate-spin' : ''}`} />
                    {generating ? 'Generating...' : 'Generate'}
                  </button>
                </div>
              </div>
            </div>
            
            {/* Current Signals Error */}
            {currentError && (
              <div className="mb-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded-lg">
                {currentError}
              </div>
            )}

            {/* Processing Status */}
            {processing && (
              <div className="mb-4 p-4 bg-blue-100 border border-blue-400 text-blue-700 rounded-lg">
                <div className="flex items-center">
                  <RefreshCw className="animate-spin w-4 h-4 mr-2" />
                  <span>{processStatus}</span>
                </div>
                <div className="mt-2 text-sm text-blue-600">
                  Signals will appear in the table below as they are generated...
                </div>
              </div>
            )}

            {/* Statistics Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-white p-4 rounded-lg shadow">
                <div className="flex items-center">
                  <TrendingUp className="w-5 h-5 text-green-600 mr-2" />
                  <div>
                    <p className="text-sm text-gray-600">Buy Signals</p>
                    <p className="text-xl font-bold text-green-600">
                      {currentSignals.filter(s => s.signal_type === 'buy').length}
                    </p>
                  </div>
                </div>
              </div>
              
              <div className="bg-white p-4 rounded-lg shadow">
                <div className="flex items-center">
                  <TrendingDown className="w-5 h-5 text-red-600 mr-2" />
                  <div>
                    <p className="text-sm text-gray-600">Sell Signals</p>
                    <p className="text-xl font-bold text-red-600">
                      {currentSignals.filter(s => s.signal_type === 'sell').length}
                    </p>
                  </div>
                </div>
              </div>
              
              <div className="bg-white p-4 rounded-lg shadow">
                <div className="flex items-center">
                  <AlertCircle className="w-5 h-5 text-blue-600 mr-2" />
                  <div>
                    <p className="text-sm text-gray-600">Total Signals</p>
                    <p className="text-xl font-bold text-blue-600">{currentSignals.length}</p>
                  </div>
                </div>
              </div>
              
              <div className="bg-white p-4 rounded-lg shadow">
                <div className="flex items-center">
                  <Eye className="w-5 h-5 text-purple-600 mr-2" />
                  <div>
                    <p className="text-sm text-gray-600">Avg Confidence</p>
                    <p className="text-xl font-bold text-purple-600">
                      {currentSignals.length > 0 
                        ? `${Math.round(currentSignals.reduce((acc, s) => acc + s.confidence_score, 0) / currentSignals.length * 100)}%`
                        : '0%'
                      }
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Signals Table */}
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Ticker
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Signal
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Strength
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Price
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Volume
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Confidence
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Generated
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {currentLoading ? (
                      <tr>
                        <td colSpan={8} className="px-6 py-12 text-center text-gray-500">
                          Loading signals...
                        </td>
                      </tr>
                    ) : currentSignals.length === 0 ? (
                      <tr>
                        <td colSpan={8} className="px-6 py-12 text-center text-gray-500">
                          No signals generated yet. Click "Generate" to start.
                        </td>
                      </tr>
                    ) : (
                      currentSignals.map((signal, index) => (
                        <tr key={`${signal.ticker_id}-${signal.generated_at}-${index}`} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            <div>
                              <div className="font-semibold">{signal.ticker?.symbol || 'Unknown'}</div>
                              <div className="text-xs text-gray-500">{signal.ticker?.exchange || 'Unknown Exchange'}</div>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm">
                            <div className="flex items-center">
                              {getSignalIcon(signal.signal_type)}
                              <span className={`ml-2 px-2 py-1 text-xs rounded-full ${getSignalColor(signal.signal_type)}`}>
                                {signal.signal_type.toUpperCase()}
                              </span>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm">
                            <span className={`px-2 py-1 text-xs rounded-full ${getStrengthColor(signal.signal_strength)}`}>
                              {signal.signal_strength.toUpperCase()}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            ${signal.price.toFixed(2)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {signal.volume ? signal.volume.toLocaleString() : 'N/A'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {Math.round(signal.confidence_score * 100)}%
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {new Date(signal.generated_at).toLocaleString()}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                            <div className="flex space-x-2">
                              <button
                                onClick={() => openWatchlistForm(signal)}
                                className="text-blue-600 hover:text-blue-900"
                                title="Add to Watchlist"
                              >
                                <Eye className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => openTradeForm(signal)}
                                className="text-green-600 hover:text-green-900"
                                title="Open Trade"
                              >
                                <Target className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => processSignal(signal.id!, 'skip')}
                                className="text-gray-600 hover:text-gray-900"
                                title="Skip"
                              >
                                <X className="w-4 h-4" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
        
        {/* Historical Signals Tab */}
        {activeTab === 'historical' && (
          <div className="space-y-6">
            {/* Historical Signals Filters */}
            <div className="bg-white p-4 rounded-lg shadow border">
              <h3 className="text-lg font-semibold mb-4">Filter Historical Signals</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
                {/* Market Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Market</label>
                  <select
                    value={historicalMarket}
                    onChange={(e) => setHistoricalMarket(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">All Markets</option>
                    <option value="crypto">Crypto</option>
                    <option value="stock">Stock</option>
                  </select>
                </div>
                
                {/* Exchange Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Exchange</label>
                  <select
                    value={historicalExchange}
                    onChange={(e) => setHistoricalExchange(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">All Exchanges</option>
                    {historicalMarket === 'crypto' && (
                      <>
                        <option value="Binance">Binance</option>
                        <option value="Bybit">Bybit</option>
                        <option value="Kraken">Kraken</option>
                        <option value="KuCoin">KuCoin</option>
                      </>
                    )}
                    {historicalMarket === 'stock' && (
                      <>
                        <option value="NYSE">NYSE</option>
                        <option value="NASDAQ">NASDAQ</option>
                        <option value="ASX">ASX</option>
                      </>
                    )}
                  </select>
                </div>
                
                {/* Ticker Search */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Ticker Symbol</label>
                  <input
                    type="text"
                    value={historicalTicker}
                    onChange={(e) => setHistoricalTicker(e.target.value.toUpperCase())}
                    placeholder="e.g., CBA, BHP"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                
                {/* Signal Type */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Signal Type</label>
                  <select
                    value={historicalSignalType}
                    onChange={(e) => setHistoricalSignalType(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">All Types</option>
                    <option value="buy">Buy</option>
                    <option value="sell">Sell</option>
                    <option value="hold">Hold</option>
                  </select>
                </div>
                
                {/* Signal Strength */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Signal Strength</label>
                  <select
                    value={historicalSignalStrength}
                    onChange={(e) => setHistoricalSignalStrength(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">All Strengths</option>
                    <option value="weak">Weak</option>
                    <option value="moderate">Moderate</option>
                    <option value="strong">Strong</option>
                  </select>
                </div>
                
                {/* Start Date */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">From Date</label>
                  <input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                
                {/* End Date */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">To Date</label>
                  <input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                
                {/* Processed Status */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                  <select
                    value={historicalProcessed}
                    onChange={(e) => setHistoricalProcessed(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">All</option>
                    <option value="false">Pending</option>
                    <option value="true">Processed</option>
                  </select>
                </div>
              </div>
            </div>
            
            {/* Historical Signals Error */}
            {historicalError && (
              <div className="p-4 bg-red-100 border border-red-400 text-red-700 rounded-lg">
                {historicalError}
              </div>
            )}
            
            {/* Historical Signals Table */}
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="px-4 py-3 border-b border-gray-200">
                <h3 className="text-lg font-semibold">Historical Signals</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Ticker
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Signal
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Strength
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Price
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Confidence
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Signal Date
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Generated
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {historicalLoading ? (
                      <tr>
                        <td colSpan={9} className="px-6 py-12 text-center text-gray-500">
                          Loading historical signals...
                        </td>
                      </tr>
                    ) : historicalSignals.length === 0 ? (
                      <tr>
                        <td colSpan={9} className="px-6 py-12 text-center text-gray-500">
                          No historical signals found. Adjust your filters or generate some signals first.
                        </td>
                      </tr>
                    ) : (
                      historicalSignals.map((signal, index) => (
                        <tr key={`historical-${signal.ticker_id}-${signal.generated_at}-${index}`} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            <div>
                              <div className="font-semibold">{signal.ticker?.symbol || 'Unknown'}</div>
                              <div className="text-xs text-gray-500">{signal.ticker?.exchange || 'Unknown Exchange'}</div>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm">
                            <div className="flex items-center">
                              {getSignalIcon(signal.signal_type)}
                              <span className={`ml-2 px-2 py-1 text-xs rounded-full ${getSignalColor(signal.signal_type)}`}>
                                {signal.signal_type.toUpperCase()}
                              </span>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm">
                            <span className={`px-2 py-1 text-xs rounded-full ${getStrengthColor(signal.signal_strength)}`}>
                              {signal.signal_strength.toUpperCase()}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            ${signal.price.toFixed(2)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {Math.round(signal.confidence_score * 100)}%
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {signal.signal_date || 'N/A'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {new Date(signal.generated_at).toLocaleString()}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm">
                            <span className={`px-2 py-1 text-xs rounded-full ${
                              signal.is_processed ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                            }`}>
                              {signal.is_processed ? 'Processed' : 'Pending'}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                            <div className="flex space-x-2">
                              <button
                                onClick={() => openWatchlistForm(signal)}
                                className="text-blue-600 hover:text-blue-900"
                                title="Add to Watchlist"
                              >
                                <Eye className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => openTradeForm(signal)}
                                className="text-green-600 hover:text-green-900"
                                title="Open Trade"
                              >
                                <Target className="w-4 h-4" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
              
              {/* Pagination Controls */}
              {historicalTotalPages > 1 && (
                <div className="px-6 py-4 flex items-center justify-between border-t border-gray-200">
                  <div className="text-sm text-gray-700">
                    Showing {((historicalPage - 1) * ITEMS_PER_PAGE) + 1} to {Math.min(historicalPage * ITEMS_PER_PAGE, historicalTotalCount)} of {historicalTotalCount} signals
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => handlePageChange(historicalPage - 1)}
                      disabled={historicalPage <= 1}
                      className="px-3 py-1 text-sm border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Previous
                    </button>
                    
                    {/* Page Numbers */}
                    {Array.from({ length: Math.min(5, historicalTotalPages) }, (_, i) => {
                      let pageNum;
                      if (historicalTotalPages <= 5) {
                        pageNum = i + 1;
                      } else if (historicalPage <= 3) {
                        pageNum = i + 1;
                      } else if (historicalPage >= historicalTotalPages - 2) {
                        pageNum = historicalTotalPages - 4 + i;
                      } else {
                        pageNum = historicalPage - 2 + i;
                      }
                      
                      return (
                        <button
                          key={pageNum}
                          onClick={() => handlePageChange(pageNum)}
                          className={`px-3 py-1 text-sm border rounded-md ${
                            pageNum === historicalPage
                              ? 'bg-blue-600 text-white border-blue-600'
                              : 'border-gray-300 hover:bg-gray-50'
                          }`}
                        >
                          {pageNum}
                        </button>
                      );
                    })}
                    
                    <button
                      onClick={() => handlePageChange(historicalPage + 1)}
                      disabled={historicalPage >= historicalTotalPages}
                      className="px-3 py-1 text-sm border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Next
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
        
        {/* Trade Entry Form Modal - Outside tabs so it works for both current and historical */}
        {showTradeForm && selectedSignalForTrade && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold">
                  Open Trade - {selectedSignalForTrade.ticker?.symbol} ({selectedSignalForTrade.ticker?.exchange})
                </h3>
                <button
                  onClick={() => setShowTradeForm(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              
              <form onSubmit={submitTrade} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Entry Price
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={tradeFormData.entry_price}
                    onChange={(e) => setTradeFormData({...tradeFormData, entry_price: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Quantity
                  </label>
                  <input
                    type="number"
                    step="0.001"
                    value={tradeFormData.quantity}
                    onChange={(e) => setTradeFormData({...tradeFormData, quantity: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Stop Loss (Optional)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={tradeFormData.stop_loss}
                    onChange={(e) => setTradeFormData({...tradeFormData, stop_loss: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Take Profit (Optional)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={tradeFormData.take_profit}
                    onChange={(e) => setTradeFormData({...tradeFormData, take_profit: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Notes
                  </label>
                  <textarea
                    value={tradeFormData.notes}
                    onChange={(e) => setTradeFormData({...tradeFormData, notes: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    rows={3}
                    placeholder="Trade notes or strategy..."
                  />
                </div>
                
                <div className="flex gap-3 pt-4">
                  <button
                    type="button"
                    onClick={() => setShowTradeForm(false)}
                    className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                  >
                    Open Trade
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Watchlist Entry Form Modal - Outside tabs so it works for both current and historical */}
        {showWatchlistForm && selectedSignalForWatchlist && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold">
                  Add to Watchlist - {selectedSignalForWatchlist.ticker?.symbol} ({selectedSignalForWatchlist.ticker?.exchange})
                </h3>
                <button
                  onClick={() => setShowWatchlistForm(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              
              <form onSubmit={submitWatchlist} className="space-y-4">
                {/* Signal Info Row */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Signal Price
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={selectedSignalForWatchlist.price}
                      disabled
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-100 text-gray-600"
                    />
                    <p className="text-xs text-gray-500 mt-1">Current signal price</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Signal Type
                    </label>
                    <input
                      type="text"
                      value={selectedSignalForWatchlist.signal_type.toUpperCase()}
                      disabled
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-100 text-gray-600"
                    />
                  </div>
                </div>
                
                {/* Support/Resistance Section */}
                <div className="border rounded-lg p-3 bg-gray-50">
                  <h4 className="font-medium text-gray-700 mb-3">Support & Resistance Levels</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Support Price
                      </label>
                      <input
                        type="number"
                        step="0.01"
                        value={watchlistFormData.support_price}
                        onChange={(e) => setWatchlistFormData({...watchlistFormData, support_price: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                        placeholder="Support level"
                      />
                      <p className="text-xs text-gray-500 mt-1">Invalidation price</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Resistance Price
                      </label>
                      <input
                        type="number"
                        step="0.01"
                        value={watchlistFormData.resistance_price}
                        onChange={(e) => setWatchlistFormData({...watchlistFormData, resistance_price: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                        placeholder="Resistance level"
                      />
                      <p className="text-xs text-gray-500 mt-1">Breakout price</p>
                    </div>
                  </div>
                </div>

                {/* Target Range Section */}
                <div className="border rounded-lg p-3 bg-blue-50">
                  <h4 className="font-medium text-gray-700 mb-3">Target Range (Retracement Entry)</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Target Min
                      </label>
                      <input
                        type="number"
                        step="0.01"
                        value={watchlistFormData.target_min}
                        onChange={(e) => setWatchlistFormData({...watchlistFormData, target_min: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                        placeholder="Min entry price"
                      />
                      <p className="text-xs text-gray-500 mt-1">Entry floor</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Target Max
                      </label>
                      <input
                        type="number"
                        step="0.01"
                        value={watchlistFormData.target_max}
                        onChange={(e) => setWatchlistFormData({...watchlistFormData, target_max: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                        placeholder="Max entry price"
                      />
                      <p className="text-xs text-gray-500 mt-1">Entry ceiling</p>
                    </div>
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Notes (Optional)
                  </label>
                  <textarea
                    value={watchlistFormData.notes}
                    onChange={(e) => setWatchlistFormData({...watchlistFormData, notes: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    rows={3}
                    placeholder="Why are you watching this? What's your strategy?"
                  />
                </div>
                
                <div className="flex gap-3 pt-4">
                  <button
                    type="button"
                    onClick={() => setShowWatchlistForm(false)}
                    className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center justify-center gap-2"
                  >
                    <Eye className="w-4 h-4" />
                    Add to Watchlist
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}