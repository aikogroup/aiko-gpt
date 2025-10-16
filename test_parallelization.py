"""
Script de test pour démontrer le gain de temps avec la parallélisation
"""

import time
import asyncio
from typing import Dict, Any

def simulate_workshop_agent() -> Dict[str, Any]:
    """Simule l'exécution du workshop agent (3 secondes)"""
    print("📝 [PARALLÈLE-1/3] Workshop Agent - DÉBUT")
    time.sleep(3)
    print("✅ [PARALLÈLE-1/3] Workshop Agent - FIN (3s)")
    return {"workshops": ["Workshop 1", "Workshop 2"]}

def simulate_transcript_agent() -> Dict[str, Any]:
    """Simule l'exécution du transcript agent (5 secondes)"""
    print("📄 [PARALLÈLE-2/3] Transcript Agent - DÉBUT")
    time.sleep(5)
    print("✅ [PARALLÈLE-2/3] Transcript Agent - FIN (5s)")
    return {"transcripts": ["Transcript 1", "Transcript 2"]}

def simulate_web_search_agent() -> Dict[str, Any]:
    """Simule l'exécution du web search agent (2 secondes)"""
    print("🌐 [PARALLÈLE-3/3] Web Search Agent - DÉBUT")
    time.sleep(2)
    print("✅ [PARALLÈLE-3/3] Web Search Agent - FIN (2s)")
    return {"web_results": ["Result 1", "Result 2"]}

def run_sequential():
    """Exécution séquentielle (l'ancien workflow)"""
    print("\n" + "="*70)
    print("⏱️  EXÉCUTION SÉQUENTIELLE")
    print("="*70)
    
    start = time.time()
    
    # Workshop Agent
    workshop_results = simulate_workshop_agent()
    
    # Transcript Agent
    transcript_results = simulate_transcript_agent()
    
    # Web Search Agent
    web_search_results = simulate_web_search_agent()
    
    duration = time.time() - start
    
    print(f"\n⏱️  Temps total (séquentiel): {duration:.2f}s")
    print(f"   (3s + 5s + 2s = 10s)")
    
    return duration, {
        "workshop_results": workshop_results,
        "transcript_results": transcript_results,
        "web_search_results": web_search_results
    }

async def run_parallel():
    """Exécution parallèle (le nouveau workflow)"""
    print("\n" + "="*70)
    print("⚡ EXÉCUTION PARALLÈLE")
    print("="*70)
    
    start = time.time()
    
    # Dispatcher
    print("🚀 [PARALLÉLISATION] Dispatcher - Distribution des tâches")
    
    # Les 3 agents s'exécutent EN PARALLÈLE
    async def async_workshop():
        return await asyncio.to_thread(simulate_workshop_agent)
    
    async def async_transcript():
        return await asyncio.to_thread(simulate_transcript_agent)
    
    async def async_web_search():
        return await asyncio.to_thread(simulate_web_search_agent)
    
    # Exécution en parallèle avec asyncio.gather
    results = await asyncio.gather(
        async_workshop(),
        async_transcript(),
        async_web_search()
    )
    
    workshop_results, transcript_results, web_search_results = results
    
    # Convergence
    print("\n📊 [CONVERGENCE] Collect Data - Agrégation des résultats")
    
    duration = time.time() - start
    
    print(f"\n⏱️  Temps total (parallèle): {duration:.2f}s")
    print(f"   (max(3s, 5s, 2s) = 5s)")
    
    return duration, {
        "workshop_results": workshop_results,
        "transcript_results": transcript_results,
        "web_search_results": web_search_results
    }

def main():
    """Fonction principale de test"""
    print("🧪 Test de Parallélisation du Workflow")
    print("="*70)
    
    # Test séquentiel
    seq_duration, seq_results = run_sequential()
    
    # Test parallèle
    para_duration, para_results = asyncio.run(run_parallel())
    
    # Comparaison
    print("\n" + "="*70)
    print("📊 RÉSULTATS DE LA COMPARAISON")
    print("="*70)
    print(f"⏱️  Temps séquentiel : {seq_duration:.2f}s (baseline)")
    print(f"⚡ Temps parallèle  : {para_duration:.2f}s")
    print(f"🚀 Gain de temps    : {seq_duration - para_duration:.2f}s")
    print(f"📈 Amélioration     : {((seq_duration - para_duration) / seq_duration * 100):.1f}%")
    print("="*70)
    
    # Vérification que les résultats sont identiques
    print("\n✅ Vérification: Les résultats sont identiques")
    print(f"   Workshop results: {seq_results['workshop_results'] == para_results['workshop_results']}")
    print(f"   Transcript results: {seq_results['transcript_results'] == para_results['transcript_results']}")
    print(f"   Web search results: {seq_results['web_search_results'] == para_results['web_search_results']}")

if __name__ == "__main__":
    main()

