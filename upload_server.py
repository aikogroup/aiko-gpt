#!/usr/bin/env python3
"""
Serveur d'upload simple pour gérer les fichiers uploadés par le frontend
et les transmettre à l'API LangGraph
"""

import os
import json
import asyncio
import aiohttp
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import tempfile
import shutil

# Configuration
UPLOAD_DIR = "uploads"
LANGGRAPH_API_URL = "http://127.0.0.1:2024"

class UploadHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """Gérer les requêtes CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        """Gérer les uploads de fichiers"""
        try:
            if self.path == '/upload':
                self.handle_file_upload()
            elif self.path == '/start-workflow':
                self.handle_start_workflow()
            else:
                self.send_error(404, "Endpoint not found")
        except Exception as e:
            print(f"❌ Erreur: {e}")
            self.send_error(500, str(e))

    def handle_file_upload(self):
        """Gérer l'upload d'un fichier"""
        try:
            # Lire le contenu du fichier
            content_length = int(self.headers['Content-Length'])
            file_data = self.rfile.read(content_length)
            
            # Extraire le nom du fichier depuis les headers
            filename = self.headers.get('X-Filename', 'uploaded_file')
            
            # Créer le dossier uploads s'il n'existe pas
            os.makedirs(UPLOAD_DIR, exist_ok=True)
            
            # Sauvegarder le fichier
            file_path = os.path.join(UPLOAD_DIR, filename)
            with open(file_path, 'wb') as f:
                f.write(file_data)
            
            print(f"✅ Fichier sauvegardé: {file_path}")
            
            # Répondre avec le chemin du fichier
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {
                "success": True,
                "file_path": file_path,
                "filename": filename
            }
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            print(f"❌ Erreur upload: {e}")
            self.send_error(500, str(e))

    def handle_start_workflow(self):
        """Démarrer le workflow avec les fichiers uploadés"""
        try:
            # Lire les données JSON
            content_length = int(self.headers['Content-Length'])
            data = json.loads(self.rfile.read(content_length))
            
            company_name = data.get('company_name', '')
            workshop_files = data.get('workshop_files', [])
            transcript_files = data.get('transcript_files', [])
            
            print(f"🚀 Démarrage workflow pour {company_name}")
            print(f"📊 Fichiers Excel: {workshop_files}")
            print(f"📄 Fichiers PDF: {transcript_files}")
            
            # Démarrer le workflow via l'API LangGraph
            result = asyncio.run(self.start_langgraph_workflow(
                company_name, workshop_files, transcript_files
            ))
            
            # Répondre avec le résultat
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            self.wfile.write(json.dumps(result).encode())
            
        except Exception as e:
            print(f"❌ Erreur workflow: {e}")
            self.send_error(500, str(e))

    async def start_langgraph_workflow(self, company_name, workshop_files, transcript_files):
        """Démarrer le workflow via l'API LangGraph"""
        try:
            async with aiohttp.ClientSession() as session:
                # Créer un thread
                thread_data = {"name": f"Thread-{company_name}-{os.getpid()}"}
                async with session.post(f"{LANGGRAPH_API_URL}/threads", json=thread_data) as resp:
                    if resp.status != 200:
                        raise Exception(f"Erreur création thread: {resp.status}")
                    thread = await resp.json()
                
                print(f"✅ Thread créé: {thread['thread_id']}")
                
                # Démarrer le workflow
                workflow_data = {
                    "assistant_id": "need_analysis",
                    "input": {
                        "company_info": {"company_name": company_name},
                        "workshop_files": workshop_files,
                        "transcript_files": transcript_files
                    }
                }
                
                async with session.post(
                    f"{LANGGRAPH_API_URL}/threads/{thread['thread_id']}/runs/wait",
                    json=workflow_data
                ) as resp:
                    if resp.status != 200:
                        raise Exception(f"Erreur démarrage workflow: {resp.status}")
                    result = await resp.json()
                
                print(f"✅ Workflow terminé avec {len(result.get('state', {}).get('values', {}).get('identified_needs', []))} besoins")
                
                return {
                    "success": True,
                    "thread_id": thread['thread_id'],
                    "state": result
                }
                
        except Exception as e:
            print(f"❌ Erreur LangGraph: {e}")
            raise

    def do_GET(self):
        """Gérer les requêtes GET"""
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode())
        else:
            self.send_error(404, "Not found")

def main():
    """Démarrer le serveur d'upload"""
    port = 2026
    server = HTTPServer(('localhost', port), UploadHandler)
    print(f"🚀 Serveur d'upload démarré sur http://localhost:{port}")
    print(f"📁 Dossier d'upload: {os.path.abspath(UPLOAD_DIR)}")
    print(f"🔗 API LangGraph: {LANGGRAPH_API_URL}")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Serveur arrêté")
        server.shutdown()

if __name__ == "__main__":
    main()
