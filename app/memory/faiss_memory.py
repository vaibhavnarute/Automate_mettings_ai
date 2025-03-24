import os
import json
import faiss
import numpy as np
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import time

class FaissMemory:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.embedding_size = self.model.get_sentence_embedding_dimension()
        self.indices = {}  # User ID -> FAISS index
        self.memories = {}  # User ID -> list of memories
        self.memory_dir = os.path.join(os.path.dirname(__file__), "memory_data")
        
        # Create memory directory if it doesn't exist
        os.makedirs(self.memory_dir, exist_ok=True)
        
        # Load existing memories
        self._load_memories()
    
    def _get_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for text"""
        return self.model.encode([text])[0]
    
    def _load_memories(self):
        """Load memories from disk"""
        if not os.path.exists(self.memory_dir):
            return
            
        for filename in os.listdir(self.memory_dir):
            if filename.endswith(".json"):
                user_id = filename.split(".")[0]
                file_path = os.path.join(self.memory_dir, filename)
                
                try:
                    with open(file_path, "r") as f:
                        self.memories[user_id] = json.load(f)
                        
                    # Create FAISS index for this user
                    if self.memories[user_id]:
                        embeddings = np.array([
                            memory["embedding"] for memory in self.memories[user_id]
                        ]).astype('float32')
                        
                        index = faiss.IndexFlatL2(self.embedding_size)
                        index.add(embeddings)
                        self.indices[user_id] = index
                except Exception as e:
                    print(f"Error loading memories for {user_id}: {str(e)}")
    
    def _save_memories(self, user_id: str):
        """Save memories to disk"""
        file_path = os.path.join(self.memory_dir, f"{user_id}.json")
        
        try:
            with open(file_path, "w") as f:
                json.dump(self.memories[user_id], f)
        except Exception as e:
            print(f"Error saving memories for {user_id}: {str(e)}")
    
    def add(self, user_id: str, query: str, response: str):
        """Add a new memory"""
        # Initialize user memories if not exists
        if user_id not in self.memories:
            self.memories[user_id] = []
            self.indices[user_id] = faiss.IndexFlatL2(self.embedding_size)
        
        # Generate embedding for the query
        embedding = self._get_embedding(query).tolist()
        
        # Create memory object
        memory = {
            "query": query,
            "response": response,
            "embedding": embedding,
            "timestamp": time.time()
        }
        
        # Add to memories
        self.memories[user_id].append(memory)
        
        # Add to FAISS index
        self.indices[user_id].add(np.array([embedding]).astype('float32'))
        
        # Save to disk
        self._save_memories(user_id)
    
    def search(self, query: str, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant memories"""
        if user_id not in self.memories or not self.memories[user_id]:
            return []
        
        # Generate embedding for the query
        query_embedding = self._get_embedding(query).astype('float32').reshape(1, -1)
        
        # Search in FAISS index
        distances, indices = self.indices[user_id].search(query_embedding, limit)
        
        # Get the memories
        results = []
        for idx in indices[0]:
            if idx < len(self.memories[user_id]):
                memory = self.memories[user_id][idx].copy()
                # Remove embedding from result
                memory.pop("embedding", None)
                results.append(memory)
        
        return results
    
    def get_recent(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most recent memories"""
        if user_id not in self.memories:
            return []
        
        # Sort by timestamp (newest first) and take the top 'limit'
        recent_memories = sorted(
            self.memories[user_id], 
            key=lambda x: x.get("timestamp", 0), 
            reverse=True
        )[:limit]
        
        # Remove embeddings from results
        return [{k: v for k, v in memory.items() if k != "embedding"} 
                for memory in recent_memories]