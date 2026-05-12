"""Streamlit application for agriculture image classification — AgroScan UI.
   Redesigned with 2026 Biopunk Lab aesthetic.
"""

import html
from io import BytesIO
from typing import Optional

from PIL import Image, UnidentifiedImageError
import streamlit as st
from src.blip_caption import CaptionError, caption_image
from src.load_model import load_model
from src.predict import predict_image

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AgroScan · Neural Vision",
    page_icon="⬡",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS — 2026 Biopunk Lab Aesthetic ────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=JetBrains+Mono:wght@300;400;500&family=Outfit:wght@300;400;500&display=swap');

/* ── CSS variables ── */
:root {
    --col-bg:       #080C09;
    --col-surface:  #0E1510;
    --col-panel:    #121A13;
    --col-border:   rgba(74,255,107,0.12);
    --col-border-md:rgba(74,255,107,0.22);
    --col-accent:   #4AFF6B;
    --col-accent-dim:#2BBF46;
    --col-amber:    #F5C842;
    --col-amber-dim:#B8942E;
    --col-text:     #E8F0E9;
    --col-muted:    rgba(232,240,233,0.45);
    --col-hint:     rgba(232,240,233,0.22);
    --font-display: 'Syne', sans-serif;
    --font-mono:    'JetBrains Mono', monospace;
    --font-body:    'Outfit', sans-serif;
}

/* ── Global ── */
html, body, [class*="css"] {
    font-family: var(--font-body);
    background: var(--col-bg) !important;
    color: var(--col-text);
}

.stApp {
    background: var(--col-bg) !important;
}

/* Scanline texture overlay */
.stApp::before {
    content: '';
    position: fixed;
    inset: 0;
    background: repeating-linear-gradient(
        0deg,
        transparent,
        transparent 2px,
        rgba(74,255,107,0.012) 2px,
        rgba(74,255,107,0.012) 4px
    );
    pointer-events: none;
    z-index: 0;
}

/* ── Hide default Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container {
    padding: 0 !important;
    max-width: 820px !important;
    position: relative;
    z-index: 1;
}

/* ── Header ── */
.ns-header {
    background: var(--col-surface);
    border-bottom: 1px solid var(--col-border);
    padding: 0 32px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 64px;
    margin-bottom: 32px;
    position: relative;
    overflow: hidden;
}
.ns-header::before {
    content: '';
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 3px;
    background: var(--col-accent);
    box-shadow: 0 0 12px var(--col-accent);
}
.ns-header::after {
    content: '';
    position: absolute;
    right: -60px; top: -60px;
    width: 200px; height: 200px;
    border-radius: 50%;
    border: 1px solid var(--col-border);
}
.ns-wordmark {
    display: flex;
    align-items: baseline;
    gap: 10px;
}
.ns-logo {
    font-family: var(--font-display);
    font-size: 20px;
    font-weight: 800;
    letter-spacing: -0.5px;
    color: var(--col-text);
}
.ns-logo span {
    color: var(--col-accent);
}
.ns-tagline {
    font-family: var(--font-mono);
    font-size: 9px;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    color: var(--col-muted);
    padding-top: 2px;
}
.ns-pill-group {
    display: flex;
    align-items: center;
    gap: 8px;
}
.ns-pill {
    font-family: var(--font-mono);
    font-size: 9px;
    letter-spacing: 1px;
    text-transform: uppercase;
    padding: 4px 10px;
    border-radius: 2px;
    border: 1px solid var(--col-border-md);
    color: var(--col-accent);
    background: rgba(74,255,107,0.06);
}
.ns-pill.amber {
    border-color: rgba(245,200,66,0.3);
    color: var(--col-amber);
    background: rgba(245,200,66,0.06);
}

/* ── Section label ── */
.ns-label {
    font-family: var(--font-mono);
    font-size: 9px;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    color: var(--col-accent-dim);
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.ns-label::before {
    content: '';
    display: inline-block;
    width: 12px;
    height: 1px;
    background: var(--col-accent-dim);
}

/* ── Panel / card ── */
.ns-panel {
    background: var(--col-panel);
    border: 1px solid var(--col-border);
    border-radius: 4px;
    padding: 20px 22px;
    margin-bottom: 16px;
    position: relative;
}
.ns-panel::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 100%; height: 1px;
    background: linear-gradient(90deg, var(--col-accent) 0%, transparent 60%);
    opacity: 0.4;
}

