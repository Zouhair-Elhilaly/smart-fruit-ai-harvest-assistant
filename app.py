"""Streamlit application for agriculture image classification — AgroScan UI."""

import html
from typing import Optional

from PIL import Image, UnidentifiedImageError
import streamlit as st
from src.load_model import load_model
from src.predict import predict_image

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AgroScan · Crop Vision",
    page_icon="🌿",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600&family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500&display=swap');

/* ── Global reset ── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

.stApp {
    background: #F0EBE0;
}

/* ── Hide default Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container {
    padding: 0 !important;
    max-width: 780px !important;
}

/* ── Header banner ── */
.ag-header {
    background: #2D5016;
    padding: 22px 32px 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-radius: 0 0 18px 18px;
    margin-bottom: 28px;
    position: relative;
    overflow: hidden;
}
.ag-header::before {
    content: '';
    position: absolute;
    right: -30px; top: -40px;
    width: 200px; height: 200px;
    border-radius: 50%;
    border: 1px solid rgba(139,175,114,0.18);
    pointer-events: none;
}
.ag-header::after {
    content: '';
    position: absolute;
    right: 40px; top: -60px;
    width: 130px; height: 130px;
    border-radius: 50%;
    border: 1px solid rgba(139,175,114,0.1);
    pointer-events: none;
}
.ag-logo-text {
    font-family: 'Playfair Display', serif;
    font-size: 24px;
    font-weight: 600;
    color: #E8F5DA;
    letter-spacing: -0.4px;
    line-height: 1.15;
}
.ag-logo-sub {
    font-size: 10px;
    font-weight: 300;
    color: rgba(232,245,218,0.55);
    letter-spacing: 2.5px;
    text-transform: uppercase;
    margin-top: 2px;
}
.ag-badge {
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    background: rgba(196,152,42,0.18);
    color: #E8C96A;
    border: 1px solid rgba(196,152,42,0.35);
    padding: 5px 12px;
    border-radius: 20px;
    letter-spacing: 0.4px;
    position: relative;
    z-index: 1;
}

/* ── Section headings ── */
.ag-section-label {
    font-size: 9.5px;
    font-weight: 500;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #4A7C2E;
    margin-bottom: 10px;
    margin-top: 4px;
}

/* ── Upload zone ── */
.ag-upload-hint {
    background: #fff;
    border-radius: 12px;
    border: 0.5px solid rgba(74,124,46,0.18);
    padding: 14px 18px 12px;
    margin-bottom: 8px;
}
.ag-upload-hint p {
    font-size: 13px;
    color: #4A7C2E;
    margin: 0 0 4px;
}
.ag-upload-hint span {
    font-size: 11px;
    color: rgba(45,80,22,0.5);
    font-family: 'DM Mono', monospace;
}

/* ── File uploader override ── */
[data-testid="stFileUploader"] {
    background: #fff;
    border-radius: 12px;
    border: 1.5px dashed rgba(74,124,46,0.32) !important;
    padding: 20px;
}
[data-testid="stFileUploader"] label {
    font-family: 'DM Sans', sans-serif;
    font-size: 13px;
    color: #4A7C2E !important;
}
[data-testid="stFileUploader"] section {
    border: none !important;
}
[data-testid="stFileDropzoneInstructions"] {
    color: rgba(45,80,22,0.6) !important;
    font-size: 12px !important;
}

/* ── Image display ── */
[data-testid="stImage"] {
    border-radius: 10px;
    overflow: hidden;
    border: 0.5px solid rgba(74,124,46,0.15);
}
[data-testid="stImage"] img {
    border-radius: 10px;
}

/* ── Info / Status box ── */
.ag-status {
    background: #fff;
    border-radius: 10px;
    border: 0.5px solid rgba(74,124,46,0.18);
    padding: 12px 16px;
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 12px 0;
}
.ag-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: #7BAD52;
    flex-shrink: 0;
    animation: ag-pulse 1.6s ease-in-out infinite;
}
@keyframes ag-pulse {
    0%, 100% { opacity: 0.3; transform: scale(0.8); }
    50%       { opacity: 1;   transform: scale(1.1); }
}
.ag-status p {
    font-size: 12px;
    color: #4A7C2E;
    margin: 0;
}

