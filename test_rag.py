from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

with open("traffic_rules.txt", "r", encoding="utf-8") as f:
    rules = f.read().split("\n\n")

model = SentenceTransformer("all-MiniLM-L6-v2")

embeddings = model.encode(rules)

index = faiss.IndexFlatL2(embeddings.shape[1])

index.add(np.array(embeddings))

query = "red traffic light"

query_embedding = model.encode([query])

distances, indices = index.search(
    np.array(query_embedding),
    k=1
)

print("Retrieved Rule:\n")
print(rules[indices[0][0]])