import os
import chromadb
from typing import List, Dict, Any

class MemoryManager:
    """
    Gestor de memoria en tiempo real usando ChromaDB.
    Optimizado para ejecución en memoria (In-Memory) gracias a la mejora de hardware (64GB RAM).
    """
    def __init__(self):
        self.use_in_memory = os.getenv("RAG_IN_MEMORY", "True").lower() == "true"
        if self.use_in_memory:
            print("[*] Inicializando ChromaDB en MEMORIA (Alta Performance)")
            self.client = chromadb.Client()
        else:
            print("[*] Inicializando ChromaDB Persistente")
            db_path = os.path.join(os.getcwd(), "chroma_db")
            self.client = chromadb.PersistentClient(path=db_path)
            
        self.collection = self.client.get_or_create_collection(name="jarvis_memory")

    def add_to_memory(self, text: str, metadata: Dict[str, Any] = None):
        """Añade un fragmento de información a la memoria volátil."""
        import uuid
        self.collection.add(
            documents=[text],
            metadatas=[metadata or {}],
            ids=[str(uuid.uuid4())]
        )

    def search_memory(self, query: str, n_results: int = 3) -> List[str]:
        """Busca en la memoria de trabajo actual."""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return results['documents'][0] if results['documents'] else []

    def reset_memory(self):
        """Limpia toda la memoria de trabajo eliminando y recreando la colección."""
        print("[!] Reseteando Memoria volátil...")
        self.client.delete_collection(name="jarvis_memory")
        self.collection = self.client.get_or_create_collection(name="jarvis_memory")
        print("[*] Memoria de trabajo reseteada correctamente.")

# Instancia global para ser importada por el Core
memory = MemoryManager()
