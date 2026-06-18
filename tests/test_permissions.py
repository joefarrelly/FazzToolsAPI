"""Tests for apicore.permissions.IsSessionUser."""

from apicore.permissions import IsSessionUser


def _make_request(session_user: str | None, param_user: str | None) -> object:
    class _FakeRequest:
        session = {}
        query_params = {}

    req = _FakeRequest()
    if session_user is not None:
        req.session = {"user_id": session_user}
    req.query_params = {"user": param_user}
    return req


class TestIsSessionUser:
    def setup_method(self):
        self.perm = IsSessionUser()

    def test_no_session_denies(self):
        req = _make_request(session_user=None, param_user="abc")
        assert self.perm.has_permission(req, None) is False

    def test_mismatched_user_denies(self):
        req = _make_request(session_user="user-a", param_user="user-b")
        assert self.perm.has_permission(req, None) is False

    def test_matching_user_allows(self):
        req = _make_request(session_user="user-a", param_user="user-a")
        assert self.perm.has_permission(req, None) is True

    def test_missing_user_param_denies(self):
        req = _make_request(session_user="user-a", param_user=None)
        assert self.perm.has_permission(req, None) is False
