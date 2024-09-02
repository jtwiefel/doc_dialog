
from codetiming import Timer
from pprint import pprint
from tqdm import tqdm

from FlagEmbedding import BGEM3FlagModel
REPO_ID = 'BAAI/bge-m3'
CACHE_DIR = "/workspace/volumes/models"
class EmbeddingModel:
    def __init__(self, verbose = False):
        self.verbose = verbose
        self.embedding_model = BGEM3FlagModel(REPO_ID,  use_fp16=True)
    
    def embed(self, text):
        """converts text to an embedding

        Args:
            text (_type_): input text

        Returns:
            _type_: embedding
        """        
        return self.embedding_model.encode(text)['dense_vecs']
    
    def __call__(self, text):
        """converts text to an embedding

        Args:
            text (_type_): input text

        Returns:
            _type_: embedding
        """        
        return self.embedding_model.encode(text)['dense_vecs']

    def embed_documents(self, texts):
        """converts multiple texts to embeddings

        Args:
            texts (_type_): list of texts

        Returns:
            _type_: list of embeddings
        """        
        embeddings = []
        if not self.verbose:
            embeddings = self.embedding_model.encode(texts)['dense_vecs']
        else:
            for text in tqdm(texts):
                embedding = self.embedding_model.encode(text)['dense_vecs']
                print(f"text: {text[:50]}")
                print(f"embedding: {embedding[:10]}")
                embeddings.append(embedding)
        return embeddings