/* ── File uploader override ── */
[data-testid="stFileUploader"] {
    background: var(--col-panel) !important;
    border: 1px dashed var(--col-border-md) !important;
    border-radius: 4px !important;
    padding: 24px !important;
}
[data-testid="stFileUploader"] label {
    font-family: var(--font-body) !important;
    font-size: 13px !important;
    color: var(--col-muted) !important;
}
[data-testid="stFileUploader"] section {
    border: none !important;
    background: transparent !important;
}
[data-testid="stFileDropzoneInstructions"] {
    color: var(--col-hint) !important;
    font-size: 11px !important;
}
[data-testid="stBaseButton-secondary"] {
    background: rgba(74,255,107,0.08) !important;
    border: 1px solid var(--col-border-md) !important;
    color: var(--col-accent) !important;
    border-radius: 2px !important;
    font-family: var(--font-mono) !important;
    font-size: 11px !important;
    letter-spacing: 1px !important;
}
[data-testid="stBaseButton-secondary"]:hover {
    background: rgba(74,255,107,0.14) !important;
}

/* ── Image display ── */
[data-testid="stImage"] {
    border-radius: 4px;
    overflow: hidden;
    border: 1px solid var(--col-border);
}
[data-testid="stImage"] img {
    border-radius: 4px;
    filter: saturate(0.9) contrast(1.05);
}

/* ── Status idle ── */
.ns-idle {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 16px 18px;
    background: var(--col-panel);
    border: 1px solid var(--col-border);
    border-radius: 4px;
    margin: 16px 0;
}
.ns-idle-icon {
    width: 32px; height: 32px;
    border: 1px solid var(--col-border-md);
    border-radius: 2px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}
.ns-idle-dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: var(--col-accent);
    animation: ns-blink 2s ease-in-out infinite;
}
@keyframes ns-blink {
    0%, 100% { opacity: 0.2; }
    50%       { opacity: 1; box-shadow: 0 0 6px var(--col-accent); }
}
.ns-idle-text {
    font-size: 12px;
    color: var(--col-muted);
    line-height: 1.6;
    margin: 0;
}
.ns-idle-text strong {
    color: var(--col-text);
    font-weight: 500;
}

/* ── Result card ── */
.ns-result {
    background: var(--col-panel);
    border: 1px solid var(--col-border-md);
    border-radius: 4px;
    padding: 22px 24px 20px;
    margin-top: 16px;
    position: relative;
    overflow: hidden;
}
.ns-result::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 100%; height: 2px;
    background: linear-gradient(90deg, var(--col-accent), var(--col-amber), transparent);
}
.ns-result-grid {
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 16px;
    align-items: start;
    margin-bottom: 20px;
}
.ns-result-class {
    font-family: var(--font-display);
    font-size: 30px;
    font-weight: 700;
    color: var(--col-text);
    letter-spacing: -0.5px;
    line-height: 1.1;
    margin-bottom: 4px;
}
.ns-result-sub {
    font-family: var(--font-mono);
    font-size: 10px;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: var(--col-muted);
}
.ns-score-box {
    text-align: right;
}
.ns-score-big {
    font-family: var(--font-mono);
    font-size: 36px;
    font-weight: 500;
    color: var(--col-amber);
    line-height: 1;
    letter-spacing: -1px;
}
.ns-score-unit {
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--col-amber-dim);
    letter-spacing: 1px;
}

/* Progress bar */
.ns-bar-wrap {
    margin-bottom: 20px;
}
.ns-bar-track {
    height: 3px;
    background: rgba(74,255,107,0.1);
    border-radius: 0;
    overflow: hidden;
    position: relative;
}
.ns-bar-fill {
    height: 100%;
    background: linear-gradient(90deg, var(--col-accent-dim), var(--col-accent), var(--col-amber));
    position: relative;
    transition: width 0.8s cubic-bezier(0.16, 1, 0.3, 1);
}
.ns-bar-fill::after {
    content: '';
    position: absolute;
    right: 0; top: -2px;
    width: 6px; height: 7px;
    background: var(--col-amber);
    border-radius: 1px;
}
.ns-bar-legend {
    display: flex;
    justify-content: space-between;
    margin-top: 6px;
}
.ns-bar-legend span {
    font-family: var(--font-mono);
    font-size: 9px;
    color: var(--col-hint);
    letter-spacing: 1px;
}

