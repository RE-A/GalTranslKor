"""한국어 대상 프로젝트에서 에이전트 시스템 프롬프트가 한국어 번역을 요구하는지 확인(합성 설정)."""

import os
import tempfile
import unittest

from GalTransl.Agent.models import AgentState
from GalTransl.Agent.prompts import (
    COMPACT_INSTRUCTION_PROMPT,
    COMPACT_SUMMARY_PROMPT,
    _build_system_prompt,
)
from GalTransl.Agent.subagent import SUBAGENT_COMPACT_INSTRUCTION_PROMPT


def _project(language):
    tmp = tempfile.TemporaryDirectory()
    with open(os.path.join(tmp.name, "config.yaml"), "w", encoding="utf-8") as f:
        f.write(f"common:\n  language: {language}\n")
    return tmp


class AgentKoreanTargetTests(unittest.TestCase):
    def test_korean_project_adds_target_language_section(self):
        with _project("ja2ko") as d:
            prompt = _build_system_prompt(AgentState(project_dir=d, config_file_name="config.yaml"))
        self.assertIn("# 번역 대상 언어: 한국어", prompt)
        self.assertIn("日文<Tab>韩文", prompt)

    def test_chinese_project_keeps_prompt(self):
        with _project("ja2zh-cn") as d:
            prompt = _build_system_prompt(AgentState(project_dir=d, config_file_name="config.yaml"))
        self.assertNotIn("번역 대상 언어", prompt)

    def test_missing_config_is_tolerated(self):
        prompt = _build_system_prompt(AgentState(project_dir="no-such-dir", config_file_name="x.yaml"))
        self.assertNotIn("번역 대상 언어", prompt)

    def test_summaries_follow_user_language(self):
        for text in (COMPACT_SUMMARY_PROMPT, COMPACT_INSTRUCTION_PROMPT, SUBAGENT_COMPACT_INSTRUCTION_PROMPT):
            self.assertNotIn("用中文", text)


if __name__ == "__main__":
    unittest.main()
