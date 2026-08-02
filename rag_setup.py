from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

with open("traffic_rules.txt", "r", encoding="utf-8") as f:
    rules = f.read().split("\n\n")

model = SentenceTransformer("all-MiniLM-L6-v2")

embeddings = model.encode(rules)

dimension = embeddings.shape[1]

index = faiss.IndexFlatL2(dimension)

index.add(np.array(embeddings))

print("Rules loaded:", len(rules))
print("FAISS index created")