/* ── Alt chips ── */
.ns-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 4px;
}
.ns-chip {
    font-family: var(--font-mono);
    font-size: 10px;
    padding: 4px 10px;
    border-radius: 2px;
    border: 1px solid var(--col-border);
    color: var(--col-hint);
    letter-spacing: 0.5px;
}
.ns-chip.active {
    border-color: rgba(74,255,107,0.4);
    color: var(--col-accent);
    background: rgba(74,255,107,0.06);
}

/* ── Metric row ── */
.ns-metrics {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 10px;
    margin-top: 20px;
}
.ns-metric {
    background: var(--col-surface);
    border: 1px solid var(--col-border);
    border-radius: 4px;
    padding: 14px 16px;
}
.ns-metric-label {
    font-family: var(--font-mono);
    font-size: 8.5px;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--col-hint);
    margin-bottom: 8px;
}
.ns-metric-val {
    font-family: var(--font-mono);
    font-size: 18px;
    font-weight: 500;
    color: var(--col-text);
    letter-spacing: -0.5px;
}

/* ── Divider ── */
.ns-divider {
    height: 1px;
    background: var(--col-border);
    margin: 24px 0;
    position: relative;
}
.ns-divider::after {
    content: '⬡';
    position: absolute;
    left: 50%; top: 50%;
    transform: translate(-50%, -50%);
    font-size: 10px;
    color: var(--col-border-md);
    background: var(--col-bg);
    padding: 0 8px;
    letter-spacing: 0;
}

/* ── Tabs override ── */
[data-testid="stTabs"] {
    background: transparent;
}
button[data-baseweb="tab"] {
    font-family: var(--font-mono) !important;
    font-size: 10px !important;
    letter-spacing: 1.5px !important;
    text-transform: uppercase !important;
    color: var(--col-muted) !important;
    background: transparent !important;
    border: none !important;
    padding: 12px 20px !important;
    border-bottom: 2px solid transparent !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: var(--col-accent) !important;
    border-bottom-color: var(--col-accent) !important;
}
[data-testid="stTabPanel"] {
    padding: 24px 0 0 !important;
}
[role="tablist"] {
    border-bottom: 1px solid var(--col-border) !important;
    gap: 0 !important;
    background: transparent !important;
}

/* ── Assistant card ── */
.ns-assistant-info {
    background: var(--col-panel);
    border: 1px solid var(--col-border);
    border-left: 2px solid var(--col-accent-dim);
    border-radius: 4px;
    padding: 14px 18px;
    margin-bottom: 20px;
}
.ns-assistant-info p {
    font-size: 12px;
    color: var(--col-muted);
    margin: 0 0 6px;
    line-height: 1.6;
}
.ns-assistant-info span {
    font-family: var(--font-mono);
    font-size: 9px;
    color: var(--col-hint);
    letter-spacing: 1px;
    text-transform: uppercase;
}

/* ── Buttons ── */
[data-testid="stButton"] button {
    background: rgba(74,255,107,0.07) !important;
    border: 1px solid var(--col-border-md) !important;
    color: var(--col-accent) !important;
    border-radius: 2px !important;
    font-family: var(--font-mono) !important;
    font-size: 10px !important;
    letter-spacing: 1.5px !important;
    text-transform: uppercase !important;
    padding: 8px 18px !important;
    transition: background 0.2s, border-color 0.2s !important;
}
[data-testid="stButton"] button:hover {
    background: rgba(74,255,107,0.14) !important;
    border-color: rgba(74,255,107,0.45) !important;
}

/* ── Metric widget ── */
[data-testid="stMetric"] {
    background: var(--col-panel) !important;
    border: 1px solid var(--col-border) !important;
    border-radius: 4px !important;
    padding: 14px 18px !important;
}
[data-testid="stMetricLabel"] {
    font-family: var(--font-mono) !important;
    font-size: 9px !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
    color: var(--col-hint) !important;
}
[data-testid="stMetricValue"] {
    font-family: var(--font-mono) !important;
    font-size: 20px !important;
    color: var(--col-text) !important;
}

