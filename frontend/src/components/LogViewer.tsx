"use client";
import { useEffect, useState, useRef } from "react";

interface LogEntry {
  id: string;
  timestamp: string;
  level: 'info' | 'debug' | 'warning' | 'error' | 'success';
  message: string;
  emoji?: string;
}

interface LogViewerProps {
  isActive: boolean;
  maxLines?: number;
  className?: string;
  context?: 'workflow' | 'validation' | 'download';
}

export function LogViewer({ isActive, maxLines = 20, className = "", context = 'workflow' }: LogViewerProps) {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  // Fonction pour faire le scroll automatique vers le bas
  const scrollToBottom = () => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTop = scrollContainerRef.current.scrollHeight;
    }
  };

  // Auto-scroll à chaque fois que les logs changent
  useEffect(() => {
    if (logs.length > 0) {
      scrollToBottom();
    }
  }, [logs]);

  useEffect(() => {
    if (!isActive) {
      setLogs([]);
      return;
    }

    // Messages spécifiques selon le contexte
    const getLogMessages = () => {
      switch (context) {
        case 'workflow':
          return [
            { level: 'info' as const, message: 'Initialisation du workflow...', emoji: '🚀' },
            { level: 'debug' as const, message: 'Upload des fichiers vers le serveur...', emoji: '📤' },
            { level: 'info' as const, message: 'Analyse des fichiers Excel...', emoji: '📊' },
            { level: 'debug' as const, message: 'Extraction des données des ateliers...', emoji: '📁' },
            { level: 'info' as const, message: 'Traitement des transcriptions PDF...', emoji: '📄' },
            { level: 'debug' as const, message: 'Analyse sémantique des conversations...', emoji: '🧠' },
            { level: 'info' as const, message: 'Recherche d\'informations sur l\'entreprise...', emoji: '🌐' },
            { level: 'debug' as const, message: 'Connexion aux services IA OpenAI...', emoji: '🤖' },
            { level: 'info' as const, message: 'Exécution des agents en parallèle...', emoji: '⚡' },
            { level: 'debug' as const, message: 'Agent Workshop en cours...', emoji: '📊' },
            { level: 'info' as const, message: 'Agent Transcript en cours...', emoji: '📄' },
            { level: 'debug' as const, message: 'Agent Web Search en cours...', emoji: '🌐' },
            { level: 'info' as const, message: 'Agrégation des résultats...', emoji: '🔄' },
            { level: 'debug' as const, message: 'Convergence des données...', emoji: '🔗' },
            { level: 'info' as const, message: 'Génération des besoins identifiés...', emoji: '🔍' },
            { level: 'debug' as const, message: 'Appel à l\'IA pour l\'analyse...', emoji: '🧠' },
            { level: 'info' as const, message: 'Traitement des tokens IA...', emoji: '💰' },
            { level: 'debug' as const, message: 'Analyse des thèmes et priorités...', emoji: '📈' },
            { level: 'info' as const, message: 'Structuration des besoins...', emoji: '🏗️' },
            { level: 'debug' as const, message: 'Validation des résultats...', emoji: '✅' },
            { level: 'info' as const, message: 'Sauvegarde de l\'état...', emoji: '💾' },
            { level: 'debug' as const, message: 'Préparation de l\'interface de validation...', emoji: '🎯' },
            { level: 'info' as const, message: 'Finalisation du workflow...', emoji: '🔚' },
            { level: 'success' as const, message: 'Workflow prêt pour la validation', emoji: '🎉' },
          ];
        case 'validation':
          return [
            { level: 'info' as const, message: 'Envoi de la validation...', emoji: '📤' },
            { level: 'debug' as const, message: 'Traitement des sélections...', emoji: '⚙️' },
            { level: 'info' as const, message: 'Connexion à l\'API de validation...', emoji: '🔗' },
            { level: 'debug' as const, message: 'Envoi des données au serveur...', emoji: '📡' },
            { level: 'info' as const, message: 'Analyse des besoins validés...', emoji: '🔍' },
            { level: 'debug' as const, message: 'Vérification du nombre de validations...', emoji: '📊' },
            { level: 'info' as const, message: 'Calcul du total validé...', emoji: '🧮' },
            { level: 'debug' as const, message: 'Génération de nouvelles propositions...', emoji: '🔄' },
            { level: 'info' as const, message: 'Appel à l\'IA pour de nouveaux besoins...', emoji: '🤖' },
            { level: 'debug' as const, message: 'Traitement des tokens IA...', emoji: '💰' },
            { level: 'info' as const, message: 'Analyse des nouveaux besoins...', emoji: '🧠' },
            { level: 'debug' as const, message: 'Mise à jour de l\'état du workflow...', emoji: '💾' },
            { level: 'info' as const, message: 'Sauvegarde des résultats...', emoji: '💿' },
            { level: 'debug' as const, message: 'Préparation de la réponse...', emoji: '📋' },
            { level: 'info' as const, message: 'Finalisation de la validation...', emoji: '🔚' },
            { level: 'success' as const, message: 'Validation enregistrée avec succès', emoji: '✅' },
          ];
        case 'download':
          return [
            { level: 'info' as const, message: 'Démarrage de la génération du rapport...', emoji: '📄' },
            { level: 'debug' as const, message: 'Connexion à l\'API de téléchargement...', emoji: '🔗' },
            { level: 'info' as const, message: 'Récupération des données validées...', emoji: '📊' },
            { level: 'debug' as const, message: 'Compilation des besoins identifiés...', emoji: '🔍' },
            { level: 'info' as const, message: 'Compilation des Quick Wins...', emoji: '⚡' },
            { level: 'debug' as const, message: 'Compilation de la Structuration IA...', emoji: '🏗️' },
            { level: 'info' as const, message: 'Création du document Word...', emoji: '📝' },
            { level: 'debug' as const, message: 'Ajout du logo et formatage...', emoji: '🎨' },
            { level: 'info' as const, message: 'Génération des sections du rapport...', emoji: '📋' },
            { level: 'debug' as const, message: 'Formatage des tableaux...', emoji: '📊' },
            { level: 'info' as const, message: 'Ajout des styles et couleurs...', emoji: '🎨' },
            { level: 'debug' as const, message: 'Finalisation du document...', emoji: '✨' },
            { level: 'info' as const, message: 'Compression du fichier...', emoji: '🗜️' },
            { level: 'debug' as const, message: 'Préparation du téléchargement...', emoji: '📤' },
            { level: 'success' as const, message: 'Rapport prêt au téléchargement', emoji: '📥' },
          ];
        default:
          return [
            { level: 'info' as const, message: 'Traitement en cours...', emoji: '⏳' },
          ];
      }
    };

    const logMessages = getLogMessages();

    let currentIndex = 0;
    const interval = setInterval(() => {
      if (currentIndex < logMessages.length) {
        const logEntry: LogEntry = {
          id: `log-${Date.now()}-${currentIndex}`,
          timestamp: new Date().toLocaleTimeString(),
          ...logMessages[currentIndex]
        };
        
        setLogs(prev => {
          const newLogs = [...prev, logEntry];
          // Garder seulement les dernières lignes
          return newLogs.slice(-maxLines);
        });
        
        currentIndex++;
      } else {
        // Continuer à afficher des traces génériques tant que l'opération est active
        const genericMessages = [
          { level: 'debug' as const, message: 'Traitement en cours...', emoji: '⏳' },
          { level: 'info' as const, message: 'Analyse approfondie...', emoji: '🔍' },
          { level: 'debug' as const, message: 'Optimisation des résultats...', emoji: '⚡' },
          { level: 'info' as const, message: 'Finalisation des données...', emoji: '📊' },
          { level: 'debug' as const, message: 'Vérification de la qualité...', emoji: '✅' },
        ];
        
        const randomMessage = genericMessages[Math.floor(Math.random() * genericMessages.length)];
        const logEntry: LogEntry = {
          id: `log-${Date.now()}-${currentIndex}`,
          timestamp: new Date().toLocaleTimeString(),
          ...randomMessage
        };
        
        setLogs(prev => {
          const newLogs = [...prev, logEntry];
          return newLogs.slice(-maxLines);
        });
        
        currentIndex++;
      }
    }, 1000); // Une nouvelle ligne toutes les 1 seconde

    return () => clearInterval(interval);
  }, [isActive, maxLines, context]);

  if (!isActive && logs.length === 0) {
    return null;
  }

  const getLevelColor = (level: LogEntry['level']) => {
    switch (level) {
      case 'info': return 'text-blue-600';
      case 'debug': return 'text-gray-600';
      case 'warning': return 'text-yellow-600';
      case 'error': return 'text-red-600';
      case 'success': return 'text-green-600';
      default: return 'text-gray-600';
    }
  };

  const getLevelBg = (level: LogEntry['level']) => {
    switch (level) {
      case 'info': return 'bg-blue-50';
      case 'debug': return 'bg-gray-50';
      case 'warning': return 'bg-yellow-50';
      case 'error': return 'bg-red-50';
      case 'success': return 'bg-green-50';
      default: return 'bg-gray-50';
    }
  };

  return (
    <div className={`mt-4 p-3 bg-gray-100 rounded-lg border ${className}`}>
      <div className="flex items-center gap-2 mb-2">
        <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
        <span className="text-sm font-medium text-gray-700">Activité en cours...</span>
      </div>
      
      <div ref={scrollContainerRef} className="space-y-1 max-h-80 overflow-y-auto">
        {logs.map((log) => (
          <div
            key={log.id}
            className={`flex items-start gap-2 p-2 rounded text-xs ${getLevelBg(log.level)}`}
          >
            <span className="text-gray-400 font-mono text-xs">
              {log.timestamp}
            </span>
            <span className="text-lg">{log.emoji}</span>
            <span className={`flex-1 ${getLevelColor(log.level)}`}>
              {log.message}
            </span>
          </div>
        ))}
        
        {isActive && logs.length === 0 && (
          <div className="flex items-center gap-2 p-2 text-gray-500 text-xs">
            <div className="animate-spin w-3 h-3 border border-gray-400 border-t-transparent rounded-full"></div>
            <span>Préparation du traitement...</span>
          </div>
        )}
      </div>
    </div>
  );
}
