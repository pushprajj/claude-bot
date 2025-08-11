'use client';

import { useState } from 'react';

interface WatchlistSignalResult {
  watchlist_item_id: number;
  ticker_symbol: string;
  ticker_name: string;
  current_price: number;
  condition: string;
  watchlist_item?: {
    support_price?: number;
    resistance_price?: number;
    target_min?: number;
    target_max?: number;
    notes?: string;
  };
}

// Edit Watchlist Form Component
export function EditWatchlistForm({
  item,
  onSubmit,
  onCancel
}: {
  item: WatchlistSignalResult;
  onSubmit: (data: any) => void;
  onCancel: () => void;
}) {
  const [formData, setFormData] = useState({
    support_price: item.watchlist_item?.support_price?.toString() || '',
    resistance_price: item.watchlist_item?.resistance_price?.toString() || '',
    target_min: item.watchlist_item?.target_min?.toString() || '',
    target_max: item.watchlist_item?.target_max?.toString() || '',
    notes: item.watchlist_item?.notes || ''
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Only include changed values
    const data: any = {};
    
    const originalData = item.watchlist_item;
    
    if (formData.support_price !== (originalData?.support_price?.toString() || '')) {
      data.support_price = formData.support_price ? parseFloat(formData.support_price) : null;
    }
    if (formData.resistance_price !== (originalData?.resistance_price?.toString() || '')) {
      data.resistance_price = formData.resistance_price ? parseFloat(formData.resistance_price) : null;
    }
    if (formData.target_min !== (originalData?.target_min?.toString() || '')) {
      data.target_min = formData.target_min ? parseFloat(formData.target_min) : null;
    }
    if (formData.target_max !== (originalData?.target_max?.toString() || '')) {
      data.target_max = formData.target_max ? parseFloat(formData.target_max) : null;
    }
    if (formData.notes !== (originalData?.notes || '')) {
      data.notes = formData.notes || null;
    }
    
    onSubmit(data);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="mb-4 p-3 bg-gray-50 rounded-lg">
        <p className="text-sm text-gray-600">
          <strong>{item.ticker_symbol}</strong> - {item.ticker_name}
        </p>
        <p className="text-xs text-gray-500">Current Price: ${item.current_price.toFixed(2)}</p>
        <p className="text-xs text-blue-600 mt-1">Triggered: {item.condition}</p>
      </div>
      
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Support Price
        </label>
        <input
          type="number"
          step="0.01"
          value={formData.support_price}
          onChange={(e) => setFormData({...formData, support_price: e.target.value})}
          className="w-full border border-gray-300 rounded-lg px-3 py-2"
          placeholder={item.watchlist_item?.support_price ? `Current: ${item.watchlist_item.support_price}` : "e.g. 45.50"}
        />
      </div>
      
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Resistance Price
        </label>
        <input
          type="number"
          step="0.01"
          value={formData.resistance_price}
          onChange={(e) => setFormData({...formData, resistance_price: e.target.value})}
          className="w-full border border-gray-300 rounded-lg px-3 py-2"
          placeholder={item.watchlist_item?.resistance_price ? `Current: ${item.watchlist_item.resistance_price}` : "e.g. 52.75"}
        />
      </div>
      
      <div className="grid grid-cols-2 gap-2">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Target Min
          </label>
          <input
            type="number"
            step="0.01"
            value={formData.target_min}
            onChange={(e) => setFormData({...formData, target_min: e.target.value})}
            className="w-full border border-gray-300 rounded-lg px-3 py-2"
            placeholder={item.watchlist_item?.target_min ? `Current: ${item.watchlist_item.target_min}` : "e.g. 48.00"}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Target Max
          </label>
          <input
            type="number"
            step="0.01"
            value={formData.target_max}
            onChange={(e) => setFormData({...formData, target_max: e.target.value})}
            className="w-full border border-gray-300 rounded-lg px-3 py-2"
            placeholder={item.watchlist_item?.target_max ? `Current: ${item.watchlist_item.target_max}` : "e.g. 55.00"}
          />
        </div>
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
          placeholder={item.watchlist_item?.notes ? `Current: ${item.watchlist_item.notes}` : "Add any notes about this watchlist item..."}
        />
      </div>
      
      <div className="flex gap-2">
        <button
          type="submit"
          className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700"
        >
          Update Watchlist
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

// Trade From Watchlist Form Component
export function TradeFromWatchlistForm({
  item,
  onSubmit,
  onCancel
}: {
  item: WatchlistSignalResult;
  onSubmit: (data: any) => void;
  onCancel: () => void;
}) {
  const [formData, setFormData] = useState({
    entry_price: item.current_price.toFixed(2),
    quantity: '10',
    stop_loss: '',
    take_profit: '',
    notes: `Trade from triggered condition: ${item.condition}`
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const data = {
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
      <div className="mb-4 p-3 bg-gray-50 rounded-lg">
        <p className="text-sm text-gray-600">
          <strong>{item.ticker_symbol}</strong> - {item.ticker_name}
        </p>
        <p className="text-xs text-gray-500">Triggered: {item.condition}</p>
        <p className="text-xs text-gray-500">Current Price: ${item.current_price.toFixed(2)}</p>
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
          placeholder={`Suggested: ${(item.current_price * 0.95).toFixed(2)} (-5%)`}
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
          placeholder={`Suggested: ${(item.current_price * 1.10).toFixed(2)} (+10%)`}
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
          rows={2}
        />
      </div>
      
      <div className="flex gap-2">
        <button
          type="submit"
          className="flex-1 bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700"
        >
          Open Trade
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