/* ── Result card (dark) ── */
.ag-result-card {
    background: #2D5016;
    border-radius: 14px;
    padding: 20px 22px 18px;
    margin-top: 12px;
    color: #E8F5DA;
}
.ag-result-card .ag-section-label {
    color: rgba(232,245,218,0.45);
    margin-bottom: 14px;
}
.ag-result-class {
    font-family: 'Playfair Display', serif;
    font-size: 28px;
    font-weight: 600;
    color: #E8F5DA;
    line-height: 1.15;
    margin-bottom: 4px;
}
.ag-result-sci {
    font-size: 12px;
    color: #8FAF72;
    font-style: italic;
    margin-bottom: 20px;
}
.ag-confidence-row {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 8px;
}
.ag-confidence-label-txt {
    font-size: 10px;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: rgba(232,245,218,0.45);
}
.ag-confidence-pct {
    font-family: 'DM Mono', monospace;
    font-size: 20px;
    font-weight: 500;
    color: #E8C96A;
}
.ag-bar-track {
    background: rgba(255,255,255,0.1);
    border-radius: 20px;
    height: 8px;
    overflow: hidden;
    margin-bottom: 18px;
}
.ag-bar-fill {
    height: 100%;
    border-radius: 20px;
    background: linear-gradient(90deg, #7BAD52, #E8C96A);
    position: relative;
    transition: width 0.6s ease;
}

/* ── Metric cards row ── */
.ag-metrics-row {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 10px;
    margin-top: 24px;
}
.ag-metric-mini {
    background: #fff;
    border-radius: 10px;
    border: 0.5px solid rgba(74,124,46,0.14);
    padding: 12px 14px;
}
.ag-metric-mini-label {
    font-size: 9px;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: rgba(45,80,22,0.4);
    margin-bottom: 5px;
}
.ag-metric-mini-val {
    font-family: 'DM Mono', monospace;
    font-size: 17px;
    font-weight: 500;
    color: #2D5016;
}

/* ── Alternative chips ── */
.ag-chips-row {
    display: flex;
    flex-wrap: wrap;
    gap: 7px;
    margin-top: 4px;
}
.ag-chip {
    font-size: 11px;
    padding: 4px 11px;
    border-radius: 20px;
    border: 0.5px solid rgba(232,245,218,0.18);
    color: rgba(232,245,218,0.55);
    font-family: 'DM Sans', sans-serif;
    white-space: nowrap;
}
.ag-chip-active {
    background: rgba(123,173,82,0.22);
    border-color: rgba(123,173,82,0.5);
    color: #D4EBB8;
}

/* ── Error / warning box override ── */
[data-testid="stAlert"] {
    border-radius: 10px;
    font-size: 13px;
    font-family: 'DM Sans', sans-serif;
}

/* ── Spinner text ── */
[data-testid="stSpinner"] p {
    font-family: 'DM Sans', sans-serif;
    color: #4A7C2E !important;
    font-size: 13px;
}

/* ── Divider ── */
.ag-divider {
    height: 0.5px;
    background: rgba(74,124,46,0.12);
    margin: 20px 0;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(74,124,46,0.25); border-radius: 10px; }

/* ── Assistant ── */
.ag-assistant-card {
    background: #fff;
    border-radius: 12px;
    border: 0.5px solid rgba(74,124,46,0.18);
    padding: 16px 18px;
    margin: 8px 0 14px;
}
.ag-assistant-card p {
    font-size: 13px;
    color: #315A1E;
    margin: 0 0 4px;
}
.ag-assistant-card span {
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    color: rgba(45,80,22,0.48);
    letter-spacing: 0.4px;
}
.ag-source-line {
    font-size: 12px;
    color: rgba(45,80,22,0.72);
    border-bottom: 0.5px solid rgba(74,124,46,0.10);
    padding: 7px 0;
}
</style>
""", unsafe_allow_html=True)


# ── Model loader ────────────────────────────────────────────────────────────────
@st.cache_resource
def get_cached_model():
    """Load the model once and reuse it across Streamlit reruns."""
    return load_model()


@st.cache_resource
def get_cached_vector_store():
    """Create the Chroma-backed RAG store once per Streamlit process."""
    from rag.vector_store import ChromaRAGStore

    return ChromaRAGStore()


# ── Helper: confidence bar HTML ────────────────────────────────────────────────
def confidence_bar_html(pct: float, top_classes: list[tuple[str, float]]) -> str:
    """Return the full result card as an HTML string."""
    bar_width = min(pct, 100)
    chips_html = "".join(
        f'<span class="ag-chip ag-chip-active">{html.escape(label)} · {score:.1f}%</span>'
        if i == 0
        else f'<span class="ag-chip">{html.escape(label)} · {score:.1f}%</span>'
        for i, (label, score) in enumerate(top_classes)
    )
    return f"""
    <div class="ag-result-card">
        <div class="ag-section-label">Prediction result</div>
        <div class="ag-result-class">{html.escape(top_classes[0][0]) if top_classes else '—'}</div>
        <div class="ag-result-sci">Confidence · {pct:.2f}%</div>
        <div class="ag-confidence-row">
            <span class="ag-confidence-label-txt">Confidence score</span>
            <span class="ag-confidence-pct">{pct:.2f}%</span>
        </div>
        <div class="ag-bar-track">
            <div class="ag-bar-fill" style="width:{bar_width}%;"></div>
        </div>
        <div class="ag-section-label">Top alternatives</div>
        <div class="ag-chips-row">{chips_html}</div>
    </div>
    """


def build_prediction_context(prediction: dict, class_names: list[str]) -> str:
    """Format the latest vision result as optional context for the assistant."""
    probabilities = prediction.get("probabilities") or []
    ranked = sorted(
        zip(class_names, probabilities),
        key=lambda item: item[1],
        reverse=True,
    )
    alternatives = ", ".join(f"{label}: {prob * 100:.2f}%" for label, prob in ranked[:3])
    return (
        f"The current uploaded image was classified as '{prediction['class_label']}' "
        f"with {prediction['confidence'] * 100:.2f}% confidence. "
        f"Top probabilities: {alternatives}."
    )


def render_header() -> None:
    """Render the fixed app header."""
    st.markdown("""
    <div class="ag-header">
        <div>
            <div class="ag-logo-text">AgroScan</div>
            <div class="ag-logo-sub">Vision · Classify · Ask</div>
        </div>
        <div class="ag-badge">PyTorch · RAG · Groq</div>
    </div>
    """, unsafe_allow_html=True)


def render_classifier() -> Optional[dict]:
    """Render the image classification workflow and return the latest prediction."""
    st.markdown('<div class="ag-section-label">Input image</div>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Drop a crop image here, or click to browse",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=False,
        label_visibility="visible",
    )

    if uploaded_file is None:
        st.markdown("""
        <div class="ag-status">
            <div class="ag-dot"></div>
            <p>Awaiting image — upload a JPG, JPEG or PNG to begin classification.</p>
        </div>
        """, unsafe_allow_html=True)
        return None

    try:
        image = Image.open(uploaded_file).convert("RGB")
    except UnidentifiedImageError:
        st.error("The uploaded file is not a valid image.")
        return None

    st.markdown('<div class="ag-section-label" style="margin-top:18px;">Preview</div>',
                unsafe_allow_html=True)
    st.image(image, caption=f"{uploaded_file.name}  ·  {image.width} × {image.height} px",
             use_container_width=True)

    try:
        with st.spinner("Running AgroScan model…"):
            model, class_names, device = get_cached_model()
            prediction = predict_image(
                image=image,
                model=model,
                class_names=class_names,
                device=device,
            )
    except FileNotFoundError as error:
        st.error(str(error))
        return None
    except Exception as error:
        st.error(f"Prediction failed: {error}")
        return None

    confidence_pct = prediction["confidence"] * 100
    top_label = prediction["class_label"]
    top_classes: list[tuple[str, float]] = [(top_label, confidence_pct)]

    st.session_state["last_prediction_context"] = build_prediction_context(prediction, class_names)

    st.markdown(confidence_bar_html(confidence_pct, top_classes), unsafe_allow_html=True)
    st.markdown('<div class="ag-divider"></div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="ag-metrics-row">
        <div class="ag-metric-mini">
            <div class="ag-metric-mini-label">Predicted class</div>
            <div class="ag-metric-mini-val" style="font-size:13px; font-family:'DM Sans',sans-serif;">
                {html.escape(top_label)}
            </div>
        </div>
        <div class="ag-metric-mini">
            <div class="ag-metric-mini-label">Confidence</div>
            <div class="ag-metric-mini-val">{confidence_pct:.2f}%</div>
        </div>
        <div class="ag-metric-mini">
            <div class="ag-metric-mini-label">Classes known</div>
            <div class="ag-metric-mini-val">{len(class_names)}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    return prediction


def _render_sources(sources: list[dict]) -> None:
    """Render source snippets returned by the retriever."""
    if not sources:
        st.caption("No source chunks were retrieved from the vector database.")
        return

    with st.expander("Retrieved sources", expanded=False):
        for source in sources:
            page = source.get("page")
            page_label = "" if page in (None, -1, "-1") else f" · page {page}"
            st.markdown(
                "<div class='ag-source-line'>"
                f"{html.escape(str(source.get('filename', 'unknown')))}"
                f"{html.escape(page_label)} · score {float(source.get('score', 0.0)):.3f}"
                "</div>",
                unsafe_allow_html=True,
            )
            st.caption((source.get("text") or "")[:350])


def render_assistant() -> None:
    """Render the RAG chat assistant."""
    st.markdown('<div class="ag-section-label">AI assistant</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="ag-assistant-card">
        <p>Ask questions about Moroccan agriculture, fruit production, policies, or the latest image result.</p>
        <span>ChromaDB retrieval · SentenceTransformers embeddings · Groq LLM</span>
    </div>
    """, unsafe_allow_html=True)

    try:
        vector_store = get_cached_vector_store()
    except Exception as error:
        st.error(f"RAG initialization failed: {error}")
        return

    index_col, count_col = st.columns([1.4, 1])
    with index_col:
        if st.button("Build / refresh knowledge base", use_container_width=True):
            try:
                with st.spinner("Indexing documents into ChromaDB…"):
                    summary = vector_store.index_documents()
                if summary["errors"]:
                    st.warning(
                        f"Indexed {summary['chunks_indexed']} chunks, "
                        f"but {len(summary['errors'])} file(s) raised errors."
                    )
                else:
                    st.success(
                        f"Indexed {summary['chunks_indexed']} chunks from "
                        f"{summary['files_indexed']} file(s)."
                    )
            except Exception as error:
                st.error(f"Indexing failed: {error}")
    with count_col:
        st.metric("Knowledge chunks", vector_store.count())

    if "rag_messages" not in st.session_state:
        st.session_state["rag_messages"] = []

    for message in st.session_state["rag_messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant":
                _render_sources(message.get("sources", []))

    user_question = st.chat_input("Ask AgroScan Assistant")
    if not user_question:
        return

    st.session_state["rag_messages"].append({"role": "user", "content": user_question})
    with st.chat_message("user"):
        st.markdown(user_question)

    try:
        from rag.chat import answer_question

        extra_context = st.session_state.get("last_prediction_context")
        with st.chat_message("assistant"):
            with st.spinner("Retrieving context and asking Groq…"):
                result = answer_question(
                    question=user_question,
                    vector_store=vector_store,
                    top_k=4,
                    extra_context=extra_context,
                )
            st.markdown(result["answer"])
            _render_sources(result.get("sources", []))

        st.session_state["rag_messages"].append(
            {
                "role": "assistant",
                "content": result["answer"],
                "sources": result.get("sources", []),
            }
        )
    except Exception as error:
        st.error(f"Assistant failed: {error}")


# ── Main ────────────────────────────────────────────────────────────────────────
def main() -> None:
    render_header()

    vision_tab, assistant_tab = st.tabs(["Crop Vision", "AI Assistant"])
    with vision_tab:
        render_classifier()
    with assistant_tab:
        render_assistant()


if __name__ == "__main__":
    main()
