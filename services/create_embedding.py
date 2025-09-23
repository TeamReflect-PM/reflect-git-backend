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
        print("Embedding length:", len(embedding))
        return embedding
    except Exception as e:
        # Use the original exception message, don't reference `embedding` which may not exist
        raise Exception("Embedding generation failed: " + str(e))