"""Chapter 29 must print the lab's check queries as they are, and its commands must be the ones the lab script runs."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / 'labs/migration'
CHAPTER = (ROOT / 'book/29-mig.md').read_text(encoding='utf-8')
SCRIPT = (LAB / 'verify.sh').read_text(encoding='utf-8')
RUN_BY_SCRIPT = re.compile(r'^(time )?docker compose (exec|up|down) |^diff <\(|^<\(')


class MigrationLabTest(unittest.TestCase):
    def test_printed_checks_are_the_lab_file(self):
        printed = re.findall(r'```sql\n-- labs/migration/checks\.sql\n(.*?)\n```', CHAPTER, re.S)
        self.assertEqual(len(printed), 1)
        self.assertEqual(printed[0].strip(), (LAB / 'checks.sql').read_text(encoding='utf-8').strip())

    def test_commands_in_the_chapter_are_run_by_the_script(self):
        section = CHAPTER[CHAPTER.index('## 手元で通す：移行のリハーサル'):CHAPTER.index('## 移した後に、良くしていく')]
        lines = [line.strip() for block in re.findall(r'```bash\n(.*?)```', section, re.S) for line in block.splitlines()]
        checked = [line for line in lines if RUN_BY_SCRIPT.match(line)]
        self.assertGreaterEqual(len(checked), 15)
        for line in checked:
            self.assertIn(line, SCRIPT, f'the chapter shows a command the lab script never runs: {line}')

    def test_numbers_in_the_chapter_match_the_seed_data(self):
        seed = (LAB / 'seed.sql').read_text(encoding='utf-8')
        self.assertIn('generate_series(1, 50)', seed)
        self.assertIn('generate_series(1, 2000)', seed)
        for text in ['顧客50件、注文2,000件', '2006', 'PostgreSQL 13', 'PostgreSQL 17']:
            self.assertIn(text, CHAPTER)
        compose = (LAB / 'compose.yaml').read_text(encoding='utf-8')
        self.assertIn('image: postgres:13-alpine', compose)
        self.assertIn('image: postgres:17-alpine', compose)
        self.assertNotIn('ports:', compose, 'the rehearsal databases must not be reachable from outside the machine')


if __name__ == '__main__':
    unittest.main()
