'use client';

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faTools } from '@fortawesome/free-solid-svg-icons';

interface PlaceholderViewProps {
  title: string;
}

export default function PlaceholderView({ title }: PlaceholderViewProps) {
  return (
    <div className="h-full flex items-center justify-center">
      <div className="p-8 bg-bg-panel border border-gray-800 rounded-xl text-center shadow-lg">
        <FontAwesomeIcon icon={faTools} className="text-5xl text-gray-600 mb-4" />
        <h3 className="text-xl font-bold text-white mb-2">Development In Progress</h3>
        <p className="text-gray-400">
          The <strong>{title.toUpperCase()}</strong> module is currently being built. Check back soon!
        </p>
      </div>
    </div>
  );
}
