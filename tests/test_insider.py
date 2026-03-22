from nse_corporate_data.insider import (
    INSIDER_PRESETS,
    BUY_PRESET_MODES,
    SELL_PRESET_MODES,
    filter_insider_filings_by_preset,
)


def test_insider_presets_registry_covers_supported_presets():
    assert "market" in INSIDER_PRESETS
    assert "buy" in INSIDER_PRESETS
    assert "sell" in INSIDER_PRESETS
    assert "Market Purchase" in BUY_PRESET_MODES
    assert "Block Deal" in BUY_PRESET_MODES
    assert "Market Sale" in SELL_PRESET_MODES


def test_filter_insider_filings_by_preset_supports_presets():
    metadata = {
        "api": [
            "transactionDirection",
            "postTransactionSecurityType",
            "transactionMode",
            "symbol",
        ]
    }
    filings = [
        {"api": ["Buy", "Equity Shares", "Market Purchase", "AAA"]},
        {"api": ["Sell", "Equity Shares", "Market Sale", "BBB"]},
        {"api": ["Buy", "Equity Shares", "Block Deal", "CCC"]},
        {"api": ["Sell", "Equity Shares", "ESOS", "DDD"]},
        {
            "api": ["Buy", "Warrants", "Market Purchase", "EEE"]
        },  # Should be ignored by buy/sell preset
        {
            "api": ["Buy", "Equity Shares", "Inheritance", "FFF"]
        },  # Should be ignored by buy/sell preset
    ]
    data = {"metadata": metadata, "data": filings}

    filtered_market = filter_insider_filings_by_preset(data, "market")
    assert [row["api"][-1] for row in filtered_market["data"]] == ["AAA", "BBB", "EEE"]

    filtered_buy = filter_insider_filings_by_preset(data, "buy")
    assert [row["api"][-1] for row in filtered_buy["data"]] == ["AAA", "CCC"]

    filtered_sell = filter_insider_filings_by_preset(data, "sell")
    assert [row["api"][-1] for row in filtered_sell["data"]] == ["BBB", "DDD"]


def test_holding_delta_pct():
    from nse_corporate_data.insider import _holding_delta_pct

    # Test new shares-based calculation
    context_shares = {
        "holdingBeforeShares": "1000",
        "holdingAfterShares": "1500",
        "sharesOutstanding": "10000",
        "holdingBeforePct": "10.00",
        "holdingAfterPct": "15.00",
    }
    assert _holding_delta_pct(context_shares) == 5.0

    # Test fallback to pct-based calculation
    context_pct_only = {
        "holdingBeforePct": "10.00",
        "holdingAfterPct": "15.55",
    }
    assert _holding_delta_pct(context_pct_only) == 5.55

    # Test missing data
    assert _holding_delta_pct({}) is None
