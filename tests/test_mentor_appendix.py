"""Appendix E must stay in step with the chapters, the fault script and the lab notes it refers to."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
APPENDIX = (ROOT / 'book/E-mentor.md').read_text(encoding='utf-8')


def section(title):
    start = APPENDIX.index(title)
    nxt = re.search(r'^## ', APPENDIX[start + len(title):], re.M)
    return APPENDIX[start:start + len(title) + nxt.start()] if nxt else APPENDIX[start:]


class MentorAppendixTest(unittest.TestCase):
    def test_fault_names_are_the_ones_the_script_injects(self):
        script = (ROOT / 'labs/faults/inject.sh').read_text(encoding='utf-8')
        faults = re.search(r'^FAULTS=\((.*?)\)', script, re.M).group(1).split()
        rows = re.findall(r'^\| \d \| ([a-z-]+) \|', section('## 障害の演習の進め方'), re.M)
        self.assertEqual(sorted(rows), sorted(faults))
        self.assertEqual(len(rows), 5)
        for command in re.findall(r'^\.\./faults/inject\.sh (\S+)$', APPENDIX, re.M):
            self.assertIn(command, faults + ['list', 'random', 'reveal'])

    def test_wait_times_match_the_script(self):
        script = (ROOT / 'labs/faults/inject.sh').read_text(encoding='utf-8')
        waits = set(re.findall(r'（(\d+)分ほど待ってから調べ始める）', script))
        self.assertEqual(waits, {'2', '10'})
        self.assertIn('2分か10分', APPENDIX)

    def test_every_step_has_a_row_in_the_review_table(self):
        table = section('## 合格の判定と記録')
        for n in range(1, 9):
            self.assertIn(f'| {n}（{{{{ch:s{n}}}}}） |', table)

    def test_headings_quoted_from_other_chapters_exist(self):
        quoted = {
            'book/10-env.md': ['どのアカウントで学ぶか', '最初の30分で必ずやること', '毎回の片付けチェックリスト', 'プラン：無料プランと有料プラン'],
            'book/39-field.md': ['質問と報告のしかた', '参画した最初の週に確認すること', '本番環境で作業するときのルール'],
            'book/40-road.md': ['5つのレベル', '学習の進め方', '分野別のチェック'],
            'book/14-s3.md': ['症状からではなく、通信の順に確かめる'],
            'book/38-cap.md': ['評価の基準'],
        }
        for path, titles in quoted.items():
            text = (ROOT / path).read_text(encoding='utf-8')
            for title in titles:
                self.assertIn(f'「{title}」', APPENDIX, title)
                self.assertRegex(text, rf'(?m)^(#+|:::\w+) {re.escape(title)}', f'{path} has no heading "{title}"')

    def test_cost_note_matches_the_lab_notes(self):
        self.assertIn('費用の目安は1ドル未満', (ROOT / 'labs/terraform/VERIFY.md').read_text(encoding='utf-8'))
        self.assertIn('費用の目安は1ドル未満', APPENDIX)

    def test_free_labs_are_the_ones_that_run_without_aws(self):
        free = section('## 費用の管理と、無料で進められる範囲')
        self.assertIn('{{ch:xnet}}、{{ch:mig}}、{{ch:k8s}}の、手元の実習', free)
        for lab in ['network', 'migration', 'k8s']:
            script = (ROOT / 'labs' / lab / 'verify.sh').read_text(encoding='utf-8')
            self.assertNotRegex(script, r'(?m)^\s*(run |try )?aws ', f'labs/{lab} is listed as free but calls AWS')


if __name__ == '__main__':
    unittest.main()
