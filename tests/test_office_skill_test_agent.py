import unittest
from unittest.mock import patch

from office_skill_test_agent import (
    DEFAULT_PROJECT_ENDPOINT,
    build_office_skill_test_prompt,
    parse_args,
    resolve_model_deployment_name,
    resolve_project_endpoint,
)


class OfficeSkillTestAgentTests(unittest.TestCase):
    def test_default_project_endpoint_matches_issue_endpoint(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(resolve_project_endpoint(), DEFAULT_PROJECT_ENDPOINT)

    def test_project_endpoint_environment_override_wins(self) -> None:
        with patch.dict("os.environ", {"PROJECT_ENDPOINT": "https://example.test/project"}, clear=True):
            self.assertEqual(resolve_project_endpoint(), "https://example.test/project")

    def test_model_deployment_name_is_required(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaisesRegex(ValueError, "MODEL_DEPLOYMENT_NAME"):
                resolve_model_deployment_name()

    def test_prompt_mentions_word_and_powerpoint_flows(self) -> None:
        prompt = build_office_skill_test_prompt()
        self.assertIn("Word document", prompt)
        self.assertIn("PowerPoint presentation", prompt)
        self.assertIn("missing skills", prompt)

    def test_parse_args_supports_skip_run_and_prompt(self) -> None:
        args = parse_args(["--skip-run", "--prompt", "Save files in a test folder."])
        self.assertTrue(args.skip_run)
        self.assertEqual(args.prompt, "Save files in a test folder.")


if __name__ == "__main__":
    unittest.main()
