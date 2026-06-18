"""Integration tests for key view behaviours.

Covers: session auth enforcement, request validation, and the pure helpers.
External HTTP calls (Blizzard API) are not made — tests stop at the view logic
that runs before those calls.
"""

import pytest
from django.test import Client

from apicore.libs.keybind_builder import tier_sort_key

# ---------------------------------------------------------------------------
# Pure helper: _tier_sort_key
# ---------------------------------------------------------------------------


class TestTierSortKey:
    def test_known_expansion_returns_order(self):
        assert tier_sort_key("Khaz Algar Blacksmithing") == 10
        assert tier_sort_key("Dragon Isles Alchemy") == 9
        assert tier_sort_key("Shadowlands Mining") == 8

    def test_classic_is_lowest(self):
        assert tier_sort_key("Classic Leatherworking") == 0

    def test_unknown_expansion_returns_999(self):
        assert tier_sort_key("Some Future Expansion Cooking") == 999

    def test_case_insensitive(self):
        assert tier_sort_key("KHAZ ALGAR Alchemy") == 10


# ---------------------------------------------------------------------------
# BnetLogin — state validation (no external HTTP)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestBnetLogin:
    def test_wrong_state_returns_error(self, client: Client):
        resp = client.post(
            "/api/custom/bnetlogin/",
            data={"state": "wrong"},
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.json() == "error"

    def test_missing_state_returns_error(self, client: Client):
        resp = client.post(
            "/api/custom/bnetlogin/",
            data={},
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.json() == "error"


# ---------------------------------------------------------------------------
# ScanAlt — session enforcement
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestScanAlt:
    def test_no_userid_returns_nouser(self, client: Client):
        resp = client.post(
            "/api/custom/scanalt/",
            data={},
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.json() == "nouser"

    def test_session_mismatch_returns_403(self, client: Client):
        session = client.session
        session["user_id"] = "other-user"
        session.save()

        resp = client.post(
            "/api/custom/scanalt/",
            data={"userid": "target-user"},
            content_type="application/json",
        )
        assert resp.status_code == 403

    def test_no_session_returns_403(self, client: Client):
        resp = client.post(
            "/api/custom/scanalt/",
            data={"userid": "some-user"},
            content_type="application/json",
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# ProfileUserView — list parameters
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestProfileUserView:
    def _authed_client(self, user_id: str) -> Client:
        c = Client()
        session = c.session
        session["user_id"] = user_id
        session.save()
        return c

    def test_missing_params_returns_hey(self):
        c = self._authed_client("u1")
        resp = c.get("/api/profile/users/?user=u1")
        assert resp.status_code == 200
        assert resp.json() == "hey"

    def test_no_session_returns_403(self, client: Client):
        resp = client.get("/api/profile/users/?user=u1")
        assert resp.status_code == 403

    def test_header_page_for_unknown_user_returns_empty(self):
        c = self._authed_client("nobody")
        resp = c.get("/api/profile/users/?user=nobody&page=header")
        assert resp.status_code == 200
        assert resp.json() == []


# ---------------------------------------------------------------------------
# ProfileAltView — IsSessionUser enforcement
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestProfileAltView:
    def test_no_session_returns_403(self, client: Client):
        resp = client.get("/api/profile/alts/?user=u1")
        assert resp.status_code == 403

    def test_wrong_session_returns_403(self, client: Client):
        session = client.session
        session["user_id"] = "other"
        session.save()
        resp = client.get("/api/profile/alts/?user=u1")
        assert resp.status_code == 403

    def test_correct_session_returns_200(self, client: Client):
        session = client.session
        session["user_id"] = "u1"
        session.save()
        resp = client.get("/api/profile/alts/?user=u1")
        assert resp.status_code == 200
        assert resp.json() == []


# ---------------------------------------------------------------------------
# ProfileAltEquipmentView — session and page parameter enforcement
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestProfileAltEquipmentView:
    def test_no_page_param_returns_empty(self, client: Client):
        session = client.session
        session["user_id"] = "u1"
        session.save()
        resp = client.get("/api/profile/altequipments/?user=u1")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_all_session_mismatch_returns_403(self, client: Client):
        session = client.session
        session["user_id"] = "other"
        session.save()
        resp = client.get("/api/profile/altequipments/?user=u1&page=all")
        assert resp.status_code == 403

    def test_list_all_no_user_param_returns_empty(self, client: Client):
        session = client.session
        session["user_id"] = "u1"
        session.save()
        resp = client.get("/api/profile/altequipments/?page=all")
        assert resp.status_code == 200
        assert resp.json() == []
