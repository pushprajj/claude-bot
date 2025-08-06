import Navigation from '@/components/Navigation';
import TickerManagement from '@/components/TickerManagement';

export default function TickersPage() {
  return (
    <div className="flex h-screen bg-gray-50">
      <Navigation />
      <div className="flex-1 overflow-auto">
        <TickerManagement />
      </div>
    </div>
  );
}