/* ── Chat messages ── */
[data-testid="stChatMessage"] {
    background: var(--col-panel) !important;
    border: 1px solid var(--col-border) !important;
    border-radius: 4px !important;
    margin-bottom: 10px !important;
    padding: 14px 18px !important;
}
[data-testid="stChatMessage"][data-testid*="user"] {
    border-left: 2px solid var(--col-accent-dim) !important;
}
[data-testid="stChatMessage"][data-testid*="assistant"] {
    border-left: 2px solid var(--col-amber-dim) !important;
}
[data-testid="stChatInput"] textarea {
    background: var(--col-panel) !important;
    border: 1px solid var(--col-border-md) !important;
    border-radius: 4px !important;
    color: var(--col-text) !important;
    font-family: var(--font-body) !important;
    font-size: 13px !important;
}
[data-testid="stChatInput"] textarea::placeholder {
    color: var(--col-hint) !important;
}

/* ── Alert / error ── */
[data-testid="stAlert"] {
    background: rgba(255,60,60,0.08) !important;
    border: 1px solid rgba(255,60,60,0.2) !important;
    border-radius: 4px !important;
    font-family: var(--font-body) !important;
    font-size: 12px !important;
    color: #FF8A80 !important;
}

/* ── Spinner ── */
[data-testid="stSpinner"] p {
    font-family: var(--font-mono) !important;
    font-size: 11px !important;
    color: var(--col-accent) !important;
    letter-spacing: 1px !important;
    text-transform: uppercase !important;
}

/* ── Expander ── */
[data-testid="stExpander"] {
    background: var(--col-panel) !important;
    border: 1px solid var(--col-border) !important;
    border-radius: 4px !important;
}
[data-testid="stExpander"] summary {
    font-family: var(--font-mono) !important;
    font-size: 10px !important;
    color: var(--col-muted) !important;
    letter-spacing: 1px !important;
    text-transform: uppercase !important;
}

/* ── Source line ── */
.ns-source-line {
    font-family: var(--font-mono);
    font-size: 10px;
    color: var(--col-muted);
    border-bottom: 1px solid var(--col-border);
    padding: 8px 0;
    letter-spacing: 0.5px;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
    background: rgba(74,255,107,0.2);
    border-radius: 0;
}
::-webkit-scrollbar-thumb:hover {
    background: rgba(74,255,107,0.4);
}

/* ── Columns ── */
[data-testid="stColumns"] {
    gap: 12px !important;
}

