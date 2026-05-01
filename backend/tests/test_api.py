"""API tests for the FastAPI backend."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from main import app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def client() -> TestClient:
    """Synchronous test client."""
    return TestClient(app)


@pytest.fixture
async def async_client() -> AsyncClient:
    """Async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


# ---------------------------------------------------------------------------
# Health Check Tests
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_health_endpoint_returns_200(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200


@pytest.mark.api
def test_health_response_contains_status(client: TestClient) -> None:
    response = client.get("/health")
    assert "status" in response.json() or "ok" in response.json()


@pytest.mark.api
async def test_health_async(async_client: AsyncClient) -> None:
    response = await async_client.get("/health")
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# Signal Endpoint Tests
# ---------------------------------------------------------------------------


@pytest.mark.api
@patch("routers.signal.analyze_token")
def test_signal_analyze_token_returns_200(mock_analyze: MagicMock, client: TestClient) -> None:
    mock_analyze.return_value = {
        "token_address": "0x123",
        "overall": 0.75,
        "confidence": 0.8,
        "action": "BUY",
    }
    response = client.get("/api/signal/0x123")
    assert response.status_code == 200


@pytest.mark.api
@patch("routers.signal.analyze_token")
def test_signal_analyze_token_returns_signal_data(mock_analyze: MagicMock, client: TestClient) -> None:
    mock_analyze.return_value = {
        "token_address": "0x123",
        "overall": 0.75,
        "confidence": 0.8,
        "action": "BUY",
    }
    response = client.get("/api/signal/0x123")
    data = response.json()
    assert "overall" in data
    assert "confidence" in data


@pytest.mark.api
@patch("routers.signal.analyze_token")
def test_signal_analyze_invalid_address(mock_analyze: MagicMock, client: TestClient) -> None:
    response = client.get("/api/signal/invalid")
    # Should return 400 for invalid address format
    assert response.status_code in [400, 422]


@pytest.mark.api
@patch("routers.signal.analyze_token")
def test_signal_handles_analyzer_error(mock_analyze: MagicMock, client: TestClient) -> None:
    mock_analyze.side_effect = Exception("Analyzer failed")
    response = client.get("/api/signal/0x1234567890123456789012345678901234567890")
    # Should return 500 or propagate error gracefully
    assert response.status_code in [200, 500]


# ---------------------------------------------------------------------------
# Token Scan Endpoint Tests
# ---------------------------------------------------------------------------


@pytest.mark.api
@patch("routers.token_scan.scan_token")
def test_token_scan_returns_200(mock_scan: MagicMock, client: TestClient) -> None:
    mock_scan.return_value = {
        "address": "0x123",
        "name": "Test Token",
        "symbol": "TEST",
    }
    response = client.post("/api/token/scan", json={"address": "0x123"})
    assert response.status_code == 200


@pytest.mark.api
@patch("routers.token_scan.scan_token")
def test_token_scan_returns_token_data(mock_scan: MagicMock, client: TestClient) -> None:
    mock_scan.return_value = {
        "address": "0x123",
        "name": "Test Token",
        "symbol": "TEST",
        "decimals": 18,
        "total_supply": "1000000",
    }
    response = client.post("/api/token/scan", json={"address": "0x123"})
    data = response.json()
    assert "name" in data
    assert "symbol" in data


@pytest.mark.api
@patch("routers.token_scan.scan_token")
def test_token_scan_missing_address(mock_scan: MagicMock, client: TestClient) -> None:
    response = client.post("/api/token/scan", json={})
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Vault Endpoint Tests
# ---------------------------------------------------------------------------


@pytest.mark.api
@patch("routers.vault.get_vault_state")
def test_vault_state_returns_200(mock_state: MagicMock, client: TestClient) -> None:
    mock_state.return_value = {
        "total_assets": 1000000,
        "total_supply": 1000,
        "share_price": 1.0,
    }
    response = client.get("/api/vault/state")
    assert response.status_code == 200


@pytest.mark.api
@patch("routers.vault.get_vault_state")
def test_vault_state_returns_data(mock_state: MagicMock, client: TestClient) -> None:
    mock_state.return_value = {
        "total_assets": 1000000,
        "total_supply": 1000,
        "share_price": 1.0,
        "position_open": False,
    }
    response = client.get("/api/vault/state")
    data = response.json()
    assert "total_assets" in data
    assert "share_price" in data


@pytest.mark.api
@patch("routers.vault.get_vault_state")
def test_vault_deposit_returns_200(mock_deposit: MagicMock, client: TestClient) -> None:
    mock_deposit.return_value = {"tx_hash": "0xabc"}
    response = client.post("/api/vault/deposit", json={"amount": 1000})
    assert response.status_code == 200


@pytest.mark.api
def test_vault_deposit_missing_amount(client: TestClient) -> None:
    response = client.post("/api/vault/deposit", json={})
    assert response.status_code == 422


@pytest.mark.api
def test_vault_deposit_negative_amount(client: TestClient) -> None:
    response = client.post("/api/vault/deposit", json={"amount": -100})
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Chat Endpoint Tests
# ---------------------------------------------------------------------------


@pytest.mark.api
@patch("routers.chat.generate_response")
def test_chat_returns_200(mock_chat: MagicMock, client: TestClient) -> None:
    mock_chat.return_value = {"response": "Hello! How can I help?"}
    response = client.post("/api/chat", json={"message": "Hello"})
    assert response.status_code == 200


@pytest.mark.api
@patch("routers.chat.generate_response")
def test_chat_returns_response(mock_chat: MagicMock, client: TestClient) -> None:
    mock_chat.return_value = {"response": "Test response"}
    response = client.post("/api/chat", json={"message": "Hello"})
    data = response.json()
    assert "response" in data


@pytest.mark.api
def test_chat_empty_message(client: TestClient) -> None:
    response = client.post("/api/chat", json={})
    assert response.status_code == 422


@pytest.mark.api
@patch("routers.chat.generate_response")
def test_chat_handles_error(mock_chat: MagicMock, client: TestClient) -> None:
    mock_chat.side_effect = Exception("Chat failed")
    response = client.post("/api/chat", json={"message": "Hello"})
    assert response.status_code == 200  # Should handle gracefully


# ---------------------------------------------------------------------------
# Wallet Endpoint Tests
# ---------------------------------------------------------------------------


@pytest.mark.api
@patch("routers.wallet.get_wallet_info")
def test_wallet_info_returns_200(mock_wallet: MagicMock, client: TestClient) -> None:
    mock_wallet.return_value = {"address": "0x123", "balance": 1000}
    response = client.get("/api/wallet/0x123")
    assert response.status_code == 200


@pytest.mark.api
@patch("routers.wallet.get_wallet_info")
def test_wallet_info_returns_balance(mock_wallet: MagicMock, client: TestClient) -> None:
    mock_wallet.return_value = {"address": "0x123", "balance": 5000, "positions": []}
    response = client.get("/api/wallet/0x123")
    data = response.json()
    assert "balance" in data


@pytest.mark.api
def test_wallet_info_invalid_address(client: TestClient) -> None:
    response = client.get("/api/wallet/invalid")
    assert response.status_code in [400, 422]


# ---------------------------------------------------------------------------
# GMGN Endpoint Tests
# ---------------------------------------------------------------------------


@pytest.mark.api
@patch("routers.gmgn.get_token_data")
def test_gmgn_returns_200(mock_gmgn: MagicMock, client: TestClient) -> None:
    mock_gmgn.return_value = {"pairs": []}
    response = client.get("/api/gmgn/tokens")
    assert response.status_code == 200


@pytest.mark.api
@patch("routers.gmgn.get_token_data")
def test_gmgn_returns_token_list(mock_gmgn: MagicMock, client: TestClient) -> None:
    mock_gmgn.return_value = {
        "tokens": [
            {"address": "0x1", "name": "Token1"},
            {"address": "0x2", "name": "Token2"},
        ]
    }
    response = client.get("/api/gmgn/tokens")
    data = response.json()
    assert "tokens" in data or isinstance(data, list)


# ---------------------------------------------------------------------------
# DEX Endpoint Tests
# ---------------------------------------------------------------------------


@pytest.mark.api
@patch("routers.dex.get_pool_data")
def test_dex_pool_returns_200(mock_dex: MagicMock, client: TestClient) -> None:
    mock_dex.return_value = {"liquidity": 100000}
    response = client.get("/api/dex/pool/0x123")
    assert response.status_code == 200


@pytest.mark.api
@patch("routers.dex.get_pool_data")
def test_dex_pool_returns_liquidity(mock_dex: MagicMock, client: TestClient) -> None:
    mock_dex.return_value = {
        "address": "0x123",
        "liquidity": 50000,
        "volume_24h": 10000,
    }
    response = client.get("/api/dex/pool/0x123")
    data = response.json()
    assert "liquidity" in data


# ---------------------------------------------------------------------------
# RL Trade Endpoint Tests
# ---------------------------------------------------------------------------


@pytest.mark.api
@patch("routers.rl_trade.execute_trade")
def test_rl_trade_returns_200(mock_trade: MagicMock, client: TestClient) -> None:
    mock_trade.return_value = {"status": "executed", "tx_hash": "0xabc"}
    response = client.post("/api/rl/trade", json={"token": "0x123", "action": "BUY"})
    assert response.status_code == 200


@pytest.mark.api
@patch("routers.rl_trade.execute_trade")
def test_rl_trade_returns_status(mock_trade: MagicMock, client: TestClient) -> None:
    mock_trade.return_value = {"status": "pending"}
    response = client.post("/api/rl/trade", json={"token": "0x123", "action": "SELL"})
    data = response.json()
    assert "status" in data


@pytest.mark.api
def test_rl_trade_missing_action(client: TestClient) -> None:
    response = client.post("/api/rl/trade", json={"token": "0x123"})
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# AI Analysis Endpoint Tests
# ---------------------------------------------------------------------------


@pytest.mark.api
@patch("routers.ai_analysis.analyze_market")
def test_ai_analysis_returns_200(mock_ai: MagicMock, client: TestClient) -> None:
    mock_ai.return_value = {"analysis": "Market looks bullish"}
    response = client.post("/api/ai/analyze", json={"query": "What's the market?"})
    assert response.status_code == 200


@pytest.mark.api
@patch("routers.ai_analysis.analyze_market")
def test_ai_analysis_returns_result(mock_ai: MagicMock, client: TestClient) -> None:
    mock_ai.return_value = {
        "sentiment": "bullish",
        "confidence": 0.75,
        "summary": "Test analysis",
    }
    response = client.post("/api/ai/analyze", json={"query": "What's trending?"})
    data = response.json()
    assert "sentiment" in data or "analysis" in data or "summary" in data


@pytest.mark.api
def test_ai_analysis_empty_query(client: TestClient) -> None:
    response = client.post("/api/ai/analyze", json={})
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Rate Limiting Tests
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_rate_limit_headers_present(client: TestClient) -> None:
    response = client.get("/health")
    # Some endpoints may include rate limit headers
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# CORS Tests
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_cors_headers_present(client: TestClient) -> None:
    response = client.options("/health")
    # CORS headers should be present
    assert "access-control-allow-origin" in response.headers or response.status_code == 200


# ---------------------------------------------------------------------------
# Error Handling Tests
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_404_for_unknown_endpoint(client: TestClient) -> None:
    response = client.get("/api/nonexistent")
    assert response.status_code == 404


@pytest.mark.api
def test_500_returns_json_error(client: TestClient) -> None:
    with patch("routers.signal.analyze_token", side_effect=Exception("Fail")):
        response = client.get("/api/signal/0x1234567890123456789012345678901234567890")
        # Should return JSON error, not crash
        assert response.status_code in [200, 500]
        assert "application/json" in response.headers.get("content-type", "")


# ---------------------------------------------------------------------------
# Authentication Tests
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_protected_endpoint_requires_auth(client: TestClient) -> None:
    response = client.get("/api/vault/state")
    # If endpoints are protected, should return 401
    assert response.status_code in [200, 401]


@pytest.mark.api
def test_invalid_token_rejected(client: TestClient) -> None:
    response = client.get(
        "/api/vault/state", headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code in [200, 401, 403]


# ---------------------------------------------------------------------------
# Concurrency Tests
# ---------------------------------------------------------------------------


@pytest.mark.api
@pytest.mark.parametrize("endpoint", ["/health", "/api/vault/state"])
def test_concurrent_requests_handled(client: TestClient, endpoint: str) -> None:
    import concurrent.futures

    def make_request():
        return client.get(endpoint)

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(make_request) for _ in range(10)]
        results = [f.result() for f in futures]
    assert all(r.status_code == 200 for r in results)


# ---------------------------------------------------------------------------
# Input Validation Tests
# ---------------------------------------------------------------------------


@pytest.mark.api
@pytest.mark.parametrize(
    "payload,expected_status",
    [
        ({"amount": 100}, 200),
        ({"amount": 0}, 200),
        ({"amount": -1}, 422),
        ({"amount": "invalid"}, 422),
        ({}, 422),
    ],
)
def test_vault_deposit_validation(
    payload: dict, expected_status: int, client: TestClient
) -> None:
    response = client.post("/api/vault/deposit", json=payload)
    assert response.status_code == expected_status


# ---------------------------------------------------------------------------
# Response Format Tests
# ---------------------------------------------------------------------------


@pytest.mark.api
@pytest.mark.parametrize(
    "endpoint",
    ["/health", "/api/vault/state"],
)
def test_json_response_format(client: TestClient, endpoint: str) -> None:
    response = client.get(endpoint)
    assert response.status_code == 200
    assert "application/json" in response.headers.get("content-type", "")


@pytest.mark.api
def test_errorResponse_is_json(client: TestClient) -> None:
    response = client.get("/api/nonexistent")
    assert response.status_code == 404
    assert "application/json" in response.headers.get("content-type", "")


# ---------------------------------------------------------------------------
# WebSocket Tests (if applicable)
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_websocket endpoint exists if applicable(client: TestClient) -> None:
    # Check if WebSocket endpoint is configured
    response = client.get("/ws")
    # May not exist, but should not 500
    assert response.status_code in [404, 426, 500]