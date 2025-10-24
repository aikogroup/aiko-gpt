"use client";
import { useEffect, useState, useRef } from "react";

interface LoadingModalProps {
  isVisible: boolean;
  title: string;
  logs: string[];
  elapsedTime?: number;
  formatElapsedTime?: (ms: number) => string;
  onClose?: () => void;
}

export function LoadingModal({ isVisible, title, logs, elapsedTime = 0, formatElapsedTime, onClose }: LoadingModalProps) {
  const [displayedLogs, setDisplayedLogs] = useState<string[]>([]);
  const logsEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll vers le bas quand de nouveaux logs arrivent
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [displayedLogs]);

  useEffect(() => {
    if (isVisible) {
      // Garder l'historique existant et ajouter les nouveaux logs
      setDisplayedLogs(prev => {
        const newLogs = logs.filter(log => !prev.includes(log));
        return [...prev, ...newLogs];
      });
    } else {
      // Garder l'historique même quand la popup est fermée
      // Ne pas réinitialiser displayedLogs
    }
  }, [isVisible, logs]);

  // Animation CSS pour l'apparition des logs
  useEffect(() => {
    if (typeof document !== 'undefined') {
      const style = document.createElement('style');
      style.textContent = `
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-fadeIn {
          animation: fadeIn 0.3s ease-out;
        }
      `;
      document.head.appendChild(style);
      
      return () => {
        document.head.removeChild(style);
      };
    }
  }, []);

  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Overlay avec très léger flou seulement */}
      <div className="absolute inset-0 backdrop-blur-[2px]" />
      
      {/* Modal */}
      <div className="relative bg-white rounded-lg shadow-xl p-6 max-w-md w-full mx-4 max-h-[80vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
          <div className="flex items-center space-x-2">
            <div className="animate-spin rounded-full h-4 w-4 border-2 border-blue-500 border-t-transparent"></div>
            <span className="text-sm text-gray-600">En cours...</span>
            {formatElapsedTime && (
              <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                {formatElapsedTime(elapsedTime)}
              </span>
            )}
          </div>
        </div>

        {/* Logs */}
        <div className="bg-gray-50 rounded-md p-4 max-h-60 overflow-y-auto">
          <div className="space-y-2">
            {displayedLogs.map((log, index) => (
              <div 
                key={index} 
                className="text-sm text-gray-700 flex items-start space-x-2 animate-fadeIn"
              >
                <span className="text-blue-500 font-mono">•</span>
                <span>{log}</span>
              </div>
            ))}
            {displayedLogs.length === 0 && (
              <div className="text-sm text-gray-500 italic">Initialisation...</div>
            )}
            {/* Référence pour l'autoscroll */}
            <div ref={logsEndRef} />
          </div>
        </div>

        {/* Footer */}
        <div className="mt-4 text-center">
          <p className="text-xs text-gray-500">
            Veuillez patienter pendant le traitement...
          </p>
        </div>
      </div>
    </div>
  );
}
