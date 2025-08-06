import Navigation from '@/components/Navigation';
import Signals from '@/components/Signals';

export default function SignalsPage() {
  return (
    <div className="flex h-screen bg-gray-50">
      <Navigation />
      <div className="flex-1 overflow-auto">
        <Signals />
      </div>
    </div>
  );
}