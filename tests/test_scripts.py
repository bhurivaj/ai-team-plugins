"""Stdlib-only tests for platform-core scripts. No network, no real credentials."""
import importlib, json, os, sys, tempfile, unittest

SCRIPTS = os.path.join(os.path.dirname(__file__), "..", "plugins", "platform-core", "scripts")
sys.path.insert(0, os.path.abspath(SCRIPTS))
import company_config  # noqa: E402


class TempProject(unittest.TestCase):
    def setUp(self):
        self.old_cwd = os.getcwd()
        self.old_env = os.environ.pop("CLAUDE_PROJECT_DIR", None)
        self.tmp = tempfile.TemporaryDirectory()
        self.root = os.path.realpath(self.tmp.name)
        cfg = {
            "company": "testco", "prefix": "tc",
            "wordpress": {"site_alias": "prod", "credentials": ".secret/wp.json"},
            "azure": {"credentials": ".secret/az.json"},
            "sharepoint": {"token_cache": "../shared/token.json"},
        }
        json.dump(cfg, open(os.path.join(self.root, "company.json"), "w"))
        os.makedirs(os.path.join(self.root, ".secret"))
        json.dump({"prod": {"URL": "https://example.test"}, "other": {"URL": "https://wrong.test"}},
                  open(os.path.join(self.root, ".secret", "wp.json"), "w"))
        json.dump({"accountName": "acct", "accountKey": "a2V5"}, open(os.path.join(self.root, ".secret", "az.json"), "w"))
        self.nested = os.path.join(self.root, "medias", "images")
        os.makedirs(self.nested)

    def tearDown(self):
        os.chdir(self.old_cwd)
        if self.old_env is not None:
            os.environ["CLAUDE_PROJECT_DIR"] = self.old_env
        self.tmp.cleanup()


class CompanyConfigTests(TempProject):
    def test_walks_up_from_nested_dir(self):
        os.chdir(self.nested)
        self.assertEqual(company_config.load()["_root"], self.root)

    def test_errors_outside_a_project(self):
        with tempfile.TemporaryDirectory() as empty:
            os.chdir(empty)
            with self.assertRaises(SystemExit):
                company_config.load()

    def test_falls_back_to_claude_project_dir(self):
        with tempfile.TemporaryDirectory() as empty:
            os.chdir(empty)
            os.environ["CLAUDE_PROJECT_DIR"] = self.root
            try:
                self.assertEqual(company_config.load()["_root"], self.root)
            finally:
                del os.environ["CLAUDE_PROJECT_DIR"]

    def test_path_is_relative_to_project_root(self):
        os.chdir(self.nested)
        cfg = company_config.load()
        self.assertEqual(company_config.path(cfg, "azure", "credentials"), os.path.join(self.root, ".secret", "az.json"))
        self.assertEqual(company_config.path(cfg, "sharepoint", "token_cache"),
                         os.path.normpath(os.path.join(self.root, "..", "shared", "token.json")))

    def test_wp_site_uses_alias_not_first_entry(self):
        os.chdir(self.root)
        self.assertEqual(company_config.wp_site(company_config.load())["URL"], "https://example.test")

    def test_wp_site_missing_alias_stops_instead_of_guessing(self):
        os.chdir(self.root)
        cfg = company_config.load()
        cfg["wordpress"]["site_alias"] = "nope"
        with self.assertRaises(SystemExit):
            company_config.wp_site(cfg)


class AzureUploadTests(TempProject):
    def setUp(self):
        super().setUp()
        os.chdir(self.root)  # azure_upload resolves its credential path at import time
        sys.modules.pop("azure_upload", None)
        self.az = importlib.import_module("azure_upload")

    def test_credential_path_comes_from_company_json(self):
        self.assertEqual(os.path.realpath(self.az.CRED_PATH), os.path.join(self.root, ".secret", "az.json"))

    def test_thai_and_space_segments_are_percent_encoded(self):
        self.assertEqual(self.az.encode_path_segment("ท่าน้ำนนท์ 2024.png"),
                         "%E0%B8%97%E0%B9%88%E0%B8%B2%E0%B8%99%E0%B9%89%E0%B8%B3%E0%B8%99%E0%B8%99%E0%B8%97%E0%B9%8C%202024.png")
        self.assertNotIn("/", self.az.encode_path_segment("a/b"))

    def test_shared_key_signature_is_deterministic(self):
        hdr = {"x-ms-date": "Mon, 02 Nov 2026 00:00:00 GMT", "x-ms-version": "2021-08-06"}
        a = self.az.sign_shared_key("GET", "acct", "a2V5", "/c/b.png", {"comp": "list"}, hdr, 0)
        b = self.az.sign_shared_key("GET", "acct", "a2V5", "/c/b.png", {"comp": "list"}, hdr, 0)
        self.assertEqual(a, b)
        self.assertTrue(a.startswith("SharedKey acct:"))


if __name__ == "__main__":
    unittest.main()
