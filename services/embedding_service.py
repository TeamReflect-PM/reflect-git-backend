import vertexai
from vertexai.language_models import TextEmbeddingModel
from config import PROJECT_ID, REGION, EMBEDDING_MODEL

vertexai.init(project=PROJECT_ID, location=REGION)
embedding_model = TextEmbeddingModel.from_pretrained(EMBEDDING_MODEL)

def get_embedding(text: str):
    """
    Converts any text (journal summary or query) into a vector embedding.
    """
    try:
        embedding = embedding_model.get_embeddings([text])[0].values
        return embedding
    except Exception as e:
        raise RuntimeError(f"Embedding generation failed: {str(e)}")

