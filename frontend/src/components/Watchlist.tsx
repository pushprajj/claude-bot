'use client';

import { useState, useEffect } from 'react';
import { Eye, TrendingUp, TrendingDown, BarChart3, Trash2, RefreshCw } from 'lucide-react';
import { watchlistApi, Ticker } from '@/lib/api';

interface WatchlistItem {
  id: number;
  ticker_id: number;
  signal_id?: number;
  added_at: string;
  expires_at?: string;
  notes?: string;
  is_active: boolean;
  ticker: Ticker;
}

export default function Watchlist() {
  const [watchlistItems, setWatchlistItems] = useState<WatchlistItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchWatchlist();
  }, []);

  const fetchWatchlist = async () => {
    try {
      setLoading(true);
      
      // Get from localStorage
      const storedWatchlist = JSON.parse(localStorage.getItem('watchlist') || '[]');
      
      // Convert stored items to proper format
      const formattedItems: WatchlistItem[] = storedWatchlist.map((item: any) => ({
        id: item.id,
        ticker_id: item.ticker_id,
        signal_id: item.signal_id,
        added_at: item.added_at,
        is_active: item.is_active,
        notes: item.notes,
        ticker: {
          id: item.ticker_id,
          symbol: item.ticker_symbol,
          market_type: 'crypto', // Default for now
          exchange: 'binance',   // Default for now
          name: item.ticker_symbol,
          is_active: true,
          created_at: '',
          updated_at: ''
        }
      }));
      
      // If no stored items, show sample data
      if (formattedItems.length === 0) {
        const sampleItems: WatchlistItem[] = [
          {
            id: 999,
            ticker_id: 2,
            added_at: new Date().toISOString(),
            is_active: true,
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
            notes: 'Sample item - Generate signals and add to watchlist!'
          }
        ];
        setWatchlistItems(sampleItems);
      } else {
        setWatchlistItems(formattedItems);
      }
    } catch (err) {
      setError('Failed to fetch watchlist');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const removeFromWatchlist = async (id: number) => {
    if (confirm('Remove this item from watchlist?')) {
      try {
        // Remove from localStorage
        const existingWatchlist = JSON.parse(localStorage.getItem('watchlist') || '[]');
        const updatedWatchlist = existingWatchlist.filter((item: any) => item.id !== id);
        localStorage.setItem('watchlist', JSON.stringify(updatedWatchlist));
        
        // Update local state
        setWatchlistItems(prev => prev.filter(item => item.id !== id));
      } catch (err) {
        setError('Failed to remove from watchlist');
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
                  Market
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Exchange
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Added
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Notes
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
                        <div className="text-xs text-gray-500">{item.ticker.name}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        item.ticker.market_type === 'crypto' 
                          ? 'bg-orange-100 text-orange-800' 
                          : 'bg-blue-100 text-blue-800'
                      }`}>
                        {item.ticker.market_type}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {item.ticker.exchange}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(item.added_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      <div className="max-w-xs truncate">
                        {item.notes || 'No notes'}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        item.is_active 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {item.is_active ? 'Active' : 'Inactive'}
                      </span>
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
    </div>
  );
}