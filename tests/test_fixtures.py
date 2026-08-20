"""The golden set must stay varied. A monotonous dataset flatters every agent."""


def test_golden_set_size(golden_tickets):
    assert len(golden_tickets) == 10


def test_golden_set_is_varied(golden_tickets):
    categories = {t["category"] for t in golden_tickets}
    assert len(categories) >= 4, f"only {len(categories)} categories — too monotonous to be a test"


def test_golden_set_has_a_very_short_ticket(golden_tickets):
    """T-1006 is 'it's broken'. It exists so agents must learn to ask instead of guess."""
    assert any(len(t["body"]) < 40 for t in golden_tickets)


def test_golden_set_has_a_long_ticket(golden_tickets):
    """T-1009 is the context-budget case for Day 4."""
    assert any(len(t["body"]) > 300 for t in golden_tickets)


def test_every_ticket_has_the_required_fields(golden_tickets):
    for t in golden_tickets:
        assert set(t) == {"id", "severity", "category", "body"}, f"bad shape: {t.get('id')}"


def test_ticket_ids_are_unique(golden_tickets):
    ids = [t["id"] for t in golden_tickets]
    assert len(ids) == len(set(ids)), "duplicate ticket id"
