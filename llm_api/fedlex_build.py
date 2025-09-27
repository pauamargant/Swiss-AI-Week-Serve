#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Fedlex → Multilingual RAG (DE/FR/IT) — Offline Builder
(Chroma-safe metadata: no None values)
- Now robust to unknown/aliased languages:
  * Normalizes language inputs (e.g., "arab" → "ar")
  * Skips Fedlex compilations for langs Fedlex doesn't publish (DE/FR/IT) with a warning
  * Still allows any lang for custom URL/FILE sources
"""

import os, re, json, argparse, pickle
from typing import Any, Dict, List, Optional, Tuple
import requests
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
from lxml import etree
from SPARQLWrapper import SPARQLWrapper, JSON as SPARQL_JSON
from dateutil.parser import parse as parse_dt
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi

# --- Chroma
import chromadb
from chromadb.config import Settings

# -----------------------------
# Config & constants
# -----------------------------
FEDLEX_SPARQL = "https://fedlex.data.admin.ch/sparqlendpoint"
JOLUX = "http://data.legilux.public.lu/resource/ontology/jolux#"

# Fedlex-supported langs (for SPARQL)
LANG_URI = {
    "de": "http://publications.europa.eu/resource/authority/language/DEU",
    "fr": "http://publications.europa.eu/resource/authority/language/FRA",
    "it": "http://publications.europa.eu/resource/authority/language/ITA",
}

# Human-friendly aliases → ISO-ish codes
LANG_ALIASES = {
    "arab": "ar", "arabic": "ar",
    "ger": "de", "deu": "de", "german": "de",
    "fre": "fr", "fra": "fr", "french": "fr",
    "ita": "it", "italian": "it",
}

def normalize_lang(x: str) -> str:
    x = (x or "").strip().lower()
    return LANG_ALIASES.get(x, x)

SUPPORTED_FEDLEX_LANGS = set(LANG_URI.keys())

FILETYPE_HTML = "http://publications.europa.eu/resource/authority/file-type/HTML"
FILETYPE_XML  = "http://publications.europa.eu/resource/authority/file-type/XML"

# Default Fedlex compilations (stable ‘cc’ URIs)
DEFAULT_CC_URIS = {
    "co": "https://fedlex.data.admin.ch/eli/cc/27/317_321_377",  # OR/CO  (RS 220)
    "cc": "https://fedlex.data.admin.ch/eli/cc/24/233_245_233",  # ZGB/CC (RS 210)
}
DEFAULT_RS_HINT = {"co": "220", "cc": "210"}

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
EMB_DIM = 384
HYBRID_W_DENSE = 0.55
MIN_CHUNK_LEN = 60

# -----------------------------
# SPARQL helpers
# -----------------------------
def run_sparql(query: str):
    sp = SPARQLWrapper(FEDLEX_SPARQL)
    sp.setMethod("POST")
    sp.setReturnFormat(SPARQL_JSON)
    sp.setQuery(query)
    return sp.query().convert()["results"]["bindings"]

def get_latest_manifestation(cc_uri: str, lang: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    # Safe: if Fedlex doesn't support this lang, signal no result
    if lang not in LANG_URI:
        return None, None, None
    lang_uri = LANG_URI[lang]
    q = f"""
    PREFIX jolux: <{JOLUX}>
    SELECT ?date ?ft ?url
    WHERE {{
      ?work jolux:isMemberOf <{cc_uri}>;
            jolux:dateApplicability ?date;
            jolux:isRealizedBy ?expr.
      ?expr jolux:language <{lang_uri}>;
            jolux:isEmbodiedBy ?man.
      ?man  jolux:format ?ft;
            jolux:isExemplifiedBy ?url.
      FILTER (?ft IN (<{FILETYPE_XML}>, <{FILETYPE_HTML}>))
    }}
    ORDER BY DESC(?date)
    """
    rows = run_sparql(q)
    if not rows:
        return None, None, None

    # Prefer XML from the latest date if present; otherwise HTML
    date_by_type: Dict[str, Tuple[str, str]] = {}
    latest_date: Optional[str] = None
    for r in rows:
        d = r["date"]["value"]; ft = r["ft"]["value"]; url = r["url"]["value"]
        if latest_date is None or d > latest_date:
            latest_date = d
        if ft not in date_by_type:
            date_by_type[ft] = (d, url)

    if FILETYPE_XML in date_by_type:
        d, u = date_by_type[FILETYPE_XML]
        return d, FILETYPE_XML, u
    if FILETYPE_HTML in date_by_type:
        d, u = date_by_type[FILETYPE_HTML]
        return d, FILETYPE_HTML, u
    return None, None, None

# -----------------------------
# Parsing helpers
# -----------------------------
def parse_akn_xml(xml_text: str) -> List[Dict[str, Any]]:
    chunks: List[Dict[str, Any]] = []
    try:
        root = etree.fromstring(xml_text.encode("utf-8"))
    except Exception:
        root = etree.fromstring(xml_text)

    ns = root.nsmap.copy()
    if None in ns:
        ns["akn"] = ns.pop(None)

    xpaths = [".//akn:article", ".//article"]
    for xp in xpaths:
        arts = root.xpath(xp, namespaces=ns) if ns else root.xpath(xp)
        if not arts: continue
        for a in arts:
            num_nodes = a.xpath(".//akn:num/text()", namespaces=ns) if ns else a.xpath(".//num/text()")
            num = num_nodes[0].strip() if num_nodes else None

            paragraphs = a.xpath(".//akn:paragraph", namespaces=ns) if ns else a.xpath(".//paragraph")
            if paragraphs:
                texts = []
                for p in paragraphs:
                    txt = " ".join(p.itertext()).strip()
                    if txt: texts.append(txt)
                text = "\n\n".join(texts).strip()
            else:
                text = " ".join(a.itertext()).strip()

            if text and len(text) >= MIN_CHUNK_LEN:
                chunks.append({"article_number": num, "text": text})
        if chunks: break
    return chunks

ART_PATTERNS = [
    r"(?=^Art\.?\s+\d+[a-z]?\s)",
    r"(?=^Artikel\s+\d+[a-z]?\s)",
    r"(?=^Articolo\s+\d+[a-z]?\s)",
]
ART_SPLIT = re.compile("|".join(ART_PATTERNS), re.MULTILINE)

def parse_html_to_articles(html_text: str) -> List[Dict[str, Any]]:
    soup = BeautifulSoup(html_text, "lxml")
    main = soup.find("main") or soup.find("body") or soup
    for tag in main.find_all(["script", "style", "noscript"]):
        tag.decompose()

    text = main.get_text("\n")
    text = re.sub(r"\n{2,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text).strip()

    parts = ART_SPLIT.split(text)
    chunks: List[Dict[str, Any]] = []
    for p in parts:
        p = p.strip()
        if len(p) < MIN_CHUNK_LEN:
            continue
        m = re.match(r"^(?:Art\.?|Artikel|Articolo)\s+([0-9][0-9a-z]*)", p)
        art_num = m.group(1) if m else None
        chunks.append({"article_number": art_num, "text": p})
    if not chunks and len(text) >= MIN_CHUNK_LEN:
        chunks = [{"article_number": None, "text": text}]
    return chunks

# -----------------------------
# Source loaders
# -----------------------------
def _fetch_text(url_or_path: str, is_file: bool) -> str:
    if is_file:
        with open(url_or_path, "rb") as f:
            raw = f.read()
        try:
            return raw.decode("utf-8")
        except Exception:
            return raw.decode("latin-1", errors="ignore")
    else:
        r = requests.get(url_or_path, timeout=40); r.raise_for_status()
        return r.text

def fetch_manifest_and_chunks(cc_uri: str, lang: str) -> Tuple[Optional[str], Optional[str], List[Dict[str, Any]], Optional[str]]:
    date_app, ft, url = get_latest_manifestation(cc_uri, lang)
    if not url: return None, None, [], None
    txt = _fetch_text(url, is_file=False)
    if ft == FILETYPE_XML or url.lower().endswith(".xml"):
        try: chunks = parse_akn_xml(txt)
        except Exception: chunks = parse_html_to_articles(txt)
        filetype = "XML"
    else:
        chunks = parse_html_to_articles(txt)
        filetype = "HTML"
    return date_app, filetype, chunks, url

def load_source_record(src: Dict[str, Any], lang: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    stype = src["type"]

    if stype == "fedlex_cc":
        cc_uri = src["uri"]
        cc_key = src.get("id", cc_uri.split("/")[-1])
        rs_hint = src.get("rs_hint", "")

        # If lang unsupported by Fedlex, nothing to fetch
        if lang not in SUPPORTED_FEDLEX_LANGS:
            print(f"[WARN] Skipping Fedlex {cc_key} ({cc_uri}) for unsupported language '{lang}'. "
                  f"Supported: {sorted(SUPPORTED_FEDLEX_LANGS)}")
            return rows

        valid_date, ft, chunks, url = fetch_manifest_and_chunks(cc_uri, lang)
        for i, ch in enumerate(chunks):
            if not ch["text"] or len(ch["text"]) < MIN_CHUNK_LEN: continue
            rows.append({
                "chunk_id": f"{cc_uri}#{lang}#art{ch['article_number'] or i}",
                "cc_key": cc_key, "cc_uri": cc_uri, "rs_hint": rs_hint,
                "lang": lang, "article_number": ch["article_number"],
                "text": ch["text"],
                "valid_from": valid_date, "valid_to": None,
                "source_uri": url, "filetype": ft,
            })
        return rows

    if stype == "url":
        url = src["url"]
        label = src.get("id", "url")
        rs_hint = src.get("rs_hint", "")
        txt = _fetch_text(url, is_file=False)
        if url.lower().endswith(".xml"):
            try: chunks = parse_akn_xml(txt); ft = "XML"
            except Exception: chunks = parse_html_to_articles(txt); ft = "HTML"
        else:
            chunks = parse_html_to_articles(txt); ft = "HTML"
        for i, ch in enumerate(chunks):
            if not ch["text"] or len(ch["text"]) < MIN_CHUNK_LEN: continue
            rows.append({
                "chunk_id": f"{url}#{lang}#art{ch['article_number'] or i}",
                "cc_key": label, "cc_uri": url, "rs_hint": rs_hint,
                "lang": lang, "article_number": ch["article_number"],
                "text": ch["text"],
                "valid_from": None, "valid_to": None,
                "source_uri": url, "filetype": ft,
            })
        return rows

    if stype == "file":
        path = src["path"]
        label = src.get("id", os.path.basename(path))
        rs_hint = src.get("rs_hint", "")
        txt = _fetch_text(path, is_file=True)
        if path.lower().endswith(".xml"):
            try: chunks = parse_akn_xml(txt); ft = "XML"
            except Exception: chunks = parse_html_to_articles(txt); ft = "HTML"
        else:
            chunks = parse_html_to_articles(txt); ft = "HTML"
        for i, ch in enumerate(chunks):
            if not ch["text"] or len(ch["text"]) < MIN_CHUNK_LEN: continue
            rows.append({
                "chunk_id": f"{path}#{lang}#art{ch['article_number'] or i}",
                "cc_key": label, "cc_uri": path, "rs_hint": rs_hint,
                "lang": lang, "article_number": ch["article_number"],
                "text": ch["text"],
                "valid_from": None, "valid_to": None,
                "source_uri": path, "filetype": ft,
            })
        return rows

    raise ValueError(f"Unknown source type: {stype}")

# -----------------------------
# Build corpus
# -----------------------------
def build_corpus(sources: List[Dict[str, Any]], langs: List[str]) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for lang in langs:
        for src in sources:
            try:
                rows.extend(load_source_record(src, lang))
            except Exception as e:
                print(f"[WARN] Failed source {src} lang={lang}: {e}")
    df = pd.DataFrame(rows).drop_duplicates(subset=["chunk_id"]).reset_index(drop=True)
    return df

# -----------------------------
# Helpers for Chroma metadata
# -----------------------------
SAFE_META_KEYS = ["cc_key","cc_uri","rs_hint","lang","article_number","valid_from","valid_to","source_uri","filetype","cite"]

def _normalize_meta(row: Dict[str, Any]) -> Dict[str, Any]:
    """Chroma Rust API allows only bool/int/float/str/sparsevec. No None."""
    out: Dict[str, Any] = {}
    for k in SAFE_META_KEYS:
        v = row.get(k, "")
        if v is None:
            v = ""
        # cast everything to str (safest for mixed/nullable fields like dates & article numbers)
        out[k] = str(v)
    return out

# -----------------------------
# Main
# -----------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="./fedlex_store", help="Output folder (persistent store)")
    ap.add_argument("--langs", nargs="+", default=["de","fr"], help="Languages to fetch (e.g., de fr it ar ...)")
    ap.add_argument("--uris", type=str, default="co,cc",
                    help="Comma-separated keys from built-ins (co,cc) or ignored if --config is given")
    ap.add_argument("--config", type=str, default=None,
                    help="Optional JSON config path describing sources")
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--w_dense", type=float, default=HYBRID_W_DENSE)
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    chroma_dir = os.path.join(args.out, "chroma")
    os.makedirs(chroma_dir, exist_ok=True)

    # Resolve sources
    if args.config:
        with open(args.config, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        sources = cfg["sources"]
        langs   = cfg.get("langs", args.langs)
        w_dense = float(cfg.get("w_dense", args.w_dense))
    else:
        keys = [k.strip() for k in args.uris.split(",") if k.strip()]
        sources = [{"type":"fedlex_cc",
                    "id": k,
                    "uri": DEFAULT_CC_URIS[k],
                    "rs_hint": DEFAULT_RS_HINT.get(k,"")} for k in keys]
        langs = args.langs
        w_dense = args.w_dense

    # Normalize language inputs (aliases) and dedupe while preserving order
    dedup = []
    seen = set()
    for l in [normalize_lang(x) for x in langs]:
        if l not in seen:
            dedup.append(l); seen.add(l)
    langs = dedup

    print(f"[Build] Languages (normalized): {langs}")
    print(f"[Build] Sources ({len(sources)}): {sources}")

    # Build corpus
    corpus = build_corpus(sources, langs)
    if corpus.empty:
        print("[Build] No data extracted; abort.")
        return

    # Add citation
    def make_cite(row):
        rs = row.get("rs_hint") or ""
        art = row.get("article_number") or "?"
        lang = (row.get("lang") or "").upper()
        label = f"RS {rs}" if rs else row.get("cc_key", "")
        return f"{label}, Art. {art} – {lang}"
    corpus["cite"] = corpus.apply(make_cite, axis=1)

    # Embeddings
    print("[Build] Embedding with SentenceTransformer...")
    model = SentenceTransformer(MODEL_NAME)
    embs = model.encode(
        corpus["text"].tolist(),
        batch_size=64,
        show_progress_bar=True,
        normalize_embeddings=True
    )
    embs = np.asarray(embs, dtype="float32")
    assert embs.shape == (len(corpus), EMB_DIM)

    # Tokenize for BM25 (saved tokens; BM25Okapi built at query time)
    tokenized = [t.lower().split() for t in corpus["text"].tolist()]
    bm25_path = os.path.join(args.out, "bm25_tokens.pkl")
    with open(bm25_path, "wb") as f:
        pickle.dump(tokenized, f)

    # Save embeddings and corpus
    np.save(os.path.join(args.out, "embeddings.npy"), embs)
    corpus_path = os.path.join(args.out, "corpus.parquet")
    corpus.to_parquet(corpus_path, index=False)

    # Persist in Chroma
    print("[Build] Saving to Chroma (persistent)...")
    client = chromadb.PersistentClient(path=chroma_dir, settings=Settings(anonymized_telemetry=False))
    if args.overwrite:
        try:
            client.delete_collection("fedlex_rag")
        except Exception:
            pass
    coll = client.get_or_create_collection(name="fedlex_rag")

    # Prepare inserts
    ids = [str(i) for i in range(len(corpus))]

    # Normalize metadatas: replace None → "" and cast to str
    SAFE_META_KEYS = ["cc_key","cc_uri","rs_hint","lang","article_number","valid_from","valid_to","source_uri","filetype","cite"]
    def _normalize_meta(row: Dict[str, Any]) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        for k in SAFE_META_KEYS:
            v = row.get(k, "")
            if v is None:
                v = ""
            out[k] = str(v)
        return out

    meta_records = corpus[SAFE_META_KEYS].to_dict(orient="records")
    metadatas = [_normalize_meta(m) for m in meta_records]
    documents = corpus["text"].tolist()

    # Chunked add
    B = 2048
    for s in range(0, len(ids), B):
        e = min(s+B, len(ids))
        coll.add(
            ids=ids[s:e],
            documents=documents[s:e],
            metadatas=metadatas[s:e],
            embeddings=embs[s:e]
        )

    # Save store metadata
    meta = {
        "model_name": MODEL_NAME,
        "emb_dim": EMB_DIM,
        "w_dense": float(w_dense),
        "n_docs": int(len(corpus)),
        "supported_fedlex_langs": sorted(SUPPORTED_FEDLEX_LANGS),
    }
    with open(os.path.join(args.out, "store_meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    print(f"[Build] Done. Docs: {len(corpus)}  → {args.out}")
    print(f"  - {corpus_path}")
    print(f"  - embeddings.npy")
    print(f"  - bm25_tokens.pkl")
    print(f"  - store_meta.json")
    print(f"  - chroma/ (persistent collection 'fedlex_rag')")

if __name__ == "__main__":
    main()
