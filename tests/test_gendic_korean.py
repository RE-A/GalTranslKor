"""한국어 대상 GenDic: 프롬프트·힌트·사전 파일이 한국어로 나오는지 확인(합성 데이터)."""

import unittest

from GalTransl.Backend.GenDic import _category_of, _merge_into_sections
from tests.test_gendic_pipeline import _ChatSession, _make_engine


def _korean_engine():
    engine = _make_engine()
    engine.target_lang = "Korean"
    return engine


class KoreanCategoryTests(unittest.TestCase):
    def test_korean_note_types_map_to_categories(self):
        self.assertEqual(_category_of("인명, 여성"), "人名")
        self.assertEqual(_category_of("호칭, 유이의 애칭"), "称呼")
        self.assertEqual(_category_of("지명"), "地名")
        self.assertEqual(_category_of("조직, 학교"), "组织")
        self.assertEqual(_category_of("물품, 무기"), "物品")
        self.assertEqual(_category_of("기타, 책 제목"), "其他")

    def test_korean_sections_and_header(self):
        lines = _merge_into_sections(
            [], [["瑠那", "루나", "인명, 여성"], ["白鷺市", "시라사기시", "지명"]], korean=True
        )
        self.assertTrue(lines[0].startswith("#"))
        self.assertIn("한국어", lines[0])
        self.assertIn("----------↓인명↓----------", lines)
        self.assertIn("----------↓지명↓----------", lines)
        # 기존 한국어 구역에 이어 붙임
        lines2 = _merge_into_sections(lines, [["咲來", "사쿠라", "인명, 여성"]], korean=True)
        self.assertEqual(lines2.count("----------↓인명↓----------"), 1)
        self.assertLess(lines2.index("咲來\t사쿠라\t인명, 여성"), lines2.index("----------↓지명↓----------"))


class KoreanPromptTests(unittest.IsolatedAsyncioTestCase):
    async def test_extraction_prompt_is_korean(self):
        engine = _korean_engine()
        engine.existing_dict_map = {"マジホ": ("마지호", "물품")}
        prompts = []

        async def fake_ask(prompt, task_label, task_index, session=None):
            prompts.append(prompt)
            rsp = "일본어 원문\t한국어 번역\t비고\n瑠那\t루나\t인명, 여성"
            if session is not None:
                session.add_turn(prompt, rsp)
            return rsp

        engine._ask_gendic = fake_ask
        session = _ChatSession()
        await engine.llm_gen_dic("瑠那：マジホ", task_index=0, session=session)
        await engine.llm_gen_dic("瑠那：マジホ", task_index=1, session=session)
        self.assertIn("한국어", prompts[0])
        self.assertNotIn("中文", prompts[0])
        self.assertIn("マジホ\t마지호\t물품", prompts[0])
        self.assertNotIn("中文", prompts[1])
        self.assertEqual(engine.dic_votes["瑠那"]["루나"], 2)
        self.assertNotIn("일본어 원문", engine.dic_votes)

    def test_korean_system_prompt(self):
        engine = _korean_engine()
        self.assertIn("한국어", engine._gendic_prompt("SYSTEM"))
        self.assertNotIn("日译中", engine._gendic_prompt("SYSTEM"))
        self.assertIn("日译中", _make_engine()._gendic_prompt("SYSTEM"))

    def test_all_korean_prompts_keep_placeholders(self):
        from GalTransl.Backend import Prompts

        for name in ("PROMPT", "FOLLOWUP_PROMPT", "NAME_PROMPT", "REVIEW_PROMPT", "REVIEW_FOLLOWUP_PROMPT"):
            zh = getattr(Prompts, f"GENDIC_{name}")
            ko = getattr(Prompts, f"GENDIC_{name}_KO")
            for key in ("{input}", "{hint}", "{fixed}", "{catalog}", "{protected}"):
                self.assertEqual(key in zh, key in ko, f"{name} {key}")
            self.assertNotRegex(ko, r"中文|日译中")


if __name__ == "__main__":
    unittest.main()
