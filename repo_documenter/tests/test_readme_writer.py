import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from repo_documenter.tools.readme_writer import prepare_readme_review, commit_readme


class ReadmeReviewTests(unittest.TestCase):
    def test_prepare_review_does_not_modify_existing_readme(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            readme = root / "README.md"
            readme.write_text("# Existing\n", encoding="utf-8")

            review = prepare_readme_review({
                "repository_path": str(root),
                "markdown": "# Proposed\n\nNew documentation.\n",
            })

            self.assertEqual(readme.read_text(encoding="utf-8"), "# Existing\n")
            self.assertIn("-# Existing", review["diff"])
            self.assertIn("+# Proposed", review["diff"])

    def test_rejected_proposal_does_not_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            readme = root / "README.md"
            readme.write_text("# Existing\n", encoding="utf-8")
            review = prepare_readme_review({
                "repository_path": str(root),
                "markdown": "# Proposed\n",
            })

            result = commit_readme(json.dumps({"approved": False, "review": review}))

            self.assertEqual(result["status"], "rejected")
            self.assertEqual(readme.read_text(encoding="utf-8"), "# Existing\n")

    def test_accept_backs_up_and_replaces(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            readme = root / "README.md"
            readme.write_text("# Existing\n", encoding="utf-8")
            review = prepare_readme_review({
                "repository_path": str(root),
                "markdown": "# Proposed\n",
            })

            result = commit_readme(json.dumps({"approved": True, "review": review}))

            self.assertEqual(result["status"], "success")
            self.assertEqual(readme.read_text(encoding="utf-8"), "# Proposed\n")
            self.assertEqual(Path(result["backup_path"]).read_text(encoding="utf-8"), "# Existing\n")

    def test_accept_refuses_if_readme_changed_after_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            readme = root / "README.md"
            readme.write_text("# Existing\n", encoding="utf-8")
            review = prepare_readme_review({
                "repository_path": str(root),
                "markdown": "# Proposed\n",
            })
            readme.write_text("# Edited after review\n", encoding="utf-8")

            with self.assertRaisesRegex(RuntimeError, "changed after the review"):
                commit_readme(json.dumps({"approved": True, "review": review}))


if __name__ == "__main__":
    unittest.main()
