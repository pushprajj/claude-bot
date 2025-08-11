'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  TrendingUp, 
  Target, 
  Eye, 
  BarChart3, 
  Settings, 
  Menu, 
  X,
  Home
} from 'lucide-react';

const navigation = [
  { name: 'Dashboard', href: '/', icon: Home },
  { name: 'Tickers', href: '/tickers', icon: Target },
  { name: 'Signals', href: '/signals', icon: TrendingUp },
  { name: 'Watchlist', href: '/watchlist', icon: Eye },
  { name: 'Trades', href: '/trades', icon: BarChart3 },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export default function Navigation() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const pathname = usePathname();

  return (
    <>
      {/* Mobile menu */}
      <div className="lg:hidden">
        <div className="flex items-center justify-between bg-white px-4 py-3 shadow-sm border-b">
          <div className="flex items-center">
            <TrendingUp className="h-7 w-7 text-blue-600 mr-2" />
            <h1 className="text-lg sm:text-xl font-semibold text-gray-900">Trading Bot</h1>
          </div>
          <button
            type="button"
            className="p-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-50 transition-colors"
            onClick={() => setSidebarOpen(true)}
            aria-label="Open navigation menu"
          >
            <Menu className="h-6 w-6" />
          </button>
        </div>

        {sidebarOpen && (
          <div className="fixed inset-0 flex z-50">
            <div className="fixed inset-0 bg-gray-600 bg-opacity-75 transition-opacity" onClick={() => setSidebarOpen(false)} />
            <div className="relative flex-1 flex flex-col max-w-xs w-full bg-white shadow-xl">
              <div className="absolute top-0 right-0 -mr-12 pt-2">
                <button
                  type="button"
                  className="ml-1 flex items-center justify-center h-10 w-10 rounded-full focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white transition-colors hover:bg-gray-600"
                  onClick={() => setSidebarOpen(false)}
                  aria-label="Close navigation menu"
                >
                  <X className="h-6 w-6 text-white" />
                </button>
              </div>
              <div className="flex-1 h-0 pt-5 pb-4 overflow-y-auto">
                <div className="px-4 pb-4 border-b border-gray-200">
                  <div className="flex items-center">
                    <TrendingUp className="h-8 w-8 text-blue-600" />
                    <h2 className="ml-2 text-lg font-semibold text-gray-900">Trading Bot</h2>
                  </div>
                </div>
                <nav className="mt-6 px-4">
                  <div className="space-y-1">
                    {navigation.map((item) => {
                      const isActive = pathname === item.href;
                      return (
                        <Link
                          key={item.name}
                          href={item.href}
                          className={`group flex items-center px-3 py-3 text-sm font-medium rounded-lg transition-colors ${
                            isActive
                              ? 'bg-blue-100 text-blue-900'
                              : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                          }`}
                          onClick={() => setSidebarOpen(false)}
                        >
                          <item.icon className="mr-4 h-5 w-5 flex-shrink-0" />
                          {item.name}
                        </Link>
                      );
                    })}
                  </div>
                </nav>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Desktop sidebar */}
      <div className="hidden lg:flex lg:flex-shrink-0">
        <div className={`flex flex-col transition-all duration-300 ease-in-out ${
          sidebarCollapsed ? 'w-16' : 'w-64'
        }`}>
          <div className="flex flex-col h-0 flex-1 bg-white border-r border-gray-200">
            <div className="flex-1 flex flex-col pt-5 pb-4 overflow-y-auto">
              {/* Header with collapse toggle */}
              <div className={`flex items-center flex-shrink-0 px-4 ${
                sidebarCollapsed ? 'justify-center' : 'justify-between'
              }`}>
                {!sidebarCollapsed && (
                  <div className="flex items-center">
                    <TrendingUp className="h-8 w-8 text-blue-600" />
                    <h2 className="ml-2 text-xl font-semibold text-gray-900">Trading Bot</h2>
                  </div>
                )}
                {sidebarCollapsed && (
                  <TrendingUp className="h-8 w-8 text-blue-600" />
                )}
                <button
                  onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
                  className={`p-1 rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors ${
                    sidebarCollapsed ? 'mt-0' : ''
                  }`}
                  title={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
                >
                  <Menu className="h-5 w-5" />
                </button>
              </div>
              
              {/* Navigation */}
              <nav className={`mt-8 flex-1 ${
                sidebarCollapsed ? 'px-2' : 'px-4'
              }`}>
                <div className="space-y-1">
                  {navigation.map((item) => {
                    const isActive = pathname === item.href;
                    return (
                      <Link
                        key={item.name}
                        href={item.href}
                        className={`group flex items-center px-2 py-2 text-sm font-medium rounded-md transition-all duration-200 relative ${
                          isActive
                            ? 'bg-blue-100 text-blue-900'
                            : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                        } ${
                          sidebarCollapsed ? 'justify-center' : ''
                        }`}
                        title={sidebarCollapsed ? item.name : ''}
                      >
                        <item.icon className={`h-5 w-5 ${
                          sidebarCollapsed ? 'mr-0' : 'mr-3'
                        }`} />
                        {!sidebarCollapsed && (
                          <span className="transition-opacity duration-200">
                            {item.name}
                          </span>
                        )}
                        {sidebarCollapsed && (
                          <>
                            <span className="sr-only">{item.name}</span>
                            {/* Tooltip for collapsed state */}
                            <div className="absolute left-full ml-2 px-2 py-1 bg-gray-900 text-white text-xs rounded-md opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap z-10">
                              {item.name}
                            </div>
                          </>
                        )}
                      </Link>
                    );
                  })}
                </div>
              </nav>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}