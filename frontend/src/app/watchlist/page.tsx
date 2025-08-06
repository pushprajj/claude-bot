import Navigation from '@/components/Navigation';
import Watchlist from '@/components/Watchlist';

export default function WatchlistPage() {
  return (
    <div className="flex h-screen bg-gray-50">
      <Navigation />
      <div className="flex-1 overflow-auto">
        <Watchlist />
      </div>
    </div>
  );
}