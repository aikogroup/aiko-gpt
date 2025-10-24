"use client";
import { useState, useCallback, useEffect, useRef } from "react";

interface LoadingState {
  isVisible: boolean;
  title: string;
  logs: string[];
  startTime: number | null;
}

export function useLoadingModal() {
  const [loadingState, setLoadingState] = useState<LoadingState>({
    isVisible: false,
    title: "",
    logs: [],
    startTime: null
  });
  
  const [elapsedTime, setElapsedTime] = useState(0);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const showLoading = useCallback((title: string, initialLogs: string[] = []) => {
    const startTime = Date.now();
    setLoadingState(prev => ({
      isVisible: true,
      title,
      logs: [...prev.logs, ...initialLogs], // Ajouter aux logs existants
      startTime
    }));
    setElapsedTime(0);
    
    // Démarrer le timer
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }
    intervalRef.current = setInterval(() => {
      setElapsedTime(Date.now() - startTime);
    }, 1000);
  }, []);

  const addLog = useCallback((log: string) => {
    setLoadingState(prev => ({
      ...prev,
      logs: [...prev.logs, log]
    }));
  }, []);

  const hideLoading = useCallback(() => {
    setLoadingState(prev => ({
      ...prev,
      isVisible: false
    }));
    
    // Arrêter le timer
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  const updateTitle = useCallback((title: string) => {
    setLoadingState(prev => ({
      ...prev,
      title
    }));
  }, []);

  const clearLogs = useCallback(() => {
    setLoadingState(prev => ({
      ...prev,
      logs: []
    }));
  }, []);

  // Nettoyage du timer au démontage du composant
  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  // Fonction pour formater le temps écoulé
  const formatElapsedTime = useCallback((ms: number) => {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    
    if (minutes > 0) {
      return `${minutes}m ${remainingSeconds}s`;
    }
    return `${remainingSeconds}s`;
  }, []);

  return {
    loadingState,
    elapsedTime,
    formatElapsedTime,
    showLoading,
    addLog,
    hideLoading,
    updateTitle,
    clearLogs
  };
}
