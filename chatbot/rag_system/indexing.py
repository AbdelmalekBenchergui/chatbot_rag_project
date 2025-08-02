from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import DirectoryLoader, TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from functools import partial
from django.conf import settings
from ..config import embeddings


class IndexingService:
    @staticmethod
    def build_vector_store():
        try:
            # Charger documents
            txt_loader = DirectoryLoader(
                str(settings.DATA_FOLDER), 
                glob="**/*.txt", 
                loader_cls=partial(TextLoader, encoding="utf-8")
            )
            pdf_loader = DirectoryLoader(
                str(settings.DATA_FOLDER), 
                glob="**/*.pdf", 
                loader_cls=PyPDFLoader
            )
            
            docs = txt_loader.load() + pdf_loader.load()
            
            if not docs:
                raise Exception("Aucun document trouvé à indexer")
            
            # Split documents
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=200, 
                chunk_overlap=20
            )
            chunks = splitter.split_documents(docs)
            
            # Créer l'index FAISS
            vectorstore = FAISS.from_documents(chunks, embeddings)
            vectorstore.save_local(str(settings.FAISS_INDEX_DIR))
            
            return True, "Indexation terminée avec succès"
            
        except Exception as e:
            return False, f"Erreur lors de l'indexation : {str(e)}"


            