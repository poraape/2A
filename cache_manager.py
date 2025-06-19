import streamlit as st
import faiss
import json
import numpy as np
from sentence_transformers import SentenceTransformer
import os

# DevÆGENT-I (Intelligence): Esta classe encapsula a "memória" do nosso agente.
# Ela permite que o agente se lembre de perguntas e respostas anteriores,
# respondendo instantaneamente a perguntas similares e economizando custos de API.

@st.cache_resource
def load_sentence_transformer():
    """Carrega o modelo de embedding e o armazena no cache do Streamlit."""
    return SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

class SemanticCacheManager:
    def __init__(self, cache_dir="cache_data"):
        """
        Inicializa o gerenciador de cache, carregando o modelo e os dados do cache se existirem.
        """
        self.model = load_sentence_transformer()
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        self.cache_dir = cache_dir
        self.index_file = os.path.join(cache_dir, "cache.index")
        self.data_file = os.path.join(cache_dir, "cache_data.json")

        # Garante que o diretório de cache exista
        os.makedirs(self.cache_dir, exist_ok=True)

        self._load_cache()

    def _load_cache(self):
        """Carrega o índice FAISS e o mapa de dados do disco."""
        if os.path.exists(self.index_file) and os.path.exists(self.data_file):
            self.index = faiss.read_index(self.index_file)
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self.qa_data = json.load(f)
        else:
            # Inicializa um cache vazio
            self.index = faiss.IndexFlatL2(self.embedding_dim)
            self.qa_data = {}

    def _save_cache(self):
        """Salva o índice FAISS e o mapa de dados no disco."""
        faiss.write_index(self.index, self.index_file)
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.qa_data, f, indent=4)

    def add_to_cache(self, question: str, answer: str):
        """
        Adiciona um novo par de pergunta e resposta ao cache.
        1. Gera o embedding da pergunta.
        2. Adiciona o embedding ao índice FAISS.
        3. Salva o par (pergunta, resposta) no arquivo de dados.
        """
        try:
            embedding = self.model.encode([question], convert_to_tensor=False).astype('float32')
            new_id = self.index.ntotal
            self.index.add(embedding)
            self.qa_data[str(new_id)] = {"question": question, "answer": answer}
            self._save_cache()
        except Exception as e:
            st.error(f"Erro ao adicionar ao cache: {e}")

    def search_cache(self, query_question: str, threshold: float = 0.9):
        """
        Busca no cache por uma pergunta semanticamente similar.
        Retorna a resposta se a similaridade for maior que o limiar, caso contrário, retorna None.
        """
        if self.index.ntotal == 0:
            return None # Cache está vazio

        try:
            query_embedding = self.model.encode([query_question]).astype('float32')
            # Busca pelo vizinho mais próximo (k=1)
            distances, ids = self.index.search(query_embedding, 1)
            
            top_id = ids[0][0]
            distance = distances[0][0]

            # Converte a distância L2 em um score de similaridade (0 a 1)
            # Esta é uma heurística simples, pode ser ajustada.
            similarity = 1 / (1 + distance)

            if similarity >= threshold:
                st.toast(f"♻️ Resposta do cache! Similaridade: {similarity:.2f}")
                return self.qa_data[str(top_id)]["answer"]
            
            return None
        except Exception as e:
            st.error(f"Erro ao buscar no cache: {e}")
            return None
