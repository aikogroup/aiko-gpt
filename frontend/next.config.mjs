/**
 * FR: Configuration Next.js
 * @type {import('next').NextConfig}
 */
const nextConfig = {
  /* FR: Options de configuration */
  reactStrictMode: true,
  
  // FR: Configuration des variables d'environnement
  env: {
    // FR: URL de l'API LangGraph
    NEXT_PUBLIC_LANGGRAPH_URL: process.env.NEXT_PUBLIC_LANGGRAPH_URL || 'http://localhost:2024',
    
    // FR: URL backend (si routes custom)
    NEXT_PUBLIC_BACKEND_URL: process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000',
  },
};

export default nextConfig;

