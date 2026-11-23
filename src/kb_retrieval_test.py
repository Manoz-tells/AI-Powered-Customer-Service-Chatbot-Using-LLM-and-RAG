import os

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings


project_root = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

index_path = os.path.join(
    project_root,
    "faiss_kb_index"
)


embeddings = HuggingFaceEmbeddings(
    model_name="hkunlp/instructor-large"
)


vectordb = FAISS.load_local(
    index_path,
    embeddings,
    allow_dangerous_deserialization=True
)


query = "What is the policy for duplicate payment refunds?"

results = vectordb.similarity_search(
    query,
    k=2
)


print("\nQUERY:")
print(query)

print("\nRETRIEVED DOCUMENTS:")

for i, document in enumerate(results, start=1):

    print(f"\n--- Result {i} ---")
    print("Source:", document.metadata.get("source"))
    print("Content:")
    print(document.page_content)