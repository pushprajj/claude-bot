import Navigation from '@/components/Navigation';
import { TrendingUp, Target, Eye, BarChart3, Activity, DollarSign, TrendingDown } from 'lucide-react';

export default function Home() {
  return (
    <div className="flex h-screen bg-gray-50">
      <Navigation />
      
      <div className="flex-1 overflow-auto">
        <div className="p-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-8">Trading Bot Dashboard</h1>
          
          {/* Overview Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <div className="flex items-center">
                <div className="p-2 bg-blue-100 rounded-md">
                  <Target className="h-6 w-6 text-blue-600" />
                </div>
                <div className="ml-4">
                  <h3 className="text-sm font-medium text-gray-500">Active Tickers</h3>
                  <p className="text-2xl font-semibold text-gray-900">0</p>
                </div>
              </div>
            </div>
            
            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <div className="flex items-center">
                <div className="p-2 bg-green-100 rounded-md">
                  <TrendingUp className="h-6 w-6 text-green-600" />
                </div>
                <div className="ml-4">
                  <h3 className="text-sm font-medium text-gray-500">Buy Signals</h3>
                  <p className="text-2xl font-semibold text-gray-900">0</p>
                </div>
              </div>
            </div>
            
            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <div className="flex items-center">
                <div className="p-2 bg-yellow-100 rounded-md">
                  <Eye className="h-6 w-6 text-yellow-600" />
                </div>
                <div className="ml-4">
                  <h3 className="text-sm font-medium text-gray-500">Watchlist</h3>
                  <p className="text-2xl font-semibold text-gray-900">0</p>
                </div>
              </div>
            </div>
            
            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <div className="flex items-center">
                <div className="p-2 bg-purple-100 rounded-md">
                  <BarChart3 className="h-6 w-6 text-purple-600" />
                </div>
                <div className="ml-4">
                  <h3 className="text-sm font-medium text-gray-500">Open Trades</h3>
                  <p className="text-2xl font-semibold text-gray-900">0</p>
                </div>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
              <div className="grid grid-cols-2 gap-4">
                <a
                  href="/tickers"
                  className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <Target className="h-8 w-8 text-blue-600 mb-2" />
                  <h3 className="font-medium text-gray-900">Manage Tickers</h3>
                  <p className="text-sm text-gray-500">Add or edit ticker symbols</p>
                </a>
                
                <a
                  href="/signals"
                  className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <Activity className="h-8 w-8 text-green-600 mb-2" />
                  <h3 className="font-medium text-gray-900">Generate Signals</h3>
                  <p className="text-sm text-gray-500">Run signal analysis</p>
                </a>
                
                <a
                  href="/watchlist"
                  className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <Eye className="h-8 w-8 text-yellow-600 mb-2" />
                  <h3 className="font-medium text-gray-900">View Watchlist</h3>
                  <p className="text-sm text-gray-500">Monitor selected assets</p>
                </a>
                
                <a
                  href="/trades"
                  className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <BarChart3 className="h-8 w-8 text-purple-600 mb-2" />
                  <h3 className="font-medium text-gray-900">Active Trades</h3>
                  <p className="text-sm text-gray-500">Manage open positions</p>
                </a>
              </div>
            </div>

            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h2>
              <div className="space-y-4">
                <div className="text-center py-8 text-gray-500">
                  <Activity className="h-12 w-12 mx-auto mb-2 text-gray-300" />
                  <p>No recent activity</p>
                  <p className="text-sm">Start by adding tickers and generating signals</p>
                </div>
              </div>
            </div>
          </div>

          {/* System Status */}
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">System Status</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="flex items-center">
                <div className="w-3 h-3 bg-green-400 rounded-full mr-3"></div>
                <span className="text-sm text-gray-600">API Status: Online</span>
              </div>
              <div className="flex items-center">
                <div className="w-3 h-3 bg-yellow-400 rounded-full mr-3"></div>
                <span className="text-sm text-gray-600">Signal Generation: Ready</span>
              </div>
              <div className="flex items-center">
                <div className="w-3 h-3 bg-blue-400 rounded-full mr-3"></div>
                <span className="text-sm text-gray-600">Data Feeds: Connected</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
