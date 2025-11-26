import json

from pathlib import Path

import streamlit as st

from quantum.infrastructure.config.runtime.manager import ConfigManager


def render_page() -> None:
    st.title("🔍 Quantum Observability — Core Dashboard")

    st.write("Supervision en temps réel de l’Observability Core.")
    st.divider()

    render_config_section()
    st.divider()

    render_logs_section()
    st.divider()

    render_audit_section()
    st.divider()

    render_metrics_section()
    st.divider()

    render_tracing_section()
    st.divider()


# ---------------------------------------------------------------------------
# CONFIG SNAPSHOT
# ---------------------------------------------------------------------------
def render_config_section() -> None:
    st.subheader("⚙️ Configuration Snapshot (runtime)")

    snapshot = ConfigManager.snapshot()
    st.json(snapshot)


# ---------------------------------------------------------------------------
# LOGS TAIL VIEW
# ---------------------------------------------------------------------------
logging_cfg = ConfigManager.load_logging()


def render_logs_section() -> None:
    st.subheader("🧾 Logs")

    log_dir = Path(logging_cfg.quantum_log_dir)
    if not log_dir.exists():
        st.info("Aucun répertoire de logs trouvé.")
        return

    files = list(log_dir.glob("*.jsonl"))
    if not files:
        st.info("Aucun fichier log .jsonl trouvé.")
        return

    file = st.selectbox("Fichier log :", files, index=0)

    if st.button("Rafraîchir"):
        st.experimental_rerun()

    content = file.read_text().strip().split("\n")[-200:]

    mode = st.radio("Renderer :", ["json", "texte"], index=0)

    if mode == "json":
        for line in content:
            try:
                st.json(json.loads(line))
            except Exception:
                st.code(line)
    else:
        st.code("\n".join(content))


# ---------------------------------------------------------------------------
# AUDIT TAIL VIEW
# ---------------------------------------------------------------------------


def render_audit_section() -> None:
    st.subheader("📑 Audit Events")

    audit_dir = Path(logging_cfg.quantum_audit_dir)
    if not audit_dir.exists():
        st.info("Aucun répertoire d’audit trouvé.")
        return

    files = list(audit_dir.glob("events-*.jsonl"))
    if not files:
        st.info("Aucun audit event trouvé.")
        return

    file = st.selectbox("Fichier audit :", files, index=0)

    content = file.read_text().strip().split("\n")[-200:]

    for line in content:
        try:
            st.json(json.loads(line))
        except Exception:
            st.code(line)


# ---------------------------------------------------------------------------
# METRICS SCRAPER
# ---------------------------------------------------------------------------


def render_metrics_section() -> None:
    import requests

    st.subheader("📊 Metrics (Prometheus format)")

    cfg = ConfigManager.load()
    endpoint = f"http://{cfg.quantum_metrics_host}:{cfg.quantum_metrics_port}/metrics"

    st.write(f"Endpoint : `{endpoint}`")

    try:
        resp = requests.get(endpoint, timeout=1.0)
        resp.raise_for_status()
    except Exception as e:
        st.error(f"Erreur lors de la récupération des métriques : {e}")
        return

    st.code(resp.text)


# ---------------------------------------------------------------------------
# BASIC TRACING VIEW (console exporter / otlp local)
# ---------------------------------------------------------------------------


def render_tracing_section() -> None:
    st.subheader("🕵️ Tracing (last spans)")

    trace_file = Path("tracing/spans.jsonl")  # si tu utilises le console exporter
    if not trace_file.exists():
        st.info("Aucun fichier de spans trouvé.")
        return

    spans = trace_file.read_text().strip().split("\n")[-200:]
    for line in spans:
        try:
            st.json(json.loads(line))
        except Exception:
            st.code(line)
