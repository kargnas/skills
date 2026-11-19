"""Checks gh_pool's discovery of gh's own logins: python3 scripts/test_gh_pool.py"""
import tempfile
import unittest
from pathlib import Path

from gh_pool import gh_tokens, hosts_account

# gh 2.40+ hosts.yml with two signed-in users whose tokens gh kept in the file:
# the active account sits at the host's own level, and every user repeats below
# `users:`.
TWO_USERS = """\
github.com:
    users:
        alice:
            oauth_token: gho_alice
        bob:
            oauth_token: gho_bob
    git_protocol: https
    oauth_token: gho_bob
    user: bob
"""
# The same login with its token in the system keyring: no token in the file.
KEYRING = """\
github.com:
    users:
        bob:
    git_protocol: https
    user: bob
"""


class GhLoginDiscovery(unittest.TestCase):
    def test_active_account_wins_over_the_users_map(self):
        self.assertEqual(hosts_account(TWO_USERS), ("bob", "gho_bob"))

    def test_keyring_login_has_no_token(self):
        self.assertEqual(hosts_account(KEYRING), ("bob", None))

    def test_one_token_per_login_across_default_dir_and_profiles(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "hosts.yml").write_text(TWO_USERS)
            # A second profile of bob shares bob's quota, so it must not join.
            for profile, login in (("bob-for-org", "bob"), ("bot", "carol")):
                (root / profile).mkdir()
                (root / profile / "hosts.yml").write_text(
                    f"github.com:\n    oauth_token: gho_{profile}\n    user: {login}\n"
                )
            (root / "keyring-only").mkdir()
            (root / "keyring-only" / "hosts.yml").write_text(KEYRING.replace("bob", "dave"))
            tokens = [token for _, token in gh_tokens(root)]
        self.assertEqual(tokens, ["gho_bob", "gho_bot"])


if __name__ == "__main__":
    unittest.main()
