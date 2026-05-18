# AgroScan — Fruit classification + RAG assistant

## What this project does

- **Vision model (PyTorch / ResNet50)** classifies fruit condition into 3 classes: **overripe / ripe / unripe**.
- **Energy-based OOD detection** flags high-energy inputs as **UNKNOWN / NOT FRUIT**.
- **BLIP** generates an image caption (via Hugging Face Inference API).
- **RAG (ChromaDB + SentenceTransformers)** indexes agriculture PDFs/texts and retrieves relevant chunks.
- **Groq LLM** generates a **strict JSON** response (grounded in retrieved documents) for advice + prevention.

## Quick start

1. Install dependencies (Python **3.11.15**).
2. Set environment variables in a `.env` file.
3. (Optional) Start ChromaDB via Docker.
4. Run the Streamlit UI.

## Prerequisites

- Python **3.11.15**
- A trained classifier checkpoint at `models/checkpoints/best_model.pth`
- Environment variables:
  - `GROQ_API_KEY` (Groq)
  - `HUGGINGFACE_API_KEY` (or `HF_API_TOKEN`) for BLIP captioning
  - `OOD_THRESHOLD` after calibration

## Environment variables

Create a `.env` file at project root:

```bash
# Groq
GROQ_API_KEY=your_groq_key
# Optional overrides
# GROQ_MODEL=llama-3.3-70b-versatile
# GROQ_TEMPERATURE=0.1
# GROQ_MAX_TOKENS=900

# Hugging Face (for BLIP)
HUGGINGFACE_API_KEY=your_hf_key
# Optional overrides
# BLIP_MODEL_ID=Salesforce/blip-image-captioning-base

# OOD detection
# Set by calibration script
OOD_THRESHOLD=
OOD_THRESHOLD_PERCENTILE=95
# Optional validation data overrides
OOD_VAL_DIR=
OOD_VAL_CSV=./models/logs/split_val.csv
OOD_DATA_ROOT=
```

## Directory layout

- `app.py` — Streamlit UI
- `src/load_model.py` — loads the PyTorch checkpoint
- `src/predict.py` — runs preprocessing + inference
- `src/preprocess.py` — image preprocessing (224x224)
- `src/ood.py` — energy score + threshold-based OOD decision
- `scripts/calibrate_ood_threshold.py` — calibrates `OOD_THRESHOLD` from validation images
- `src/blip_caption.py` — BLIP captioning via HuggingFace InferenceClient
- `rag/vector_store.py` — ChromaDB indexing + search
- `rag/chat.py` — builds retrieved context and calls Groq
- `docker/docker-compose.yaml` — optional ChromaDB service

## 1) Running the web app (Streamlit)

```bash
streamlit run app.py
```

Usage:

- Upload an image in **“Crop Vision”** to get classification + BLIP caption.
- In **“AI Assistant”**, click **Build / refresh knowledge base** (indexes docs into ChromaDB).
- Ask questions in the chat; answers are returned as structured, grounded JSON.

## 2) Use the model locally (Python 3.11.15)

### 2.1 Image classification only

Create `local_classify.py`:

```python
from PIL import Image
from src.load_model import load_model
from src.predict import predict_image

image = Image.open("assets/overripe.jpg").convert("RGB")

model, class_names, device = load_model()
pred = predict_image(image=image, model=model, class_names=class_names, device=device)

print("Predicted class:", pred["class_label"])
print("Final label:", pred["final_label"])
print("Confidence:", pred["confidence"])
print("Energy:", pred["energy_score"])
print("OOD threshold:", pred["ood_threshold"])
print("Is OOD:", pred["is_ood"])
print("Probabilities:", pred["probabilities"])
```

Run:

```bash
python local_classify.py
```

### 2.2 Calibrate Energy-Based OOD detection

Energy is computed from logits:

```text
energy(x) = -logsumexp(logits)
```

Use in-distribution validation fruit images to set a threshold. The default policy is the 95th percentile of validation energies, meaning roughly 95% of known validation fruit remain accepted while unusually high-energy samples are flagged as unknown.

```bash
python scripts/calibrate_ood_threshold.py --val-dir path/to/validation --percentile 95
```

The script writes the calibrated value to `.env`:

```bash
OOD_THRESHOLD=...
```

At inference time:

- if `energy_score > OOD_THRESHOLD`, `final_label` becomes `UNKNOWN / NOT FRUIT`
- otherwise, `final_label` stays equal to the normal fruit class

### 2.3 RAG assistant call (without UI)

This calls:

- vector retrieval from Chroma
- Groq JSON generation

Create `local_rag_chat.py`:

```python
from rag.vector_store import ChromaRAGStore
from rag.chat import answer_question

question = "How should I store overripe fruit to reduce rot?"

store = ChromaRAGStore()
# Optionally index documents first:
# store.index_documents()

result = answer_question(
    question=question,
    vector_store=store,
    top_k=4,
    extra_context=None,
    vision_payload=None,
)

print(result["answer"])
print("Sources used:", len(result["sources"]))
```

Run:

```bash
python local_rag_chat.py
```

## 3) Building the vector database (Chroma)

By default, the app uses the local persistent store in `.chroma/`.

From code:

```python
from rag.vector_store import ChromaRAGStore

store = ChromaRAGStore()
summary = store.index_documents()
print(summary)
```

## 4) Optional: run ChromaDB with Docker

Start docker-compose:

```bash
docker compose -f docker/docker-compose.yaml up -d
```

Then set env vars (or configure in code) so `ChromaRAGStore` connects to the HTTP host:

- `CHROMA_HOST=localhost` (or your host)
- `CHROMA_PORT=8000`

## Known requirements / notes

- BLIP captioning requires Hugging Face API access + token.
- Groq assistant requires `GROQ_API_KEY`.
- If Chroma DB is empty, retrieval returns no sources; answers will fall back to uncertainty handling.
