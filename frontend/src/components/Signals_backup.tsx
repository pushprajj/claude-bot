'use client';

import { useState, useEffect } from 'react';
import { Play, RefreshCw, TrendingUp, TrendingDown, AlertCircle, Eye, Plus, BarChart3, X } from 'lucide-react';
import { signalApi, tickerApi, Ticker } from '@/lib/api';

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

  useEffect(() => {
    fetchTickers();
    // Don't auto-fetch signals on mount for current tab
  }, []);

  // Refetch current signals when market or exchange changes
  useEffect(() => {
    if (activeTab === 'current') {
      // Don't auto-fetch for current tab - only after generation
      setCurrentSignals([]);
    }
  }, [selectedMarket, selectedExchange]);
  
  // Fetch historical signals when historical filters change
  useEffect(() => {
    if (activeTab === 'historical') {
      fetchHistoricalSignals();
    }
  }, [activeTab, historicalMarket, historicalExchange, historicalTicker, historicalSignalType, historicalSignalStrength, startDate, endDate, historicalProcessed]);

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
  
  const fetchHistoricalSignals = async () => {
    try {
      setHistoricalLoading(true);
      setHistoricalError(null);
      
      // Build request for historical signals endpoint
      const requestBody: any = {
        skip: 0,
        limit: 50
      };
      
      if (historicalMarket) {
        requestBody.market_type = historicalMarket;
      }
      
      if (historicalExchange) {
        requestBody.exchange = historicalExchange;
      }
      
      if (historicalTicker) {
        requestBody.ticker_symbol = historicalTicker;
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
      const parsedSignals = response.data.map((signal: any) => ({
        ...signal,
        details: signal.signal_data ? JSON.parse(signal.signal_data) : {}
      }));
      
      setHistoricalSignals(parsedSignals);
    } catch (err: any) {
      console.error('Failed to fetch historical signals:', err);
      setHistoricalError(err.message || 'Failed to fetch historical signals');
      setHistoricalSignals([]);
    } finally {
      setHistoricalLoading(false);
    }
  };

  const generateSignals = async () => {
    try {
      setGenerating(true);
      setError(null);

      // Build request parameters matching backend schema
      const requestParams = {
        market_type: selectedMarket as 'crypto' | 'stock' || undefined,
        exchange: selectedExchange || undefined,
        ticker_symbols: selectedTicker ? [selectedTicker] : undefined
      };

      const response = await signalApi.generate(requestParams);
      
      if (response.data.status === 'completed') {
        setError(null);
        // Show feedback that signals were generated
        alert(`Generated ${response.data.signals_created} signals for ${response.data.ticker_count} tickers!`);
        
        // Immediately fetch the new signals (filtered by current selection)
        await fetchCurrentSignals(selectedMarket, selectedExchange);
      } else if (response.data.status === 'processing') {
        setError(null);
        // Show feedback that signals are being generated
        alert(`Signal generation started for ${response.data.ticker_count} tickers. Please wait a moment and refresh to see results.`);
        
        // Wait a moment and fetch signals
        setTimeout(() => {
          fetchCurrentSignals(selectedMarket, selectedExchange);
        }, 5000);
      } else {
        setError('Failed to start signal generation');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to generate signals');
    } finally {
      setGenerating(false);
    }
  };

  const generateConfirmedBuySignals = async () => {
    try {
      setGenerating(true);
      setError(null);

      // Build request parameters matching backend schema
      const requestParams = {
        market_type: selectedMarket as 'crypto' | 'stock' || undefined,
        exchange: selectedExchange || undefined,
        ticker_symbols: selectedTicker ? [selectedTicker] : undefined
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
        }, 10000); // Poll every 10 seconds for status only
        
      } else if (response.data.status === 'completed') {
        setError(null);
        setProcessing(false);
        setProcessStatus('');
        alert(`Generated confirmed buy signals for ${response.data.ticker_count} tickers!`);
        await fetchSignals(selectedMarket, selectedExchange);
      } else {
        setError('Failed to generate confirmed buy signals');
        setProcessing(false);
        setProcessStatus('');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to generate confirmed buy signals');
    } finally {
      setGenerating(false);
    }
  };

  const moveToWatchlist = async (signal: Signal) => {
    try {
      // Create watchlist item from signal
      const watchlistItem = {
        ticker_id: signal.ticker_id,
        signal_id: signal.id,
        notes: `${signal.signal_type.toUpperCase()} signal - ${signal.details?.reason || 'Signal generated'}`
      };
      
      // Store in localStorage for now (mock implementation)
      const existingWatchlist = JSON.parse(localStorage.getItem('watchlist') || '[]');
      
      // Check if already exists
      const exists = existingWatchlist.some((item: any) => 
        item.ticker_id === signal.ticker_id && item.ticker_symbol === (signal.ticker?.symbol || '')
      );
      
      if (exists) {
        alert(`${signal.ticker?.symbol || 'Ticker'} is already in watchlist!`);
        return;
      }
      
      const newItem = {
        id: Date.now(),
        ticker_id: signal.ticker_id,
        ticker_symbol: signal.ticker?.symbol || '',
        signal_id: signal.id,
        added_at: new Date().toISOString(),
        is_active: true,
        notes: watchlistItem.notes,
        signal_type: signal.signal_type,
        confidence: signal.confidence_score,
        base_asset: signal.details?.base_asset || 'USDT'
      };
      
      existingWatchlist.push(newItem);
      localStorage.setItem('watchlist', JSON.stringify(existingWatchlist));
      
      alert(`${signal.ticker?.symbol || 'Ticker'} moved to watchlist!`);
    } catch (err) {
      setError('Failed to move to watchlist');
    }
  };

  const openTrade = async (signal: Signal) => {
    try {
      setSelectedSignalForTrade(signal);
      setTradeFormData({
        entry_price: signal.price.toString(),
        quantity: '1',
        stop_loss: '',
        take_profit: '',
        notes: `${signal.signal_type.toUpperCase()} signal - ${signal.details?.reason || ''}`
      });
      setShowTradeForm(true);
    } catch (err) {
      setError('Failed to open trade form');
    }
  };

  const submitTrade = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (!selectedSignalForTrade) return;
      
      const tradeData = {
        id: Date.now(),
        ticker_id: selectedSignalForTrade.ticker_id,
        ticker_symbol: selectedSignalForTrade.ticker?.symbol || '',
        signal_id: selectedSignalForTrade.id,
        entry_price: parseFloat(tradeFormData.entry_price),
        current_price: parseFloat(tradeFormData.entry_price),
        quantity: parseFloat(tradeFormData.quantity),
        stop_loss: tradeFormData.stop_loss ? parseFloat(tradeFormData.stop_loss) : undefined,
        take_profit: tradeFormData.take_profit ? parseFloat(tradeFormData.take_profit) : undefined,
        status: 'open',
        pnl: 0,
        opened_at: new Date().toISOString(),
        notes: tradeFormData.notes,
        signal_type: selectedSignalForTrade.signal_type,
        base_asset: selectedSignalForTrade.details?.base_asset || 'USDT'
      };
      
      // Store in localStorage for now
      const existingTrades = JSON.parse(localStorage.getItem('trades') || '[]');
      existingTrades.push(tradeData);
      localStorage.setItem('trades', JSON.stringify(existingTrades));
      
      setShowTradeForm(false);
      setSelectedSignalForTrade(null);
      alert(`Trade opened for ${selectedSignalForTrade.ticker?.symbol || 'Ticker'}!`);
    } catch (err) {
      setError('Failed to open trade');
    }
  };

  const getSignalIcon = (type: string) => {
    switch (type) {
      case 'buy':
        return <TrendingUp className="w-4 h-4 text-green-600" />;
      case 'sell':
        return <TrendingDown className="w-4 h-4 text-red-600" />;
      default:
        return <AlertCircle className="w-4 h-4 text-yellow-600" />;
    }
  };

  const getSignalColor = (type: string) => {
    switch (type) {
      case 'buy':
        return 'bg-green-100 text-green-800';
      case 'sell':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-yellow-100 text-yellow-800';
    }
  };

  const getStrengthColor = (strength: string) => {
    switch (strength) {
      case 'strong':
        return 'bg-blue-100 text-blue-800';
      case 'moderate':
        return 'bg-purple-100 text-purple-800';
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
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 mb-4">
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
          </div>
          
          {/* Generate Button */}
          <div className="flex justify-center">
            <button
              onClick={generateConfirmedBuySignals}
              disabled={generating || (!selectedMarket || !selectedExchange)}
              className="bg-green-600 text-white px-6 py-2 rounded-lg flex items-center justify-center gap-2 hover:bg-green-700 disabled:opacity-50"
            >
              <TrendingUp className={`w-4 h-4 ${generating ? 'animate-spin' : ''}`} />
              {generating ? 'Generating...' : 'Generate'}
            </button>
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
                  Confidence
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Generated
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Details
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
                    No signals generated yet. Click "Generate Signals" to start.
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
                        {signal.signal_strength}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      ${signal.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <div className="flex items-center">
                        <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                          <div 
                            className="bg-blue-600 h-2 rounded-full" 
                            style={{ width: `${signal.confidence_score * 100}%` }}
                          ></div>
                        </div>
                        <span className="text-sm">{Math.round(signal.confidence_score * 100)}%</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(signal.generated_at).toLocaleString('en-AU', { 
                        timeZone: 'Australia/Sydney',
                        year: 'numeric',
                        month: '2-digit', 
                        day: '2-digit',
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit'
                      })}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      <div className="max-w-xs">
                        <div className="font-medium">{signal.details?.type || 'N/A'}</div>
                        <div className="text-xs text-gray-400 truncate">
                          {signal.details?.reason || 'No details available'}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <div className="flex gap-2">
                        <button
                          onClick={() => moveToWatchlist(signal)}
                          className="bg-yellow-100 text-yellow-800 px-3 py-1 rounded-lg text-xs font-medium hover:bg-yellow-200 flex items-center gap-1"
                          title="Add to Watchlist"
                        >
                          <Eye className="w-3 h-3" />
                          Watchlist
                        </button>
                        <button
                          onClick={() => openTrade(signal)}
                          className="bg-blue-100 text-blue-800 px-3 py-1 rounded-lg text-xs font-medium hover:bg-blue-200 flex items-center gap-1"
                          title="Open Trade"
                        >
                          <BarChart3 className="w-3 h-3" />
                          Trade
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

          {/* Trade Entry Form Modal */}
      {showTradeForm && selectedSignalForTrade && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">Open Trade for {selectedSignalForTrade.ticker?.symbol || 'Ticker'}</h3>
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
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {historicalLoading ? (
                    <tr>
                      <td colSpan={8} className="px-6 py-12 text-center text-gray-500">
                        Loading historical signals...
                      </td>
                    </tr>
                  ) : historicalSignals.length === 0 ? (
                    <tr>
                      <td colSpan={8} className="px-6 py-12 text-center text-gray-500">
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
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}