from nse_corporate_data.insider import (
    INSIDER_MODES,
    INSIDER_MODE_TO_ACQ_MODE,
    filter_insider_filings_by_mode,
)


def test_insider_mode_registry_covers_full_supported_acquisition_modes():
    assert INSIDER_MODE_TO_ACQ_MODE["allotment"] == ("Allotment",)
    assert INSIDER_MODE_TO_ACQ_MODE["beneficiary-from-trusts"] == (
        "Beneficiary from Trusts",
    )
    assert INSIDER_MODE_TO_ACQ_MODE["block-deal"] == ("Block Deal",)
    assert INSIDER_MODE_TO_ACQ_MODE["buy-back"] == ("Buy Back",)
    assert INSIDER_MODE_TO_ACQ_MODE["esos"] == ("ESOS",)
    assert INSIDER_MODE_TO_ACQ_MODE["inheritance"] == ("Inheritance",)
    assert INSIDER_MODE_TO_ACQ_MODE["pledge-release"] == ("Pledge Release",)
    assert INSIDER_MODE_TO_ACQ_MODE["pledge-revoke"] == ("Revocation of Pledge",)

    assert "pledge-release" in INSIDER_MODES
    assert "pledge-revoke" in INSIDER_MODES


def test_filter_insider_filings_by_mode_supports_new_acquisition_modes():
    filings = [
        {"symbol": "AAA", "acqMode": "Allotment"},
        {"symbol": "BBB", "acqMode": "ESOS"},
        {"symbol": "CCC", "acqMode": "Block Deal"},
        {"symbol": "DDD", "acqMode": "Pledge Release"},
        {"symbol": "EEE", "acqMode": "Revocation of Pledge"},
    ]

    filtered = filter_insider_filings_by_mode(
        filings,
        ("allotment", "esos", "block-deal", "pledge-release", "pledge-revoke"),
    )

    assert [row["symbol"] for row in filtered] == ["AAA", "BBB", "CCC", "DDD", "EEE"]
