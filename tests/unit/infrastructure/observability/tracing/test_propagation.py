from __future__ import annotations

import uuid
from contextlib import contextmanager

from opentelemetry import baggage
from opentelemetry import context as otel_context
from opentelemetry.propagate import get_global_textmap

from quantum.infrastructure.observability.tracing.propagation import (
    baggage_context_from_ids,
    capture_context_snapshot,
    detach_process_baggage_if_any,
    install_process_baggage,
    setup_propagation,
    use_context_snapshot,
    wrap_callable_with_context,
)
from quantum.shared.context.run_id import get_run_id, run_id_context
from quantum.shared.correlation.correlation_id import (
    correlation_context,
    get_correlation_id,
)

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────


def _baggage(key: str) -> str | None:
    try:
        return baggage.get_baggage(key, context=otel_context.get_current())
    except Exception:
        return None


@contextmanager
def _ids_ctx(run_id: str, corr_id: str):
    rc = run_id_context(run_id)
    cc = correlation_context(corr_id)
    rc.__enter__()
    cc.__enter__()
    try:
        yield
    finally:
        cc.__exit__(None, None, None)
        rc.__exit__(None, None, None)


# ──────────────────────────────────────────────────────────────────────────────
# Tests
# ──────────────────────────────────────────────────────────────────────────────


def test_setup_propagation_sets_composite_propagator():
    """
    setup_propagation() doit installer un CompositePropagator (traceparent + baggage).
    """
    setup_propagation()
    prop = get_global_textmap()
    # pas de dépendance forte à la classe interne → on vérifie le nom
    assert "CompositePropagator" in type(prop).__name__


def test_install_and_detach_process_baggage_idempotent():
    """
    - install_process_baggage(run_id, correlation_id) attache les clés dans le baggage courant
    - deuxième appel (sans detach) est NO-OP (garde les valeurs initiales)
    - detach_process_baggage_if_any() retire les clés (retour à l'état précédent)
    """
    detach_process_baggage_if_any()  # nettoie l’état si un autre test l’a posé

    rid1 = str(uuid.uuid4())
    cid1 = str(uuid.uuid4())
    install_process_baggage(run_id=rid1, correlation_id=cid1)

    assert _baggage("run_id") == rid1
    assert _baggage("correlation_id") == cid1

    # Appel idempotent avec d'autres valeurs → ne doit PAS remplacer
    rid2 = str(uuid.uuid4())
    cid2 = str(uuid.uuid4())
    install_process_baggage(run_id=rid2, correlation_id=cid2)

    assert _baggage("run_id") == rid1
    assert _baggage("correlation_id") == cid1

    # Détache → plus de clés
    detach_process_baggage_if_any()
    assert _baggage("run_id") in (None, "")
    assert _baggage("correlation_id") in (None, "")


def test_baggage_context_from_ids_temporarily_sets_keys():
    """
    baggage_context_from_ids() réinjecte run_id/correlation_id provenant des ContextVars
    pendant le bloc, puis restaure l’état.
    """
    rid = str(uuid.uuid4())
    cid = str(uuid.uuid4())

    # avant: s'assure qu'on n’a rien
    detach_process_baggage_if_any()
    assert _baggage("run_id") in (None, "")
    assert _baggage("correlation_id") in (None, "")

    with _ids_ctx(rid, cid):
        # pendant: les ContextVars ont des valeurs → le context manager les propage en baggage
        with baggage_context_from_ids():
            assert _baggage("run_id") == rid
            assert _baggage("correlation_id") == cid
        # après: plus de baggage injecté par ce CM
        assert _baggage("run_id") in (None, "")
        assert _baggage("correlation_id") in (None, "")


def test_capture_and_use_context_snapshot_with_baggage_injection():
    """
    use_context_snapshot(..., attach_otel=False, ensure_baggage_from_ids=True)
    doit:
      - fixer run_id/correlation_id (ContextVars) selon le snapshot
      - injecter ces valeurs dans le baggage le temps du bloc
      - restaurer l’état ensuite
    """
    rid1 = str(uuid.uuid4())
    cid1 = str(uuid.uuid4())
    with _ids_ctx(rid1, cid1):
        snap = capture_context_snapshot()

    # Change le contexte courant pour vérifier que le snapshot prime dans le bloc
    rid2 = str(uuid.uuid4())
    cid2 = str(uuid.uuid4())
    with _ids_ctx(rid2, cid2):
        # avant: le contexte courant ≠ snapshot
        assert get_run_id() == rid2 and get_correlation_id() == cid2
        assert _baggage("run_id") in (None, "")
        assert _baggage("correlation_id") in (None, "")

        # dans le bloc, on s'attend à voir les IDs du snapshot ET le baggage alimenté
        with use_context_snapshot(
            snap, attach_otel=False, ensure_baggage_from_ids=True
        ):
            assert get_run_id() == rid1
            assert get_correlation_id() == cid1
            assert _baggage("run_id") == rid1
            assert _baggage("correlation_id") == cid1

        # après: retour aux valeurs du contexte courant (rid2/cid2) et pas de baggage
        assert get_run_id() == rid2
        assert get_correlation_id() == cid2
        assert _baggage("run_id") in (None, "")
        assert _baggage("correlation_id") in (None, "")


def test_wrap_callable_with_context_runs_under_snapshot():
    """
    wrap_callable_with_context() exécute la fonction sous le snapshot capturé,
    sans polluer le contexte appelant après exécution.
    """
    rid_snap = str(uuid.uuid4())
    cid_snap = str(uuid.uuid4())
    with _ids_ctx(rid_snap, cid_snap):
        from quantum.infrastructure.observability.tracing.propagation import (
            baggage_context_from_ids,
        )

        with baggage_context_from_ids():
            snap = capture_context_snapshot()

    rid_cur = str(uuid.uuid4())
    cid_cur = str(uuid.uuid4())
    with _ids_ctx(rid_cur, cid_cur):
        # callable observant le contexte courant
        def _whoami():
            return (
                get_run_id(),
                get_correlation_id(),
                _baggage("run_id"),
                _baggage("correlation_id"),
            )

        wrapped = wrap_callable_with_context(_whoami, snap=snap)
        r_run_id, r_corr_id, b_rid, b_cid = wrapped()

        # Dans l'exécution, on voit le snapshot
        assert r_run_id == rid_snap and r_corr_id == cid_snap
        # Et le baggage injecté via ensure_baggage_from_ids du wrapper
        # (le wrapper utilise use_context_snapshot avec defaults → ensure_baggage_from_ids=True)
        assert b_rid == rid_snap and b_cid == cid_snap

        # Le contexte appelant est intact après
        assert get_run_id() == rid_cur and get_correlation_id() == cid_cur
        assert _baggage("run_id") in (None, "")
        assert _baggage("correlation_id") in (None, "")
