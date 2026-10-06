"""Tests para la lógica de lease de líder (funciones puras, sin Firebase)."""

import leader


def test_claim_taken_when_no_lease():
    now = 1_000_000
    result = leader.claim(None, now)
    assert result["id"] == leader.INSTANCE_ID
    assert result["expires_at"] == now + leader.LEASE_TTL_MS


def test_claim_denied_when_other_holds_valid_lease():
    now = 1_000_000
    other = {"id": "otra-instancia", "expires_at": now + 30_000}
    result = leader.claim(other, now)
    assert result is other  # sin cambios: no tomamos el lease


def test_claim_taken_when_other_lease_expired():
    now = 1_000_000
    other = {"id": "otra-instancia", "expires_at": now - 1}
    result = leader.claim(other, now)
    assert result["id"] == leader.INSTANCE_ID
    assert result["expires_at"] == now + leader.LEASE_TTL_MS


def test_claim_renews_own_valid_lease():
    now = 1_000_000
    mine = {"id": leader.INSTANCE_ID, "expires_at": now + 10_000}
    result = leader.claim(mine, now)
    assert result["id"] == leader.INSTANCE_ID
    assert result["expires_at"] == now + leader.LEASE_TTL_MS  # extendido


def test_claim_handles_malformed_expiry():
    now = 1_000_000
    other = {"id": "otra", "expires_at": "no-numero"}
    result = leader.claim(other, now)
    assert result["id"] == leader.INSTANCE_ID  # caducado -> tomamos


def test_release_only_if_owner():
    now = 1_000_000
    mine = {"id": leader.INSTANCE_ID, "expires_at": now + 10_000}
    other = {"id": "otra", "expires_at": now + 10_000}

    released = leader.release_claim(mine, now)
    assert released["id"] is None

    kept = leader.release_claim(other, now)
    assert kept is other  # no liberamos lease ajeno

    assert leader.release_claim(None, now)["id"] is None


def test_lease_is_valid():
    now = 1_000_000
    assert leader.lease_is_valid({"id": "x", "expires_at": now + 1}, now)
    assert not leader.lease_is_valid({"id": "x", "expires_at": now - 1}, now)
    assert not leader.lease_is_valid({"id": None, "expires_at": now + 1}, now)
    assert not leader.lease_is_valid(None, now)
    assert not leader.lease_is_valid({}, now)
    assert not leader.lease_is_valid({"id": "x", "expires_at": "bad"}, now)


def test_failover_sequence():
    """Simula: líder muere -> otra instancia toma el lease en el siguiente intento."""
    now = 1_000_000
    # 1. instancia A (ajena) tiene el lease vigente
    a = {"id": "A", "expires_at": now + leader.LEASE_TTL_MS}
    # 2. B intenta antes de que caduque -> denegado
    b_attempt = leader.claim(a, now + 1_000)
    assert b_attempt is a
    # 3. A muere; B reintenta tras TTL -> tomado
    b_attempt = leader.claim(a, now + leader.LEASE_TTL_MS + 1)
    assert b_attempt["id"] == leader.INSTANCE_ID
    assert b_attempt["expires_at"] == now + leader.LEASE_TTL_MS + 1 + leader.LEASE_TTL_MS


def test_suplente_cede_a_principal():
    """Host (prioridad 1) cede si la PC principal (0) está en espera."""
    standbys = {"pc#123": 0}
    assert leader.should_yield_for(standbys, my_priority=1, my_id="host#43")


def test_principal_no_cede_a_suplente():
    """PC (0) NO cede aunque un host suplente (1) esté en espera."""
    standbys = {"host#43": 1}
    assert not leader.should_yield_for(standbys, my_priority=0, my_id="pc#123")


def test_prioridad_igual_no_cede():
    standbys = {"otra#1": 0, "otra#2": 0}
    assert not leader.should_yield_for(standbys, my_priority=0, my_id="yo#1")


def test_standby_propio_ignorado():
    standbys = {"yo#1": 0}
    assert not leader.should_yield_for(standbys, my_priority=1, my_id="yo#1")


def test_key_firebase_sin_caracteres_illegales():
    assert leader._key("Jaume#123-x") == "Jaume_123-x"
    assert leader._key("a964aa65-68a5") == "a964aa65-68a5"
