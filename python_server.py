"""
Serveur Python simple qui utilise DIRECTEMENT les fonctions de client.py
Frontend → Python Server → client.py → LangGraph API
"""

import asyncio
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import sys
import os

# Ajouter le répertoire courant au PYTHONPATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import DIRECT des vraies fonctions de client.py
from client import (
    get_langgraph_client,
    create_thread_and_dispatch,
    human_validation,
    use_case_validation
)

class PythonServerHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """Gérer les requêtes CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_POST(self):
        """Gérer les requêtes POST"""
        if self.path == '/threads':
            self.handle_create_thread()
        elif self.path.startswith('/threads/') and '/validate-needs' in self.path:
            self.handle_validate_needs()
        elif self.path.startswith('/threads/') and '/validate-use-cases' in self.path:
            self.handle_validate_use_cases()
        else:
            self.send_error(404, "Not Found")

    def do_GET(self):
        """Gérer les requêtes GET"""
        if self.path == '/health':
            self.handle_health()
        elif self.path.startswith('/threads/') and '/state' in self.path:
            self.handle_get_state()
        else:
            self.send_error(404, "Not Found")

    def handle_create_thread(self):
        """Créer un thread et démarrer le workflow avec les VRAIES fonctions de client.py"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            input_data = data.get('input', {})
            company_name = input_data.get('company_info', {}).get('company_name', '')
            workshop_files = input_data.get('workshop_files', [])
            transcript_files = input_data.get('transcript_files', [])
            
            # Remplacer les chemins simulés par les vrais fichiers du projet
            real_workshop_files = []
            real_transcript_files = []
            
            # Utiliser les vrais fichiers du projet
            if workshop_files:
                real_workshop_files = ["/Users/julliardcyril/Projets/aikoGPT/documents/atelier_exemple.xlsx"]
            if transcript_files:
                real_transcript_files = ["/Users/julliardcyril/Projets/aikoGPT/documents/040425-Cousin-Biotech-x-aiko-Echange-IA-Booster-RH-DAF-4e7c7d16-b8f6.pdf"]
            
            print(f"🚀 [client.py] Création thread pour: {company_name}")
            print(f"📁 [client.py] Workshop files (réels): {real_workshop_files}")
            print(f"📄 [client.py] Transcript files (réels): {real_transcript_files}")
            
            # Utiliser DIRECTEMENT les VRAIES fonctions de client.py
            client = get_langgraph_client()
            
            # Exécuter de manière asynchrone
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            thread_id, state = loop.run_until_complete(
                create_thread_and_dispatch(
                    client,
                    company_name,
                    real_workshop_files,
                    real_transcript_files
                )
            )
            
            loop.close()
            
            print(f"✅ [client.py] Thread créé: {thread_id}")
            print(f"📊 [client.py] État: {state}")
            
            response = {
                'thread_id': thread_id,
                'status': 'created',
                'state': state
            }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            print(f"❌ [client.py] Erreur dans create_thread: {e}")
            self.send_error(500, f"Error: {str(e)}")

    def handle_get_state(self):
        """Obtenir l'état d'un thread avec les VRAIES fonctions de client.py"""
        try:
            # Extraire le thread_id de l'URL
            path_parts = self.path.split('/')
            thread_id = path_parts[2] if len(path_parts) > 2 else None
            
            if not thread_id:
                self.send_error(404, "Thread ID not found")
                return
            
            print(f"📊 [client.py] Récupération état thread: {thread_id}")
            
            # Utiliser le client LangGraph DIRECTEMENT
            client = get_langgraph_client()
            
            # Exécuter de manière asynchrone
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            state = loop.run_until_complete(
                client.threads.get_state(thread_id)
            )
            
            loop.close()
            
            response = {
                'thread_id': thread_id,
                'state': state,
                'status': 'running'
            }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            print(f"❌ [client.py] Erreur dans get_state: {e}")
            self.send_error(500, f"Error: {str(e)}")

    def handle_validate_needs(self):
        """Valider les besoins avec les VRAIES fonctions de client.py"""
        try:
            # Extraire le thread_id de l'URL
            path_parts = self.path.split('/')
            thread_id = path_parts[2] if len(path_parts) > 2 else None
            
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            validated_needs = data.get('validated_needs', [])
            rejected_needs = data.get('rejected_needs', [])
            user_feedback = data.get('user_feedback', '')
            
            print(f"✅ [client.py] Validation besoins pour thread: {thread_id}")
            print(f"📝 [client.py] Validés: {len(validated_needs)}")
            print(f"❌ [client.py] Rejetés: {len(rejected_needs)}")
            
            # Utiliser DIRECTEMENT les VRAIES fonctions de client.py
            client = get_langgraph_client()
            
            # Exécuter de manière asynchrone
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(
                human_validation(
                    client,
                    thread_id,
                    validated_needs,
                    rejected_needs,
                    [user_feedback]
                )
            )
            
            loop.close()
            
            response = {
                'thread_id': thread_id,
                'status': 'validated',
                'result': result
            }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            print(f"❌ [client.py] Erreur dans validate_needs: {e}")
            self.send_error(500, f"Error: {str(e)}")

    def handle_validate_use_cases(self):
        """Valider les cas d'usage avec les VRAIES fonctions de client.py"""
        try:
            # Extraire le thread_id de l'URL
            path_parts = self.path.split('/')
            thread_id = path_parts[2] if len(path_parts) > 2 else None
            
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            validated_quick_wins = data.get('validated_quick_wins', [])
            validated_structuration_ia = data.get('validated_structuration_ia', [])
            rejected_quick_wins = data.get('rejected_quick_wins', [])
            rejected_structuration_ia = data.get('rejected_structuration_ia', [])
            user_feedback = data.get('user_feedback', '')
            
            print(f"✅ [client.py] Validation use cases pour thread: {thread_id}")
            
            # Utiliser DIRECTEMENT les VRAIES fonctions de client.py
            client = get_langgraph_client()
            
            # Exécuter de manière asynchrone
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(
                use_case_validation(
                    client,
                    thread_id,
                    validated_quick_wins,
                    validated_structuration_ia,
                    rejected_quick_wins,
                    rejected_structuration_ia,
                    user_feedback
                )
            )
            
            loop.close()
            
            response = {
                'thread_id': thread_id,
                'status': 'validated',
                'result': result
            }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            print(f"❌ [client.py] Erreur dans validate_use_cases: {e}")
            self.send_error(500, f"Error: {str(e)}")

    def handle_health(self):
        """Vérification de santé"""
        response = {
            'status': 'healthy',
            'message': 'Python Server avec client.py - VRAIES fonctions',
            'endpoints': [
                'POST /threads - Create thread and start workflow (client.py)',
                'GET /threads/{id}/state - Get thread state (client.py)',
                'POST /threads/{id}/validate-needs - Validate needs (client.py)',
                'POST /threads/{id}/validate-use-cases - Validate use cases (client.py)'
            ]
        }
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())

def run_server(port=2026):
    """Démarrer le serveur Python avec les VRAIES fonctions de client.py"""
    server = HTTPServer(('127.0.0.1', port), PythonServerHandler)
    print(f"🚀 Python Server avec client.py running on http://127.0.0.1:{port}")
    print("📡 Frontend → Python Server → client.py → LangGraph API")
    print("🔗 Endpoints disponibles:")
    print("   POST /threads - Créer thread et démarrer workflow (client.py)")
    print("   GET /threads/{id}/state - Obtenir l'état du thread (client.py)")
    print("   POST /threads/{id}/validate-needs - Valider les besoins (client.py)")
    print("   POST /threads/{id}/validate-use-cases - Valider les use cases (client.py)")
    print("⚠️  Nécessite que l'API LangGraph soit démarrée !")
    server.serve_forever()

if __name__ == "__main__":
    run_server()
