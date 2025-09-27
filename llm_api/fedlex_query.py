# fedlex_search.py
import os, json, pickle, numpy as np, pandas as pd
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

STORE = "./fedlex_store"

def load_store(store_dir=STORE):
    with open(os.path.join(store_dir, "store_meta.json"), "r", encoding="utf-8") as f:
        meta = json.load(f)
    corpus = pd.read_parquet(os.path.join(store_dir, "corpus.parquet"))
    embs = np.load(os.path.join(store_dir, "embeddings.npy"))
    with open(os.path.join(store_dir, "bm25_tokens.pkl"), "rb") as f:
        tokens = pickle.load(f)
    bm25 = BM25Okapi(tokens)
    model = SentenceTransformer(meta["model_name"])
    return meta, corpus, embs, bm25, model

def hybrid_search(query, topk=8, w_dense=0.55):
    meta, corpus, embs, bm25, model = load_store(STORE)
    q = model.encode([query], normalize_embeddings=True).astype("float32")[0]
    dense_scores = (embs @ q)  # cosine because normalized
    # BM25 (higher is better); normalize to [0,1]
    bm25_scores = np.array(bm25.get_scores(query.lower().split()), dtype="float32")
    if bm25_scores.max() > 0:
        bm25_scores = bm25_scores / (bm25_scores.max() + 1e-9)
    # fuse
    fused = w_dense * dense_scores + (1 - w_dense) * bm25_scores
    top_idx = np.argsort(-fused)[:topk]
    out = corpus.iloc[top_idx].copy()
    out["score_dense"] = dense_scores[top_idx]
    out["score_bm25"] = bm25_scores[top_idx]
    out["score_fused"] = fused[top_idx]
    return out.sort_values("score_fused", ascending=False)

if __name__ == "__main__":
    hits = hybrid_search("Haftung aus unerlaubter Handlung", topk=5)
    for _, r in hits.iterrows():
        print(f"[{r['score_fused']:.3f}] {r['cite']}")
        print(r["text"][:300].replace("\n", " "), "\n")
