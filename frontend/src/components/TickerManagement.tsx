'use client';

import { useState, useEffect } from 'react';
import { Plus, Search, Filter, Edit2, Trash2, RefreshCw, Upload } from 'lucide-react';
import { tickerApi, Ticker } from '@/lib/api';

interface TickerFormData {
  symbol: string;
  market_type: 'crypto' | 'stock';
  exchange: string;
  name: string;
  is_active: boolean;
}

export default function TickerManagement() {
  const [tickers, setTickers] = useState<Ticker[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [testError, setTestError] = useState<string | null>(null);
  
  const [showAddForm, setShowAddForm] = useState(false);
  const [showBulkForm, setShowBulkForm] = useState(false);
  const [editingTicker, setEditingTicker] = useState<Ticker | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterMarketType, setFilterMarketType] = useState<string>('');
  const [filterExchange, setFilterExchange] = useState<string>('');
  const [bulkTickersText, setBulkTickersText] = useState('');

  const [formData, setFormData] = useState<TickerFormData>({
    symbol: '',
    market_type: 'crypto',
    exchange: 'Binance',
    name: '',
    is_active: true
  });

  const exchanges = {
    crypto: ['Binance', 'Bybit', 'Kraken', 'KuCoin'],
    stock: ['NYSE', 'NASDAQ', 'ASX']
  };

  useEffect(() => {
    fetchTickers();
  }, [filterMarketType, filterExchange]);

  const fetchTickers = async () => {
    try {
      setLoading(true);
      const response = await tickerApi.getAll({
        market_type: filterMarketType || undefined,
        exchange: filterExchange || undefined,
        limit: 1000, // Ensure we fetch all tickers
      });
      setTickers(response.data);
    } catch (err) {
      setError('Failed to fetch tickers');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null); // Clear any previous errors
    
    console.log('=== FORM SUBMIT STARTED ===');
    console.log('Submitting ticker form with data:', formData);
    
    // Client-side validation for duplicates (when not editing)
    if (!editingTicker) {
      const existingTicker = tickers.find(ticker => 
        ticker.symbol.toLowerCase() === formData.symbol.toLowerCase() &&
        ticker.market_type === formData.market_type &&
        ticker.exchange === formData.exchange
      );
      
      if (existingTicker) {
        setError(`Ticker "${formData.symbol}" already exists for ${formData.market_type} market on ${formData.exchange} exchange. Please choose a different symbol or edit the existing ticker.`);
        return;
      }
    }
    
    try {
      if (editingTicker) {
        console.log('Updating ticker:', editingTicker.id, formData);
        await tickerApi.update(editingTicker.id, formData);
      } else {
        console.log('Creating new ticker:', formData);
        console.log('About to call tickerApi.create...');
        const result = await tickerApi.create(formData);
        console.log('tickerApi.create completed successfully:', result);
      }
      console.log('API call successful, fetching tickers...');
      await fetchTickers();
      console.log('Resetting form...');
      resetForm(); // Only reset on success
    } catch (err: any) {
      console.error('Form submission error:', err.response?.data?.detail || err.message);
      
      // Extract error message for display
      let errorMessage = 'Failed to save ticker';
      if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      } else if (err.response?.data?.message) {
        errorMessage = err.response.data.message;
      }
      
      setError(errorMessage);
      // Don't reset form on error so user can see the error and fix it
    }
  };

  const handleEdit = (ticker: Ticker) => {
    setEditingTicker(ticker);
    setFormData({
      symbol: ticker.symbol,
      market_type: ticker.market_type,
      exchange: ticker.exchange,
      name: ticker.name || '',
      is_active: ticker.is_active
    });
    setShowAddForm(true);
  };

  const handleDelete = async (id: number) => {
    if (confirm('Are you sure you want to delete this ticker?')) {
      try {
        await tickerApi.delete(id);
        await fetchTickers();
      } catch (err) {
        setError('Failed to delete ticker');
      }
    }
  };

  const migrateCryptoTickers = async () => {
    if (!confirm('This will update all crypto tickers to use base asset format only (e.g., BTC/USDT → BTC). Continue?')) {
      return;
    }
    
    try {
      const cryptoTickers = tickers.filter(t => 
        t.market_type === 'crypto' && 
        (t.symbol.includes('/') || t.symbol.includes('USDT') || t.symbol.includes('USD'))
      );
      
      for (const ticker of cryptoTickers) {
        const newSymbol = ticker.symbol.replace(/\/USDT$|\/USD$|\/BUSD$|USDT$|USD$|BUSD$/g, '');
        if (newSymbol !== ticker.symbol) {
          await tickerApi.update(ticker.id, { symbol: newSymbol });
        }
      }
      
      await fetchTickers();
    } catch (err) {
      setError('Failed to migrate crypto tickers');
    }
  };

  const handleBulkSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const lines = bulkTickersText.trim().split('\n').filter(line => line.trim());
      const tickers = [];
      
      for (const line of lines) {
        const parts = line.split(',').map(p => p.trim());
        if (parts.length >= 3) {
          let symbol = parts[0].toUpperCase();
          const marketType = parts[1].toLowerCase() as 'crypto' | 'stock';
          const exchange = parts[2];
          const name = parts[3] || '';
          
          // For crypto, clean to base asset only
          if (marketType === 'crypto') {
            symbol = symbol.replace(/\/USDT$|\/USD$|\/BUSD$|USDT$|USD$|BUSD$/g, '');
          }
          
          tickers.push({
            symbol,
            market_type: marketType,
            exchange,
            name,
            is_active: true
          });
        }
      }
      
      if (tickers.length > 0) {
        await tickerApi.createBulk(tickers);
        await fetchTickers();
        setBulkTickersText('');
        setShowBulkForm(false);
      } else {
        setError('No valid tickers found in the input');
      }
    } catch (err: any) {
      console.error('Bulk form submission error:', err);
      console.error('Error response data:', err.response?.data);
      
      // Enhanced error message extraction for bulk form
      let errorMessage = 'Failed to add bulk tickers';
      if (err.response?.data) {
        if (typeof err.response.data === 'string') {
          errorMessage = err.response.data;
        } else if (err.response.data.detail) {
          errorMessage = err.response.data.detail;
        } else if (err.response.data.message) {
          errorMessage = err.response.data.message;
        }
      }
      
      console.log('Setting bulk error message:', errorMessage);
      setError(errorMessage);
    }
  };

  const resetForm = () => {
    setFormData({
      symbol: '',
      market_type: 'crypto',
      exchange: 'Binance',
      name: '',
      is_active: true
    });
    setEditingTicker(null);
    setShowAddForm(false);
    setError(null);
  };

  const handleFormChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error when user starts making changes
    if (error) setError(null);
  };

  const filteredTickers = tickers.filter(ticker => 
    ticker.symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (ticker.name && ticker.name.toLowerCase().includes(searchTerm.toLowerCase()))
  ).sort((a, b) => a.symbol.localeCompare(b.symbol));

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Ticker Management</h1>
        <div className="flex gap-3">
          {tickers.some(t => t.market_type === 'crypto' && (t.symbol.includes('/') || t.symbol.includes('USDT'))) && (
            <button
              onClick={migrateCryptoTickers}
              className="bg-yellow-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-yellow-700 text-sm"
            >
              <RefreshCw className="w-4 h-4" />
              Migrate Crypto
            </button>
          )}
          <button
            onClick={() => {
              setShowBulkForm(true);
              setError(null); // Clear any existing errors when opening form
            }}
            className="bg-green-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-green-700"
          >
            <Upload className="w-4 h-4" />
            Bulk Add
          </button>
          <button
            onClick={() => {
              setShowAddForm(true);
              setError(null); // Clear any existing errors when opening form
            }}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-blue-700"
          >
            <Plus className="w-4 h-4" />
            Add Ticker
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="mb-6 grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="relative">
          <Search className="w-4 h-4 absolute left-3 top-3 text-gray-400" />
          <input
            type="text"
            placeholder="Search tickers..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg w-full focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
        
        <select
          value={filterMarketType}
          onChange={(e) => setFilterMarketType(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="">All Markets</option>
          <option value="crypto">Crypto</option>
          <option value="stock">Stock</option>
        </select>

        <select
          value={filterExchange}
          onChange={(e) => setFilterExchange(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="">All Exchanges</option>
          <option value="Binance">Binance</option>
          <option value="Bybit">Bybit</option>
          <option value="Kraken">Kraken</option>
          <option value="KuCoin">KuCoin</option>
          <option value="NYSE">NYSE</option>
          <option value="NASDAQ">NASDAQ</option>
          <option value="ASX">ASX</option>
        </select>

        <button
          onClick={fetchTickers}
          className="bg-gray-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-gray-700"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded-lg">
          <strong>Error:</strong> {error}
        </div>
      )}
      
      {testError && (
        <div className="mb-4 p-4 bg-yellow-100 border border-yellow-400 text-yellow-700 rounded-lg">
          <strong>Test Error:</strong> {testError}
        </div>
      )}

      {/* Add/Edit Form Modal */}
      {showAddForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">
              {editingTicker ? 'Edit Ticker' : 'Add New Ticker'}
            </h2>
            
            {error && (
              <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded-lg text-sm">
                <strong>Error:</strong> {error}
              </div>
            )}
            
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Symbol *
                  {formData.market_type === 'crypto' && !editingTicker && (
                    <span className="text-xs text-blue-600 ml-2">
                      (Base asset only - e.g., BTC not BTC/USDT)
                    </span>
                  )}
                </label>
                <input
                  type="text"
                  value={formData.symbol}
                  onChange={(e) => {
                    let symbol = e.target.value.toUpperCase();
                    // For crypto, only clean suffixes on new entries (not while editing)
                    if (formData.market_type === 'crypto' && !editingTicker) {
                      // Only remove suffixes when they're clearly part of a trading pair
                      symbol = symbol.replace(/\/USDT$|\/USD$|\/BUSD$|USDT$|USD$|BUSD$/g, '');
                    }
                    handleFormChange('symbol', symbol);
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                  placeholder={formData.market_type === 'crypto' ? 'e.g., BTC, ETH' : 'e.g., AAPL, TSLA'}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Market Type *
                </label>
                <select
                  value={formData.market_type}
                  onChange={(e) => {
                    const marketType = e.target.value as 'crypto' | 'stock';
                    handleFormChange('market_type', marketType);
                    handleFormChange('exchange', exchanges[marketType][0]);
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                >
                  <option value="crypto">Crypto</option>
                  <option value="stock">Stock</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Exchange *
                </label>
                <select
                  value={formData.exchange}
                  onChange={(e) => handleFormChange('exchange', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                >
                  {exchanges[formData.market_type].map(exchange => (
                    <option key={exchange} value={exchange}>{exchange}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Name (Optional)
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => handleFormChange('name', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder={formData.market_type === 'crypto' ? 'e.g., Bitcoin, Ethereum' : 'e.g., Apple Inc., Tesla Inc.'}
                />
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="is_active"
                  checked={formData.is_active}
                  onChange={(e) => handleFormChange('is_active', e.target.checked)}
                  className="mr-2 rounded"
                />
                <label htmlFor="is_active" className="text-sm font-medium text-gray-700">
                  Active
                </label>
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="submit"
                  className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700"
                >
                  {editingTicker ? 'Update' : 'Add'} Ticker
                </button>
                <button
                  type="button"
                  onClick={resetForm}
                  className="flex-1 bg-gray-300 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-400"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Bulk Add Form Modal */}
      {showBulkForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg w-full max-w-2xl">
            <h2 className="text-xl font-bold mb-4">Bulk Add Tickers</h2>
            
            {error && (
              <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded-lg text-sm">
                <strong>Error:</strong> {error}
              </div>
            )}
            
            <form onSubmit={handleBulkSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Ticker Data (CSV Format)
                </label>
                <div className="text-sm text-gray-600 mb-2">
                  Format: Symbol, Market Type, Exchange, Name (optional)
                  <br />
                  Examples:
                  <br />
                  • BTC, crypto, binance, Bitcoin
                  <br />
                  • ETH, crypto, bybit, Ethereum
                  <br />
                  • AAPL, stock, NASDAQ, Apple Inc.
                </div>
                <textarea
                  value={bulkTickersText}
                  onChange={(e) => setBulkTickersText(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  rows={8}
                  required
                  placeholder={`BTC, crypto, binance, Bitcoin
ETH, crypto, binance, Ethereum
AAPL, stock, NASDAQ, Apple Inc.
TSLA, stock, NASDAQ, Tesla Inc.`}
                />
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="submit"
                  className="flex-1 bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700"
                >
                  Add All Tickers
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowBulkForm(false);
                    setBulkTickersText('');
                    setError(null);
                  }}
                  className="flex-1 bg-gray-300 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-400"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Tickers Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Symbol
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Market
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Exchange
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
              {loading ? (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-gray-500">
                    Loading tickers...
                  </td>
                </tr>
              ) : filteredTickers.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-gray-500">
                    No tickers found
                  </td>
                </tr>
              ) : (
                filteredTickers.map((ticker) => (
                  <tr key={ticker.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {ticker.symbol}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {ticker.name || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        ticker.market_type === 'crypto' 
                          ? 'bg-orange-100 text-orange-800' 
                          : 'bg-blue-100 text-blue-800'
                      }`}>
                        {ticker.market_type}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {ticker.exchange}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        ticker.is_active 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {ticker.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleEdit(ticker)}
                          className="text-blue-600 hover:text-blue-900"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(ticker.id)}
                          className="text-red-600 hover:text-red-900"
                        >
                          <Trash2 className="w-4 h-4" />
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
  );
}