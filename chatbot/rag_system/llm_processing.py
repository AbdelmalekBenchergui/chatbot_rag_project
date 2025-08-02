# rag_app/services/llm_service.py
import os
import re
from collections import defaultdict
from typing import List, Tuple, TypedDict
from django.conf import settings
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from ..config import embeddings, openai_api_key

class State(TypedDict):
    question: str
    context: List[Tuple[Document, float]]
    results: List[dict]
    conversation_context: List[dict]  
class LLMService:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", api_key=openai_api_key)
        self.vector_store = None
        self.graph = None
        self.build_graph()
    
    def merge_context_by_file(self, context: List[Tuple[Document, float]]):
        grouped = defaultdict(list)
        for doc, score in context:
            source = doc.metadata.get("source", "inconnu")
            grouped[source].append((doc.page_content, score))
        
        merged = []
        for filepath, entries in grouped.items():
            contents = [e[0] for e in entries]
            scores = [e[1] for e in entries]
            full_content = "\n".join(contents)
            avg_score = sum(scores) / len(scores)
            filename = os.path.basename(filepath)
            merged.append((filepath, filename, full_content, avg_score))
        
        return merged
    
    def build_conversation_context_text(self, conversation_context: List[dict]) -> str:
        """Construire le contexte de conversation pour le prompt"""
        if not conversation_context:
            return ""
        
        context_text = "\n\nContexte de la conversation précédente :\n"
        for msg in conversation_context: 
            role = "Utilisateur" if msg["role"] == "user" else "Assistant"
            context_text += f"{role}: {msg['content']}\n"
        
        return context_text
    
    def build_graph(self):
        index_path = settings.FAISS_INDEX_DIR / "index.faiss"
        
        if index_path.exists():
            self.vector_store = FAISS.load_local(
                str(settings.FAISS_INDEX_DIR), 
                embeddings, 
                allow_dangerous_deserialization=True
            )
            
            def retrieve(state: State):
                docs_with_scores = self.vector_store.similarity_search_with_score(
                    state["question"], k=10
                )
                return {"context": docs_with_scores}
            
            def generate(state: State):
                filtered = []
                merged_context = self.merge_context_by_file(state["context"])
                

                
                # Construire le contexte de conversation
                conversation_context_text = self.build_conversation_context_text(
                    state.get("conversation_context", [])
                )
                
                for filepath, filename, content, score_faiss in merged_context:
                    prompt = f"""
                    Tu es un recruteur en ressources humaines. Ta tâche est d'évaluer si ce candidat correspond à l'offre suivante :
                    
                    Besoin de l'entreprise :
                    "{state['question']}"
                    
                    {conversation_context_text}
                    
                    Tu dois :
                    1. Lire le contenu du CV.
                    2. Attribuer une note sur 10 selon la pertinence du profil.
                    3. Prendre une décision : **À conserver** ou **À écarter**.
                    4. Donner une justification claire et concise, **en un seul paragraphe**.
                    
                    Format attendu **obligatoire** :
                    NOTE: X/10 — Décision : À conserver / À écarter  
                    Justification : [un seul paragraphe sans saut de ligne, 3-4 phrases max]
                    
                    Texte du CV :
                    {content}
                    """
                    
                    response = self.llm.invoke([
                        {"role": "system", "content": "Tu es un assistant RH."},
                        {"role": "user", "content": prompt}
                    ])
                    
                    match = re.search(r"NOTE\s*:\s*(\d+)", response.content)
                    score_llm = int(match.group(1)) if match else 0
                    
                    filtered.append({
                        "score_faiss": round(float(score_faiss), 3),
                        "score_llm": score_llm,
                        "justification": response.content.strip(),
                        "filename": filename,
                        "filepath": filepath,
                    })
                
                filtered = sorted(filtered, key=lambda x: x["score_llm"], reverse=True)
                return {"results": filtered}
            
            builder = StateGraph(State)
            builder.add_node("retrieve", retrieve)
            builder.add_node("generate", generate)
            builder.set_entry_point("retrieve")
            builder.add_edge("retrieve", "generate")
            self.graph = builder.compile()
        else:
            self.vector_store = None
            self.graph = None
    
    def ask_question(self, question: str, conversation_context: List[dict] = None):
        """
        Traiter une question avec contexte de conversation optionnel
        
        Args:
            question: La question à traiter
            conversation_context: Liste des messages précédents de la conversation
        
        Returns:
            Tuple (results, error)
        """
        if self.graph is None:
            return None, "Index FAISS non disponible. Exécutez l'indexation d'abord."
        
        try:
            state = {
                "question": question,
                "conversation_context": conversation_context or []
            }
            result = self.graph.invoke(state)
            return result.get("results", []), None
        except Exception as e:
            return None, f"Erreur lors du traitement : {str(e)}"

# Instance globale du service
llm_service = LLMService()
