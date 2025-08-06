import Navigation from '@/components/Navigation';
import Trades from '@/components/Trades';

export default function TradesPage() {
  return (
    <div className="flex h-screen bg-gray-50">
      <Navigation />
      <div className="flex-1 overflow-auto">
        <Trades />
      </div>
    </div>
  );
}