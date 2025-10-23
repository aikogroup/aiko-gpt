"""
API HTTP simple utilisant directement les fonctions de client.py
Alternative à FastAPI - plus simple et direct
"""

import asyncio
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import uuid

# Import des fonctions de client.py
from client import (
    get_langgraph_client,
    create_thread_and_dispatch,
    human_validation,
    use_case_validation
)

class SimpleAPIHandler(BaseHTTPRequestHandler):
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
        """Créer un thread et démarrer le workflow"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            input_data = data.get('input', {})
            company_name = input_data.get('company_info', {}).get('company_name', '')
            workshop_files = input_data.get('workshop_files', [])
            transcript_files = input_data.get('transcript_files', [])
            
            # Utiliser les fonctions de client.py
            client = get_langgraph_client()
            
            # Exécuter de manière asynchrone
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            thread_id, state = loop.run_until_complete(
                create_thread_and_dispatch(
                    client,
                    company_name,
                    workshop_files,
                    transcript_files
                )
            )
            
            loop.close()
            
            # Stocker le thread (en mémoire pour la démo)
            if not hasattr(self.server, 'threads'):
                self.server.threads = {}
            self.server.threads[thread_id] = {'state': state}
            
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
            self.send_error(500, f"Error: {str(e)}")

    def handle_get_state(self):
        """Obtenir l'état d'un thread"""
        try:
            # Extraire le thread_id de l'URL
            path_parts = self.path.split('/')
            thread_id = path_parts[2] if len(path_parts) > 2 else None
            
            if not thread_id or not hasattr(self.server, 'threads'):
                self.send_error(404, "Thread not found")
                return
            
            thread_data = self.server.threads.get(thread_id)
            if not thread_data:
                self.send_error(404, "Thread not found")
                return
            
            response = {
                'thread_id': thread_id,
                'state': thread_data['state'],
                'status': 'running'
            }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.send_error(500, f"Error: {str(e)}")

    def handle_validate_needs(self):
        """Valider les besoins"""
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
            
            # Utiliser les fonctions de client.py
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
            
            # Mettre à jour l'état stocké
            if hasattr(self.server, 'threads') and thread_id in self.server.threads:
                self.server.threads[thread_id]['state'] = result
            
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
            self.send_error(500, f"Error: {str(e)}")

    def handle_validate_use_cases(self):
        """Valider les cas d'usage"""
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
            
            # Utiliser les fonctions de client.py
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
            
            # Mettre à jour l'état stocké
            if hasattr(self.server, 'threads') and thread_id in self.server.threads:
                self.server.threads[thread_id]['state'] = result
            
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
            self.send_error(500, f"Error: {str(e)}")

    def handle_health(self):
        """Vérification de santé"""
        response = {
            'status': 'healthy',
            'active_threads': len(getattr(self.server, 'threads', {}))
        }
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())

def run_server(port=2024):
    """Démarrer le serveur"""
    server = HTTPServer(('127.0.0.1', port), SimpleAPIHandler)
    print(f"🚀 Simple API Server running on http://127.0.0.1:{port}")
    print("📡 Using client.py functions directly!")
    server.serve_forever()

if __name__ == "__main__":
    run_server()
