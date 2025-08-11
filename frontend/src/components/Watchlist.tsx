'use client';

import { useState, useEffect } from 'react';
import { Eye, TrendingUp, TrendingDown, BarChart3, Trash2, RefreshCw, Edit, Plus } from 'lucide-react';
import { watchlistApi, Ticker } from '@/lib/api';
import { EditWatchlistForm, TradeFromWatchlistForm } from './EditWatchlistForm';

interface WatchlistItem {
  id: number;
  ticker_id: number;
  signal_id?: number;
  target_price?: number;  // Keep for backward compatibility
  support_price?: number;
  resistance_price?: number;
  target_min?: number;  // Target range minimum
  target_max?: number;  // Target range maximum
  signal_price?: number;
  signal_type?: string;
  signal_date?: string;
  added_at: string;
  expires_at?: string;
  notes?: string;
  is_active: boolean;
  ticker: Ticker;
}

interface WatchlistSignalResult {
  watchlist_item_id: number;
  ticker_symbol: string;
  ticker_name: string;
  exchange: string;
  condition: string;
  trigger_price: string | number;
  current_price: number;
  description: string;
  signal_price?: number;
  signal_date?: string;
  watchlist_item: WatchlistItem;
}

export default function Watchlist() {
  const [watchlistItems, setWatchlistItems] = useState<WatchlistItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Signal checking state
  const [signalResults, setSignalResults] = useState<WatchlistSignalResult[]>([]);
  const [signalLoading, setSignalLoading] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingItem, setEditingItem] = useState<WatchlistSignalResult | null>(null);
  const [showTradeModal, setShowTradeModal] = useState(false);
  const [tradingItem, setTradingItem] = useState<WatchlistSignalResult | null>(null);
  const [selectedMarket, setSelectedMarket] = useState('');
  const [selectedExchange, setSelectedExchange] = useState('');
  const [selectedBaseAsset, setSelectedBaseAsset] = useState('');

  useEffect(() => {
    fetchWatchlist();
  }, []);

  const fetchWatchlist = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await watchlistApi.getAll({ is_active: true });
      setWatchlistItems(response.data);
      
    } catch (err: any) {
      console.error('Failed to fetch watchlist:', err);
      setError(err.message || 'Failed to fetch watchlist');
      setWatchlistItems([]);
    } finally {
      setLoading(false);
    }
  };

  const removeFromWatchlist = async (id: number) => {
    if (confirm('Remove this item from watchlist?')) {
      try {
        await watchlistApi.delete(id);
        setWatchlistItems(prev => prev.filter(item => item.id !== id));
      } catch (err) {
        setError('Failed to remove from watchlist');
        console.error(err);
      }
    }
  };

  const promoteToTrade = async (item: WatchlistItem) => {
    try {
      // For now, show success message
      alert(`Opening trade for ${item.ticker.symbol}!`);
      // In future, this will call watchlistApi.promoteToTrade()
    } catch (err) {
      setError('Failed to open trade');
    }
  };

  const checkWatchlistSignals = async () => {
    try {
      setSignalLoading(true);
      setError(null);
      
      const requestData: any = {};
      if (selectedMarket) requestData.market_type = selectedMarket;
      if (selectedExchange) requestData.exchange = selectedExchange;
      if (selectedBaseAsset) requestData.base_asset = selectedBaseAsset;
      
      console.log('Checking watchlist signals with filters:', requestData);
      
      const response = await watchlistApi.checkSignals(requestData);
      setSignalResults(response.data.results || []);
      
      alert(`${response.data.message}\nTotal checked: ${response.data.total_checked}\nTriggered: ${response.data.total_triggered}`);
      
    } catch (err: any) {
      console.error('Failed to check watchlist signals:', err);
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to check signals';
      setError(errorMessage);
      alert(`Failed to check watchlist signals: ${errorMessage}`);
    } finally {
      setSignalLoading(false);
    }
  };

  const editWatchlistItem = async (result: WatchlistSignalResult) => {
    try {
      // Fetch the full watchlist item details
      const response = await watchlistApi.getById(result.watchlist_item_id);
      const fullItem = response.data;
      
      // Create an enhanced result object with full details
      const enhancedResult = {
        ...result,
        watchlist_item: fullItem
      };
      
      setEditingItem(enhancedResult);
      setShowEditModal(true);
    } catch (err) {
      setError('Failed to load watchlist item details');
      console.error(err);
    }
  };

  const deleteWatchlistItem = async (result: WatchlistSignalResult) => {
    if (confirm(`Remove ${result.ticker_symbol} from watchlist?`)) {
      try {
        await watchlistApi.delete(result.watchlist_item_id);
        // Remove from both lists
        setWatchlistItems(prev => prev.filter(item => item.id !== result.watchlist_item_id));
        setSignalResults(prev => prev.filter(r => r.watchlist_item_id !== result.watchlist_item_id));
        alert(`${result.ticker_symbol} removed from watchlist`);
      } catch (err) {
        setError('Failed to remove from watchlist');
        console.error(err);
      }
    }
  };

  const tradeFromResult = (result: WatchlistSignalResult) => {
    setTradingItem(result);
    setShowTradeModal(true);
  };

  const handleEditSubmit = async (updates: {
    support_price?: number;
    resistance_price?: number;
    target_min?: number;
    target_max?: number;
    notes?: string;
  }) => {
    if (!editingItem) return;
    
    try {
      await watchlistApi.update(editingItem.watchlist_item_id, updates);
      setShowEditModal(false);
      setEditingItem(null);
      await fetchWatchlist(); // Refresh the list
    } catch (err) {
      setError('Failed to update watchlist item');
      console.error(err);
    }
  };

  const handleTradeSubmit = async (tradeData: {
    entry_price: number;
    quantity: number;
    stop_loss?: number;
    take_profit?: number;
    notes?: string;
  }) => {
    if (!tradingItem) return;
    
    try {
      // Create the trade using the existing promote to trade functionality
      await watchlistApi.promoteToTrade(tradingItem.watchlist_item_id, tradeData);
      setShowTradeModal(false);
      setTradingItem(null);
      await fetchWatchlist(); // Refresh the list
      // Remove from signal results since it's now a trade
      setSignalResults(prev => prev.filter(r => r.watchlist_item_id !== tradingItem.watchlist_item_id));
    } catch (err) {
      setError('Failed to create trade');
      console.error(err);
    }
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Watchlist</h1>
        <button
          onClick={fetchWatchlist}
          disabled={loading}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-blue-700 disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded-lg">
          {error}
        </div>
      )}

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="flex items-center">
            <Eye className="w-5 h-5 text-yellow-600 mr-2" />
            <div>
              <p className="text-sm text-gray-600">Total Items</p>
              <p className="text-xl font-bold text-yellow-600">{watchlistItems.length}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="flex items-center">
            <TrendingUp className="w-5 h-5 text-green-600 mr-2" />
            <div>
              <p className="text-sm text-gray-600">Active Items</p>
              <p className="text-xl font-bold text-green-600">
                {watchlistItems.filter(item => item.is_active).length}
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="flex items-center">
            <BarChart3 className="w-5 h-5 text-blue-600 mr-2" />
            <div>
              <p className="text-sm text-gray-600">Ready to Trade</p>
              <p className="text-xl font-bold text-blue-600">
                {watchlistItems.filter(item => item.is_active).length}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Signal Checking Controls */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">Check Watchlist Signals</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Market Type</label>
            <select
              value={selectedMarket}
              onChange={(e) => setSelectedMarket(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Markets</option>
              <option value="stock">Stock</option>
              <option value="crypto">Crypto</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Exchange</label>
            <select
              value={selectedExchange}
              onChange={(e) => setSelectedExchange(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Exchanges</option>
              <option value="NYSE">NYSE</option>
              <option value="NASDAQ">NASDAQ</option>
              <option value="ASX">ASX</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Base Asset</label>
            <select
              value={selectedBaseAsset}
              onChange={(e) => setSelectedBaseAsset(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              disabled
            >
              <option value="">All Assets (Coming Soon)</option>
              <option value="BTC">BTC</option>
              <option value="ETH">ETH</option>
              <option value="USDT">USDT</option>
            </select>
          </div>
          
          <div className="flex items-end">
            <button
              onClick={checkWatchlistSignals}
              disabled={signalLoading}
              className="w-full bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {signalLoading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  Checking...
                </>
              ) : (
                <>
                  <BarChart3 className="w-4 h-4" />
                  Check Signals
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Signal Results */}
      {signalResults.length > 0 && (
        <div className="bg-white rounded-lg shadow mb-6">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-lg font-semibold">Triggered Conditions ({signalResults.length})</h2>
            <p className="text-sm text-gray-600">Watchlist items that have met their conditions</p>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Ticker
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Condition Met
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Current Price
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Trigger Price
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Description
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {signalResults.map((result, index) => (
                  <tr key={`${result.watchlist_item_id}-${index}`} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900">{result.ticker_symbol}</div>
                        <div className="text-sm text-gray-500">{result.ticker_name}</div>
                        <div className="text-xs text-gray-400">{result.exchange}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs rounded-full font-medium ${
                        result.condition.includes('support') 
                          ? 'bg-red-100 text-red-800'
                          : result.condition.includes('resistance')
                          ? 'bg-green-100 text-green-800'
                          : 'bg-blue-100 text-blue-800'
                      }`}>
                        {result.condition}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      ${result.current_price.toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {typeof result.trigger_price === 'number' 
                        ? `$${result.trigger_price.toFixed(2)}`
                        : `$${result.trigger_price}`
                      }
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500 max-w-xs">
                      {result.description}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <div className="flex gap-2">
                        <button
                          onClick={() => editWatchlistItem(result)}
                          className="bg-blue-100 text-blue-800 px-2 py-1 rounded-lg text-xs font-medium hover:bg-blue-200 flex items-center gap-1"
                          title="Edit price levels"
                        >
                          <Edit className="w-3 h-3" />
                          Edit
                        </button>
                        <button
                          onClick={() => tradeFromResult(result)}
                          className="bg-green-100 text-green-800 px-2 py-1 rounded-lg text-xs font-medium hover:bg-green-200 flex items-center gap-1"
                          title="Open trade"
                        >
                          <BarChart3 className="w-3 h-3" />
                          Trade
                        </button>
                        <button
                          onClick={() => deleteWatchlistItem(result)}
                          className="bg-red-100 text-red-800 px-2 py-1 rounded-lg text-xs font-medium hover:bg-red-200 flex items-center gap-1"
                          title="Remove from watchlist"
                        >
                          <Trash2 className="w-3 h-3" />
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Watchlist Table */}
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
                  Current Price
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Support/Resistance
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Target Range
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Signal Date
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Notes
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {loading ? (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-gray-500">
                    Loading watchlist...
                  </td>
                </tr>
              ) : watchlistItems.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-gray-500">
                    <Eye className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                    <p>No items in watchlist</p>
                    <p className="text-sm">Generate signals and add them to watchlist to get started</p>
                  </td>
                </tr>
              ) : (
                watchlistItems.map((item) => (
                  <tr key={item.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      <div>
                        <div className="font-semibold">{item.ticker.symbol}</div>
                        <div className="text-xs text-gray-500">{item.ticker.exchange}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {item.signal_type ? (
                        <div className="flex items-center">
                          {item.signal_type === 'buy' ? (
                            <TrendingUp className="w-4 h-4 text-green-600 mr-1" />
                          ) : (
                            <TrendingDown className="w-4 h-4 text-red-600 mr-1" />
                          )}
                          <span className={`px-2 py-1 text-xs rounded-full ${
                            item.signal_type === 'buy' 
                              ? 'bg-green-100 text-green-800' 
                              : 'bg-red-100 text-red-800'
                          }`}>
                            {item.signal_type.toUpperCase()}
                          </span>
                        </div>
                      ) : (
                        <span className="text-gray-400">No signal</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {item.signal_price ? (
                        <div>
                          <div className="font-medium">${item.signal_price.toFixed(2)}</div>
                          <div className="text-xs text-gray-500">Signal price</div>
                        </div>
                      ) : (
                        <span className="text-gray-400">N/A</span>
                      )}
                    </td>
                    {/* Support/Resistance Column */}
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <div className="space-y-1">
                        {item.support_price && (
                          <div className="text-red-600 text-xs">
                            Support: ${item.support_price.toFixed(2)}
                          </div>
                        )}
                        {item.resistance_price && (
                          <div className="text-green-600 text-xs">
                            Resistance: ${item.resistance_price.toFixed(2)}
                          </div>
                        )}
                        {!item.support_price && !item.resistance_price && item.target_price && (
                          <div className="font-medium text-blue-600 text-xs">
                            Legacy: ${item.target_price.toFixed(2)}
                          </div>
                        )}
                        {!item.support_price && !item.resistance_price && !item.target_price && (
                          <span className="text-gray-400 text-xs">-</span>
                        )}
                      </div>
                    </td>
                    
                    {/* Target Range Column */}
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <div className="space-y-1">
                        {item.target_min && item.target_max && (
                          <div className="text-blue-600 text-xs">
                            ${item.target_min.toFixed(2)} - ${item.target_max.toFixed(2)}
                          </div>
                        )}
                        {item.target_min && !item.target_max && (
                          <div className="text-blue-600 text-xs">
                            Min: ${item.target_min.toFixed(2)}
                          </div>
                        )}
                        {!item.target_min && item.target_max && (
                          <div className="text-blue-600 text-xs">
                            Max: ${item.target_max.toFixed(2)}
                          </div>
                        )}
                        {!item.target_min && !item.target_max && (
                          <span className="text-gray-400 text-xs">-</span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {item.signal_date ? new Date(item.signal_date).toLocaleDateString() : 'N/A'}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      <div className="max-w-xs truncate">
                        {item.notes || 'No notes'}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <div className="flex gap-2">
                        <button
                          onClick={() => promoteToTrade(item)}
                          className="bg-blue-100 text-blue-800 px-3 py-1 rounded-lg text-xs font-medium hover:bg-blue-200 flex items-center gap-1"
                          title="Open Trade"
                        >
                          <BarChart3 className="w-3 h-3" />
                          Trade
                        </button>
                        <button
                          onClick={() => removeFromWatchlist(item.id)}
                          className="bg-red-100 text-red-800 px-3 py-1 rounded-lg text-xs font-medium hover:bg-red-200 flex items-center gap-1"
                          title="Remove from Watchlist"
                        >
                          <Trash2 className="w-3 h-3" />
                          Remove
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

      {/* Edit Modal */}
      {showEditModal && editingItem && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg shadow-lg max-w-md w-full mx-4">
            <h2 className="text-xl font-bold mb-4">Edit Watchlist Item</h2>
            <EditWatchlistForm
              item={editingItem}
              onSubmit={handleEditSubmit}
              onCancel={() => {
                setShowEditModal(false);
                setEditingItem(null);
              }}
            />
          </div>
        </div>
      )}

      {/* Trade Modal */}
      {showTradeModal && tradingItem && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg shadow-lg max-w-md w-full mx-4">
            <h2 className="text-xl font-bold mb-4">Open Trade</h2>
            <TradeFromWatchlistForm
              item={tradingItem}
              onSubmit={handleTradeSubmit}
              onCancel={() => {
                setShowTradeModal(false);
                setTradingItem(null);
              }}
            />
          </div>
        </div>
      )}
    </div>
  );
}