/* ── Caption ── */
[data-testid="stCaptionContainer"] {
    font-family: var(--font-mono) !important;
    font-size: 10px !important;
    color: var(--col-hint) !important;
    letter-spacing: 0.5px !important;
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


@st.cache_data(show_spinner=False)
def get_cached_blip_caption(image_bytes: bytes) -> str:
    """Generate and cache a BLIP caption for the uploaded image bytes."""
    image = Image.open(BytesIO(image_bytes)).convert("RGB")
    return caption_image(image)


# ── Helper: result card HTML ────────────────────────────────────────────────────
def result_card_html(pct: float, top_classes: list[tuple[str, float]]) -> str:
    """Return the full result card as an HTML string — 2026 Biopunk style."""
    bar_width = min(pct, 100)
    top_label = top_classes[0][0] if top_classes else "—"

    chips_html = "".join(
        f'<span class="ns-chip active">{html.escape(label)} &nbsp;{score:.1f}%</span>'
        if i == 0
        else f'<span class="ns-chip">{html.escape(label)} &nbsp;{score:.1f}%</span>'
        for i, (label, score) in enumerate(top_classes)
    )

    return f"""
    <div class="ns-result">
        <div class="ns-label" style="margin-bottom:16px;">Classification output</div>
        <div class="ns-result-grid">
            <div>
                <div class="ns-result-class">{html.escape(top_label)}</div>
                <div class="ns-result-sub">Identified crop / disease</div>
            </div>
            <div class="ns-score-box">
                <div class="ns-score-big">{pct:.1f}<span style="font-size:18px;">%</span></div>
                <div class="ns-score-unit">Confidence</div>
            </div>
        </div>
        <div class="ns-bar-wrap">
            <div class="ns-bar-track">
                <div class="ns-bar-fill" style="width:{bar_width}%;"></div>
            </div>
            <div class="ns-bar-legend">
                <span>0%</span>
                <span>Confidence threshold</span>
                <span>100%</span>
            </div>
        </div>
        <div class="ns-label" style="margin-bottom:10px;">Top alternatives</div>
        <div class="ns-chips">{chips_html}</div>
    </div>
    """


def _rank_probabilities(prediction: dict, class_names: list[str]) -> list[tuple[str, float]]:
    probabilities = prediction.get("probabilities") or []
    return sorted(
        zip(class_names, probabilities),
        key=lambda item: item[1],
        reverse=True,
    )


def build_vision_payload(
    prediction: dict,
    class_names: list[str],
    caption: str = "",
    caption_error: Optional[str] = None,
) -> dict:
    """Build the structured multimodal payload used by AgroVision AI."""
    ranked = _rank_probabilities(prediction, class_names)
    return {
        "class": prediction.get("class_label", "unknown"),
        "confidence": float(prediction.get("confidence", 0.0)),
        "caption": caption or "",
        "caption_error": caption_error or "",
        "top_probabilities": [
            {"class": label, "confidence": float(prob)} for label, prob in ranked[:3]
        ],
    }


def build_prediction_context(
    prediction: dict,
    class_names: list[str],
    caption: str = "",
    caption_error: Optional[str] = None,
) -> str:
    """Format the latest vision result as optional retrieval context."""
    ranked = _rank_probabilities(prediction, class_names)
    alternatives = ", ".join(f"{label}: {prob * 100:.2f}%" for label, prob in ranked[:3])
    caption_line = caption or f"[BLIP caption unavailable: {caption_error or 'not generated'}]"
    return (
        "Vision Model Output:\n"
        f"- class: {prediction['class_label']}\n"
        f"- confidence: {prediction['confidence']:.4f}\n"
        f"- top probabilities: {alternatives}\n\n"
        "BLIP Image Caption:\n"
        f"{caption_line}"
    )


# ── Header ──────────────────────────────────────────────────────────────────────
def render_header() -> None:
    st.markdown("""
    <div class="ns-header">
        <div class="ns-wordmark">
            <div class="ns-logo">Agro<span>Scan</span></div>
            <div class="ns-tagline">Neural Vision · RAG · Classify</div>
        </div>
        <div class="ns-pill-group">
            <div class="ns-pill">PyTorch</div>
            <div class="ns-pill">ChromaDB</div>
            <div class="ns-pill amber">Groq LLM</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ── Classifier ──────────────────────────────────────────────────────────────────
def render_classifier() -> Optional[dict]:
    st.markdown('<div class="ns-label">Input image</div>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Drop a crop image here — JPG, JPEG or PNG",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=False,
        label_visibility="visible",
    )

    if uploaded_file is None:
        st.markdown("""
        <div class="ns-idle">
            <div class="ns-idle-icon">
                <div class="ns-idle-dot"></div>
            </div>
            <p class="ns-idle-text">
                <strong>System idle.</strong> Upload a crop image to begin neural classification.
                Supported formats: JPG · JPEG · PNG
            </p>
        </div>
        """, unsafe_allow_html=True)
        return None

    image_bytes = uploaded_file.getvalue()
    try:
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
    except UnidentifiedImageError:
        st.error("The uploaded file is not a valid image.")
        return None

    st.markdown(
        '<div class="ns-label" style="margin-top:24px;">Image preview</div>',
        unsafe_allow_html=True,
    )
    st.image(
        image,
        caption=f"{uploaded_file.name}  ·  {image.width} × {image.height} px",
        use_container_width=True,
    )

    try:
        with st.spinner("Running neural scan…"):
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

    caption = ""
    caption_error = None
    try:
        with st.spinner("Generating BLIP caption…"):
            caption = get_cached_blip_caption(image_bytes)
    except CaptionError as error:
        caption_error = str(error)
        st.warning(f"BLIP caption unavailable: {caption_error}")
    except Exception as error:
        caption_error = str(error)
        st.warning(f"BLIP caption failed: {caption_error}")

    confidence_pct = prediction["confidence"] * 100
    top_label = prediction["class_label"]
    top_classes: list[tuple[str, float]] = [(top_label, confidence_pct)]

    st.session_state["last_vision_payload"] = build_vision_payload(
        prediction,
        class_names,
        caption=caption,
        caption_error=caption_error,
    )
    st.session_state["last_prediction_context"] = build_prediction_context(
        prediction,
        class_names,
        caption=caption,
        caption_error=caption_error,
    )

    st.markdown(result_card_html(confidence_pct, top_classes), unsafe_allow_html=True)
    if caption:
        st.caption(f"BLIP caption: {caption}")

    st.markdown('<div class="ns-divider"></div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="ns-metrics">
        <div class="ns-metric">
            <div class="ns-metric-label">Predicted class</div>
            <div class="ns-metric-val" style="font-size:13px; font-family:var(--font-body); letter-spacing:0;">
                {html.escape(top_label)}
            </div>
        </div>
        <div class="ns-metric">
            <div class="ns-metric-label">Confidence</div>
            <div class="ns-metric-val">{confidence_pct:.2f}%</div>
        </div>
        <div class="ns-metric">
            <div class="ns-metric-label">Classes known</div>
            <div class="ns-metric-val">{len(class_names)}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    return prediction


# ── Sources ──────────────────────────────────────────────────────────────────────
def _render_sources(sources: list[dict]) -> None:
    if not sources:
        st.caption("No source chunks retrieved from the vector database.")
        return

    with st.expander("Retrieved sources", expanded=False):
        for source in sources:
            page = source.get("page")
            page_label = "" if page in (None, -1, "-1") else f" · page {page}"
            st.markdown(
                "<div class='ns-source-line'>"
                f"{html.escape(str(source.get('filename', 'unknown')))}"
                f"{html.escape(page_label)} &nbsp;·&nbsp; score {float(source.get('score', 0.0)):.3f}"
                "</div>",
                unsafe_allow_html=True,
            )
            st.caption((source.get("text") or "")[:350])


# ── Assistant ─────────────────────────────────────────────────────────────────────
def render_assistant() -> None:
    st.markdown('<div class="ns-label">RAG assistant</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="ns-assistant-info">
        <p>Ask questions about Moroccan agriculture, fruit production, policies, or the last scanned image.</p>
        <span>BLIP · ChromaDB · SentenceTransformers · Groq JSON</span>
    </div>
    """, unsafe_allow_html=True)

    try:
        vector_store = get_cached_vector_store()
    except Exception as error:
        st.error(f"RAG initialization failed: {error}")
        return

    index_col, count_col = st.columns([1.6, 1])
    with index_col:
        if st.button("Build / refresh knowledge base", use_container_width=True):
            try:
                with st.spinner("Indexing documents…"):
                    summary = vector_store.index_documents()
                if summary["errors"]:
                    st.warning(
                        f"Indexed {summary['chunks_indexed']} chunks — "
                        f"{len(summary['errors'])} file(s) had errors."
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

    user_question = st.chat_input("Ask AgroScan Assistant…")
    if not user_question:
        return

    st.session_state["rag_messages"].append({"role": "user", "content": user_question})
    with st.chat_message("user"):
        st.markdown(user_question)

    try:
        from rag.chat import answer_question

        vision_payload = st.session_state.get("last_vision_payload")
        extra_context = None if vision_payload else st.session_state.get("last_prediction_context")
        with st.chat_message("assistant"):
            with st.spinner("Retrieving context · querying Groq…"):
                result = answer_question(
                    question=user_question,
                    vector_store=vector_store,
                    top_k=4,
                    extra_context=extra_context,
                    vision_payload=vision_payload,
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


# ── Main ─────────────────────────────────────────────────────────────────────────
def main() -> None:
    render_header()
    vision_tab, assistant_tab = st.tabs(["⬡  Crop Vision", "◈  AI Assistant"])
    with vision_tab:
        render_classifier()
    with assistant_tab:
        render_assistant()


if __name__ == "__main__":
    main()
