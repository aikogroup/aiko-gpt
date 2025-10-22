/**
 * LLM Log Viewer - Affichage des logs LLM en temps réel
 * 
 * FR: Composant pour afficher les traces d'exécution des LLM
 *     Permet à l'utilisateur de voir ce qui se passe pendant l'analyse
 */

import React, { useState, useEffect } from 'react';

interface LogEntry {
  timestamp: string;
  level: 'info' | 'warning' | 'error' | 'success';
  message: string;
  agent?: string;
}

interface LLMLogViewerProps {
  isVisible: boolean;
  onClose: () => void;
  type?: 'needs' | 'usecases'; // FR: Type de workflow
}

export const LLMLogViewer: React.FC<LLMLogViewerProps> = ({ isVisible, onClose, type = 'needs' }) => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const logsEndRef = React.useRef<HTMLDivElement>(null);

  // FR: Simuler la réception de logs en temps réel
  useEffect(() => {
    if (!isVisible) return;

    setIsConnected(true);
    
    // FR: Logs simulés pour démonstration - PROCESSUS COMPLET
    const baseTime = new Date();
    
    // FR: Logs différents selon le type de workflow
    const needsLogs: LogEntry[] = [
      {
        timestamp: new Date(baseTime.getTime() + 0).toLocaleTimeString(),
        level: 'info',
        message: '🚀 Démarrage du workflow d\'analyse...',
        agent: 'System'
      },
      {
        timestamp: new Date(baseTime.getTime() + 500).toLocaleTimeString(),
        level: 'info',
        message: '📤 Upload des fichiers en cours...',
        agent: 'System'
      },
      {
        timestamp: new Date(baseTime.getTime() + 1500).toLocaleTimeString(),
        level: 'success',
        message: '✅ Fichiers uploadés avec succès',
        agent: 'System'
      },
      {
        timestamp: new Date(baseTime.getTime() + 2000).toLocaleTimeString(),
        level: 'info',
        message: '🏭 WorkshopAgent - Début analyse fichier Excel',
        agent: 'WorkshopAgent'
      },
      {
        timestamp: new Date(baseTime.getTime() + 3000).toLocaleTimeString(),
        level: 'info',
        message: '📄 Parsing fichier Excel...',
        agent: 'WorkshopAgent'
      },
      {
        timestamp: new Date(baseTime.getTime() + 4500).toLocaleTimeString(),
        level: 'success',
        message: '✅ 15 lignes extraites du fichier Excel',
        agent: 'WorkshopAgent'
      },
      {
        timestamp: new Date(baseTime.getTime() + 5000).toLocaleTimeString(),
        level: 'info',
        message: '🤖 Analyse des données avec OpenAI...',
        agent: 'WorkshopAgent'
      },
      {
        timestamp: new Date(baseTime.getTime() + 8000).toLocaleTimeString(),
        level: 'success',
        message: '✅ WorkshopAgent - Analyse terminée',
        agent: 'WorkshopAgent'
      },
      {
        timestamp: new Date(baseTime.getTime() + 8500).toLocaleTimeString(),
        level: 'info',
        message: '📚 TranscriptAgent - Début analyse fichiers PDF/JSON',
        agent: 'TranscriptAgent'
      },
      {
        timestamp: new Date(baseTime.getTime() + 9000).toLocaleTimeString(),
        level: 'info',
        message: '📄 Parsing des fichiers PDF/JSON...',
        agent: 'TranscriptAgent'
      },
      {
        timestamp: new Date(baseTime.getTime() + 11000).toLocaleTimeString(),
        level: 'success',
        message: '✅ Fichiers PDF/JSON analysés',
        agent: 'TranscriptAgent'
      },
      {
        timestamp: new Date(baseTime.getTime() + 11500).toLocaleTimeString(),
        level: 'info',
        message: '🔍 WebSearchAgent - Recherche contextuelle entreprise',
        agent: 'WebSearchAgent'
      },
      {
        timestamp: new Date(baseTime.getTime() + 12000).toLocaleTimeString(),
        level: 'info',
        message: '🌐 Recherche Perplexity en cours...',
        agent: 'WebSearchAgent'
      },
      {
        timestamp: new Date(baseTime.getTime() + 15000).toLocaleTimeString(),
        level: 'success',
        message: '✅ Recherche Perplexity terminée - Contexte récupéré',
        agent: 'WebSearchAgent'
      },
      {
        timestamp: new Date(baseTime.getTime() + 15500).toLocaleTimeString(),
        level: 'info',
        message: '💡 NeedAnalysisAgent - Début génération des besoins',
        agent: 'NeedAnalysisAgent'
      },
      {
        timestamp: new Date(baseTime.getTime() + 16000).toLocaleTimeString(),
        level: 'info',
        message: '🤖 Combinaison des données : Workshop + Transcript + WebSearch',
        agent: 'NeedAnalysisAgent'
      },
      {
        timestamp: new Date(baseTime.getTime() + 17000).toLocaleTimeString(),
        level: 'info',
        message: '🧠 Génération des besoins avec OpenAI (modèle: gpt-4o-mini)...',
        agent: 'NeedAnalysisAgent'
      },
      {
        timestamp: new Date(baseTime.getTime() + 25000).toLocaleTimeString(),
        level: 'info',
        message: '⏳ Analyse en profondeur des besoins métier...',
        agent: 'NeedAnalysisAgent'
      },
      {
        timestamp: new Date(baseTime.getTime() + 35000).toLocaleTimeString(),
        level: 'info',
        message: '📊 Extraction des citations sources...',
        agent: 'NeedAnalysisAgent'
      },
      {
        timestamp: new Date(baseTime.getTime() + 45000).toLocaleTimeString(),
        level: 'success',
        message: '✅ 10 besoins générés avec succès !',
        agent: 'NeedAnalysisAgent'
      },
      {
        timestamp: new Date(baseTime.getTime() + 46000).toLocaleTimeString(),
        level: 'success',
        message: '🎉 Workflow terminé - Redirection en cours...',
        agent: 'System'
      }
    ];

    const usecasesLogs: LogEntry[] = [
      {
        timestamp: new Date(baseTime.getTime() + 0).toLocaleTimeString(),
        level: 'info',
        message: '🚀 Démarrage génération cas d\'usage...',
        agent: 'System'
      },
      {
        timestamp: new Date(baseTime.getTime() + 1000).toLocaleTimeString(),
        level: 'info',
        message: '📊 Récupération des besoins validés',
        agent: 'UseCaseAnalysisAgent'
      },
      {
        timestamp: new Date(baseTime.getTime() + 2000).toLocaleTimeString(),
        level: 'success',
        message: '✅ Besoins validés chargés',
        agent: 'UseCaseAnalysisAgent'
      },
      {
        timestamp: new Date(baseTime.getTime() + 3000).toLocaleTimeString(),
        level: 'info',
        message: '🤖 Combinaison des données : Besoins + Workshop + Transcript + WebSearch',
        agent: 'UseCaseAnalysisAgent'
      },
      {
        timestamp: new Date(baseTime.getTime() + 4000).toLocaleTimeString(),
        level: 'info',
        message: '🧠 Génération des Quick Wins avec OpenAI (modèle: gpt-4o-mini)...',
        agent: 'UseCaseAnalysisAgent'
      },
      {
        timestamp: new Date(baseTime.getTime() + 12000).toLocaleTimeString(),
        level: 'info',
        message: '⏳ Analyse des projets à ROI rapide (< 3 mois)...',
        agent: 'UseCaseAnalysisAgent'
      },
      {
        timestamp: new Date(baseTime.getTime() + 20000).toLocaleTimeString(),
        level: 'success',
        message: '✅ 8 Quick Wins générés !',
        agent: 'UseCaseAnalysisAgent'
      },
      {
        timestamp: new Date(baseTime.getTime() + 21000).toLocaleTimeString(),
        level: 'info',
        message: '🏗️ Génération des Structuration IA avec OpenAI...',
        agent: 'UseCaseAnalysisAgent'
      },
      {
        timestamp: new Date(baseTime.getTime() + 30000).toLocaleTimeString(),
        level: 'info',
        message: '⏳ Analyse des projets structurants (3-12 mois)...',
        agent: 'UseCaseAnalysisAgent'
      },
      {
        timestamp: new Date(baseTime.getTime() + 40000).toLocaleTimeString(),
        level: 'info',
        message: '🔍 Identification des technologies IA pertinentes...',
        agent: 'UseCaseAnalysisAgent'
      },
      {
        timestamp: new Date(baseTime.getTime() + 50000).toLocaleTimeString(),
        level: 'success',
        message: '✅ 10 Structuration IA générés !',
        agent: 'UseCaseAnalysisAgent'
      },
      {
        timestamp: new Date(baseTime.getTime() + 51000).toLocaleTimeString(),
        level: 'success',
        message: '🎉 Génération terminée - Affichage des résultats...',
        agent: 'System'
      }
    ];

    // FR: Sélectionner les logs selon le type
    const simulatedLogs = type === 'usecases' ? usecasesLogs : needsLogs;

    // FR: Ajouter les logs progressivement
    let index = 0;
    const interval = setInterval(() => {
      if (index < simulatedLogs.length) {
        const log = simulatedLogs[index];
        // FR: Vérifier que le log est valide avant de l'ajouter
        if (log && log.timestamp && log.level && log.message) {
          setLogs(prev => [...prev, log]);
        }
        index++;
      } else {
        clearInterval(interval);
        setIsConnected(false);
      }
    }, 800); // FR: Un log toutes les 800ms

    return () => clearInterval(interval);
  }, [isVisible]);

  // FR: Auto-scroll vers le bas quand de nouveaux logs arrivent
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  if (!isVisible) return null;

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'info': return 'text-blue-600';
      case 'success': return 'text-green-600';
      case 'warning': return 'text-yellow-600';
      case 'error': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getLevelIcon = (level: string) => {
    switch (level) {
      case 'info': return 'ℹ️';
      case 'success': return '✅';
      case 'warning': return '⚠️';
      case 'error': return '❌';
      default: return '📝';
    }
  };

  // FR: Fonction pour formater le timestamp de manière sécurisée
  const formatTimestamp = (timestamp: string | undefined) => {
    if (!timestamp) return '--:--:--';
    return timestamp;
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl h-3/4 flex flex-col">
        {/* FR: Header */}
        <div className="flex justify-between items-center p-4 border-b">
          <div className="flex items-center gap-3">
            <h3 className="text-lg font-semibold">🤖 Logs LLM en temps réel</h3>
            <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-gray-400'}`}></div>
            <span className="text-sm text-gray-600">
              {isConnected ? 'Connexion active' : 'Terminé'}
            </span>
          </div>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-xl"
          >
            ×
          </button>
        </div>

        {/* FR: Logs */}
        <div className="flex-1 overflow-y-auto p-4 bg-gray-50">
          <div className="space-y-2">
            {logs.map((log, index) => {
              // FR: Vérification de sécurité pour éviter les erreurs
              if (!log || !log.timestamp || !log.level || !log.message) {
                return null;
              }
              
              return (
                <div
                  key={index}
                  className="flex items-start gap-3 p-3 bg-white rounded border-l-4 border-blue-500"
                >
                  <span className="text-sm text-gray-500 mt-1 min-w-[80px]">
                    {formatTimestamp(log.timestamp)}
                  </span>
                  <span className="text-lg">
                    {getLevelIcon(log.level)}
                  </span>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`text-sm font-medium ${getLevelColor(log.level)}`}>
                        {log.message}
                      </span>
                      {log.agent && (
                        <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs font-semibold">
                          {log.agent}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
            
            {isConnected && (
              <div className="flex items-center gap-2 p-3 bg-blue-50 rounded">
                <div className="animate-spin w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full"></div>
                <span className="text-blue-600 text-sm">Analyse en cours...</span>
              </div>
            )}
            
            {/* FR: Élément invisible pour l'auto-scroll */}
            <div ref={logsEndRef} />
          </div>
        </div>

        {/* FR: Footer */}
        <div className="p-4 border-t bg-gray-50">
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600">
              {logs.length} entrées de log
            </span>
            <button
              onClick={() => setLogs([])}
              className="px-3 py-1 text-sm bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
            >
              Effacer
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
