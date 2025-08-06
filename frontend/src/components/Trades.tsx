'use client';

import { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, TrendingDown, DollarSign, X, RefreshCw } from 'lucide-react';
import { tradeApi, Ticker } from '@/lib/api';

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

  useEffect(() => {
    fetchTrades();
  }, []);

  const fetchTrades = async () => {
    try {
      setLoading(true);
      
      // Get trades from localStorage first
      const storedTrades = JSON.parse(localStorage.getItem('trades') || '[]');
      
      // Convert stored trades to proper format
      const formattedTrades: Trade[] = storedTrades.map((trade: any) => ({
        id: trade.id,
        ticker_id: trade.ticker_id,
        signal_id: trade.signal_id,
        entry_price: trade.entry_price,
        current_price: trade.current_price || trade.entry_price,
        quantity: trade.quantity,
        stop_loss: trade.stop_loss,
        take_profit: trade.take_profit,
        status: trade.status,
        pnl: trade.pnl || 0,
        opened_at: trade.opened_at,
        closed_at: trade.closed_at,
        notes: trade.notes,
        ticker: {
          id: trade.ticker_id,
          symbol: trade.ticker_symbol,
          market_type: trade.base_asset && trade.base_asset !== 'USDT' ? 'crypto' : 'crypto',
          exchange: 'binance',
          name: trade.ticker_symbol,
          is_active: true,
          created_at: '',
          updated_at: ''
        }
      }));
      
      // If no stored trades, show sample mock data
      if (formattedTrades.length === 0) {
        const mockTrades: Trade[] = [
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
        setTrades(mockTrades);
      } else {
        setTrades(formattedTrades);
      }
    } catch (err) {
      setError('Failed to fetch trades');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const closeTrade = async (id: number) => {
    if (confirm('Close this trade?')) {
      try {
        // Update localStorage
        const existingTrades = JSON.parse(localStorage.getItem('trades') || '[]');
        const updatedTrades = existingTrades.map((trade: any) => 
          trade.id === id 
            ? { ...trade, status: 'closed', closed_at: new Date().toISOString() }
            : trade
        );
        localStorage.setItem('trades', JSON.stringify(updatedTrades));
        
        // Update local state
        setTrades(prev => prev.map(trade => 
          trade.id === id 
            ? { ...trade, status: 'closed' as const, closed_at: new Date().toISOString() }
            : trade
        ));
      } catch (err) {
        setError('Failed to close trade');
      }
    }
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
        <h1 className="text-2xl font-bold">Open Trades</h1>
        <button
          onClick={fetchTrades}
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
                  <td colSpan={8} className="px-6 py-12 text-center text-gray-500">
                    Loading trades...
                  </td>
                </tr>
              ) : trades.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-6 py-12 text-center text-gray-500">
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
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(trade.status)}`}>
                        {trade.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(trade.opened_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {trade.status === 'open' && (
                        <button
                          onClick={() => closeTrade(trade.id)}
                          className="bg-red-100 text-red-800 px-3 py-1 rounded-lg text-xs font-medium hover:bg-red-200 flex items-center gap-1"
                          title="Close Trade"
                        >
                          <X className="w-3 h-3" />
                          Close
                        </button>
                      )}
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