from tools import search_listings


# ─────────────────────────────────────────────
# search_listings tests
# ─────────────────────────────────────────────

def test_search_returns_results():
    results = search_listings("vintage graphic tee", size=None, max_price=50)

    assert isinstance(results, list)
    assert len(results) > 0


def test_search_empty_results():
    results = search_listings("designer ballgown", size="XXS", max_price=5)

    assert results == []


def test_search_price_filter():
    results = search_listings("jacket", size=None, max_price=10)

    assert all(item["price"] <= 10 for item in results)


def test_search_size_filter():
    results = search_listings("tee", size="M", max_price=None)

    # If results exist, all should match size constraint loosely
    for item in results:
        assert "m" in item["size"].lower() or "s/m" in item["size"].lower()


def test_search_no_exception_on_empty():
    # robustness test — should NEVER crash
    results = search_listings("nonexistentxyz123", size="XS", max_price=1)

    assert isinstance(results, list)