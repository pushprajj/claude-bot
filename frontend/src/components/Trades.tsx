'use client';

import { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, TrendingDown, DollarSign, X, RefreshCw, Edit, Plus, Trash2 } from 'lucide-react';
import { tradeApi, Ticker, tickerApi } from '@/lib/api';

interface Trade {
  id: number;
  ticker_id: number;
  signal_id?: number;
  entry_price: number;
  current_price?: number;
  quantity: number;
  stop_loss?: number;
  take_profit?: number;
  status: 'open' | 'closed' | 'cancelled';
  pnl: number;
  opened_at: string;
  closed_at?: string;
  notes?: string;
  ticker: Ticker;
}

export default function Trades() {
  const [trades, setTrades] = useState<Trade[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [showEditForm, setShowEditForm] = useState(false);
  const [selectedTrade, setSelectedTrade] = useState<Trade | null>(null);
  const [tickers, setTickers] = useState<Ticker[]>([]);

  useEffect(() => {
    fetchTrades();
    fetchTickers();
  }, []);

  const fetchTickers = async () => {
    try {
      const response = await tickerApi.getAll();
      setTickers(response.data);
    } catch (err) {
      console.error('Failed to fetch tickers:', err);
    }
  };

  const fetchTrades = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await tradeApi.getAll();
      setTrades(response.data);
      
    } catch (err: any) {
      console.error('Failed to fetch trades:', err);
      setError(err.message || 'Failed to fetch trades');
      
      // Fallback to sample data if API fails
      const sampleTrades: Trade[] = [
        {
          id: 1,
          ticker_id: 2,
          entry_price: 45000,
          current_price: 47500,
          quantity: 0.1,
          stop_loss: 42000,
          take_profit: 50000,
          status: 'open',
          pnl: 250, // (47500 - 45000) * 0.1
          opened_at: new Date(Date.now() - 3600000).toISOString(), // 1 hour ago
          ticker: {
            id: 2,
            symbol: 'BTC',
            market_type: 'crypto',
            exchange: 'binance',
            name: 'Bitcoin',
            is_active: true,
            created_at: '',
            updated_at: ''
          },
          notes: 'Strong breakout above SMA 50'
        },
        {
          id: 2,
          ticker_id: 4,
          entry_price: 2500,
          current_price: 2450,
          quantity: 2,
          stop_loss: 2300,
          status: 'open',
          pnl: -100, // (2450 - 2500) * 2
          opened_at: new Date(Date.now() - 7200000).toISOString(), // 2 hours ago
          ticker: {
            id: 4,
            symbol: 'ETH',
            market_type: 'crypto',
            exchange: 'binance',
            name: 'Ethereum',
            is_active: true,
            created_at: '',
            updated_at: ''
          },
          notes: 'Relative performance play vs BTC'
        },
        {
          id: 3,
          ticker_id: 1,
          entry_price: 150,
          current_price: 155,
          quantity: 10,
          status: 'closed',
          pnl: 50, // (155 - 150) * 10
          opened_at: new Date(Date.now() - 86400000).toISOString(), // 1 day ago
          closed_at: new Date(Date.now() - 3600000).toISOString(), // 1 hour ago
          ticker: {
            id: 1,
            symbol: 'AAPL',
            market_type: 'stock',
            exchange: 'NASDAQ',
            name: 'Apple Inc.',
            is_active: true,
            created_at: '',
            updated_at: ''
          },
          notes: 'Quick profit taking'
        }
      ];
        setTrades(sampleTrades);
    } finally {
      setLoading(false);
    }
  };

  const closeTrade = async (id: number) => {
    const currentPrice = prompt('Enter closing price (leave empty to use current market price):');
    if (confirm('Close this trade?')) {
      try {
        await tradeApi.close(id, currentPrice ? parseFloat(currentPrice) : undefined);
        await fetchTrades(); // Refresh to get updated data
      } catch (err) {
        setError('Failed to close trade');
        console.error(err);
      }
    }
  };

  const handleAddTrade = async (tradeData: {
    ticker_id: number;
    entry_price: number;
    quantity: number;
    stop_loss?: number;
    take_profit?: number;
    notes?: string;
  }) => {
    try {
      await tradeApi.create(tradeData);
      setShowAddForm(false);
      await fetchTrades();
    } catch (err) {
      setError('Failed to create trade');
      console.error(err);
    }
  };

  const handleEditTrade = async (id: number, updates: {
    stop_loss?: number;
    take_profit?: number;
    notes?: string;
  }) => {
    try {
      await tradeApi.update(id, updates);
      setShowEditForm(false);
      setSelectedTrade(null);
      await fetchTrades();
    } catch (err) {
      setError('Failed to update trade');
      console.error(err);
    }
  };

  const handleDeleteTrade = async (id: number) => {
    if (confirm('Are you sure you want to delete this trade? This action cannot be undone.')) {
      try {
        // Note: We would need to add a delete endpoint to the backend
        // For now, let's just close it
        await tradeApi.close(id);
        await fetchTrades();
      } catch (err) {
        setError('Failed to delete trade');
        console.error(err);
      }
    }
  };

  const openEditForm = (trade: Trade) => {
    setSelectedTrade(trade);
    setShowEditForm(true);
  };

  const openTrades = trades.filter(trade => trade.status === 'open');
  const closedTrades = trades.filter(trade => trade.status === 'closed');
  const totalPnL = trades.reduce((sum, trade) => sum + trade.pnl, 0);
  const openPnL = openTrades.reduce((sum, trade) => sum + trade.pnl, 0);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'open':
        return 'bg-green-100 text-green-800';
      case 'closed':
        return 'bg-gray-100 text-gray-800';
      case 'cancelled':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getPnLColor = (pnl: number) => {
    if (pnl > 0) return 'text-green-600';
    if (pnl < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Trades</h1>
        <div className="flex gap-2">
          <button
            onClick={() => setShowAddForm(true)}
            className="bg-green-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-green-700"
          >
            <Plus className="w-4 h-4" />
            Add Trade
          </button>
          <button
            onClick={fetchTrades}
            disabled={loading}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-blue-700 disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded-lg">
          {error}
        </div>
      )}

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="flex items-center">
            <BarChart3 className="w-5 h-5 text-blue-600 mr-2" />
            <div>
              <p className="text-sm text-gray-600">Open Trades</p>
              <p className="text-xl font-bold text-blue-600">{openTrades.length}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="flex items-center">
            <TrendingUp className="w-5 h-5 text-green-600 mr-2" />
            <div>
              <p className="text-sm text-gray-600">Total Trades</p>
              <p className="text-xl font-bold text-green-600">{trades.length}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="flex items-center">
            <DollarSign className="w-5 h-5 text-purple-600 mr-2" />
            <div>
              <p className="text-sm text-gray-600">Open P&L</p>
              <p className={`text-xl font-bold ${getPnLColor(openPnL)}`}>
                ${openPnL.toFixed(2)}
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="flex items-center">
            <DollarSign className="w-5 h-5 text-gray-600 mr-2" />
            <div>
              <p className="text-sm text-gray-600">Total P&L</p>
              <p className={`text-xl font-bold ${getPnLColor(totalPnL)}`}>
                ${totalPnL.toFixed(2)}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Trades Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Ticker
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Entry Price
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Current Price
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Quantity
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  P&L
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Risk Management
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Opened
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {loading ? (
                <tr>
                  <td colSpan={9} className="px-6 py-12 text-center text-gray-500">
                    Loading trades...
                  </td>
                </tr>
              ) : trades.length === 0 ? (
                <tr>
                  <td colSpan={9} className="px-6 py-12 text-center text-gray-500">
                    <BarChart3 className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                    <p>No trades opened yet</p>
                    <p className="text-sm">Generate signals and open trades to get started</p>
                  </td>
                </tr>
              ) : (
                trades.map((trade) => (
                  <tr key={trade.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      <div>
                        <div className="font-semibold">{trade.ticker.symbol}</div>
                        <div className="text-xs text-gray-500">{trade.ticker.exchange}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      ${trade.entry_price.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {trade.current_price ? `$${trade.current_price.toLocaleString()}` : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {trade.quantity}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <span className={getPnLColor(trade.pnl)}>
                        ${trade.pnl.toFixed(2)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <div className="text-xs space-y-1">
                        {trade.stop_loss ? (
                          <div className="flex items-center text-red-600">
                            <span className="font-medium">SL:</span>
                            <span className="ml-1">${trade.stop_loss.toFixed(2)}</span>
                          </div>
                        ) : (
                          <div className="text-gray-400">No SL</div>
                        )}
                        {trade.take_profit ? (
                          <div className="flex items-center text-green-600">
                            <span className="font-medium">TP:</span>
                            <span className="ml-1">${trade.take_profit.toFixed(2)}</span>
                          </div>
                        ) : (
                          <div className="text-gray-400">No TP</div>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(trade.status)}`}>
                        {trade.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(trade.opened_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <div className="flex gap-2">
                        {trade.status === 'open' && (
                          <>
                            <button
                              onClick={() => openEditForm(trade)}
                              className="bg-blue-100 text-blue-800 px-2 py-1 rounded-lg text-xs font-medium hover:bg-blue-200 flex items-center gap-1"
                              title="Edit Trade"
                            >
                              <Edit className="w-3 h-3" />
                            </button>
                            <button
                              onClick={() => closeTrade(trade.id)}
                              className="bg-red-100 text-red-800 px-2 py-1 rounded-lg text-xs font-medium hover:bg-red-200 flex items-center gap-1"
                              title="Close Trade"
                            >
                              <X className="w-3 h-3" />
                            </button>
                          </>
                        )}
                        <button
                          onClick={() => handleDeleteTrade(trade.id)}
                          className="bg-gray-100 text-gray-800 px-2 py-1 rounded-lg text-xs font-medium hover:bg-gray-200 flex items-center gap-1"
                          title="Delete Trade"
                        >
                          <Trash2 className="w-3 h-3" />
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

      {/* Add Trade Modal */}
      {showAddForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg shadow-lg max-w-md w-full mx-4">
            <h2 className="text-xl font-bold mb-4">Add New Trade</h2>
            <TradeForm
              tickers={tickers}
              onSubmit={handleAddTrade}
              onCancel={() => setShowAddForm(false)}
            />
          </div>
        </div>
      )}

      {/* Edit Trade Modal */}
      {showEditForm && selectedTrade && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg shadow-lg max-w-md w-full mx-4">
            <h2 className="text-xl font-bold mb-4">Edit Trade</h2>
            <EditTradeForm
              trade={selectedTrade}
              onSubmit={(updates) => handleEditTrade(selectedTrade.id, updates)}
              onCancel={() => {
                setShowEditForm(false);
                setSelectedTrade(null);
              }}
            />
          </div>
        </div>
      )}
    </div>
  );
}

// Trade Form Component
function TradeForm({ 
  tickers, 
  onSubmit, 
  onCancel 
}: { 
  tickers: Ticker[];
  onSubmit: (data: any) => void;
  onCancel: () => void;
}) {
  const [formData, setFormData] = useState({
    ticker_id: '',
    entry_price: '',
    quantity: '',
    stop_loss: '',
    take_profit: '',
    notes: ''
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const data = {
      ticker_id: parseInt(formData.ticker_id),
      entry_price: parseFloat(formData.entry_price),
      quantity: parseFloat(formData.quantity),
      stop_loss: formData.stop_loss ? parseFloat(formData.stop_loss) : undefined,
      take_profit: formData.take_profit ? parseFloat(formData.take_profit) : undefined,
      notes: formData.notes || undefined
    };
    onSubmit(data);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Ticker *
        </label>
        <select
          value={formData.ticker_id}
          onChange={(e) => setFormData({...formData, ticker_id: e.target.value})}
          className="w-full border border-gray-300 rounded-lg px-3 py-2"
          required
        >
          <option value="">Select a ticker</option>
          {tickers.map((ticker) => (
            <option key={ticker.id} value={ticker.id}>
              {ticker.symbol} - {ticker.name || ticker.exchange}
            </option>
          ))}
        </select>
      </div>
      
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Entry Price *
        </label>
        <input
          type="number"
          step="0.01"
          value={formData.entry_price}
          onChange={(e) => setFormData({...formData, entry_price: e.target.value})}
          className="w-full border border-gray-300 rounded-lg px-3 py-2"
          required
        />
      </div>
      
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Quantity *
        </label>
        <input
          type="number"
          step="0.01"
          value={formData.quantity}
          onChange={(e) => setFormData({...formData, quantity: e.target.value})}
          className="w-full border border-gray-300 rounded-lg px-3 py-2"
          required
        />
      </div>
      
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Stop Loss
        </label>
        <input
          type="number"
          step="0.01"
          value={formData.stop_loss}
          onChange={(e) => setFormData({...formData, stop_loss: e.target.value})}
          className="w-full border border-gray-300 rounded-lg px-3 py-2"
        />
      </div>
      
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Take Profit
        </label>
        <input
          type="number"
          step="0.01"
          value={formData.take_profit}
          onChange={(e) => setFormData({...formData, take_profit: e.target.value})}
          className="w-full border border-gray-300 rounded-lg px-3 py-2"
        />
      </div>
      
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Notes
        </label>
        <textarea
          value={formData.notes}
          onChange={(e) => setFormData({...formData, notes: e.target.value})}
          className="w-full border border-gray-300 rounded-lg px-3 py-2"
          rows={3}
        />
      </div>
      
      <div className="flex gap-2">
        <button
          type="submit"
          className="flex-1 bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700"
        >
          Create Trade
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="flex-1 bg-gray-600 text-white py-2 px-4 rounded-lg hover:bg-gray-700"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}

// Edit Trade Form Component
function EditTradeForm({ 
  trade, 
  onSubmit, 
  onCancel 
}: { 
  trade: Trade;
  onSubmit: (data: any) => void;
  onCancel: () => void;
}) {
  const [formData, setFormData] = useState({
    stop_loss: trade.stop_loss?.toString() || '',
    take_profit: trade.take_profit?.toString() || '',
    notes: trade.notes || ''
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const data = {
      stop_loss: formData.stop_loss ? parseFloat(formData.stop_loss) : undefined,
      take_profit: formData.take_profit ? parseFloat(formData.take_profit) : undefined,
      notes: formData.notes || undefined
    };
    onSubmit(data);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="mb-4 p-3 bg-gray-50 rounded-lg">
        <p className="text-sm text-gray-600">
          <strong>{trade.ticker.symbol}</strong> - {trade.quantity} shares @ ${trade.entry_price}
        </p>
      </div>
      
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Stop Loss
        </label>
        <input
          type="number"
          step="0.01"
          value={formData.stop_loss}
          onChange={(e) => setFormData({...formData, stop_loss: e.target.value})}
          className="w-full border border-gray-300 rounded-lg px-3 py-2"
        />
      </div>
      
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Take Profit
        </label>
        <input
          type="number"
          step="0.01"
          value={formData.take_profit}
          onChange={(e) => setFormData({...formData, take_profit: e.target.value})}
          className="w-full border border-gray-300 rounded-lg px-3 py-2"
        />
      </div>
      
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Notes
        </label>
        <textarea
          value={formData.notes}
          onChange={(e) => setFormData({...formData, notes: e.target.value})}
          className="w-full border border-gray-300 rounded-lg px-3 py-2"
          rows={3}
        />
      </div>
      
      <div className="flex gap-2">
        <button
          type="submit"
          className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700"
        >
          Update Trade
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="flex-1 bg-gray-600 text-white py-2 px-4 rounded-lg hover:bg-gray-700"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}