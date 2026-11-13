"""Chapter 6's hands-on section and appendix F must print only commands that labs/basics/inside.sh runs, in a real Amazon Linux 2023 container."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / 'labs/basics/inside.sh').read_text(encoding='utf-8')
NET = (ROOT / 'book/06-net.md').read_text(encoding='utf-8')
APPENDIX = (ROOT / 'book/F-basics.md').read_text(encoding='utf-8')
# 本文にあって、スクリプトでは実行しないもの：コンテナに入る操作と、systemd（コンテナでは動かない）
NOT_RUN = re.compile(r'^docker run |systemctl|journalctl')


def commands(text):
    for block in re.findall(r'```bash\n(.*?)```', text, re.S):
        for line in block.splitlines():
            line = line.strip()
            if line and not line.startswith('#') and not NOT_RUN.search(line):
                yield line


class BasicsLabTest(unittest.TestCase):
    def test_chapter6_hands_on_commands_are_run(self):
        section = NET[NET.index('### 手元で確かめる'):NET.index('## IPアドレスの種類と範囲（CIDR）')]
        lines = list(commands(section))
        self.assertGreaterEqual(len(lines), 20)
        for line in lines:
            self.assertIn(line, SCRIPT, f'chapter 6 shows a command the lab script never runs: {line}')

    def test_appendix_commands_are_run(self):
        body = APPENDIX[:APPENDIX.index('## 章末問題')]
        lines = list(commands(body))
        self.assertGreaterEqual(len(lines), 90)
        for line in lines:
            self.assertIn(line, SCRIPT, f'appendix F shows a command the lab script never runs: {line}')

    def test_commands_run_in_the_printed_order(self):
        for text, start, end in [(NET, '### 手元で確かめる', '## IPアドレスの種類と範囲（CIDR）'), (APPENDIX, '## 練習の場所', '## 章末問題')]:
            position = 0
            for line in commands(text[text.index(start):text.index(end)]):
                found = SCRIPT.find(line, position)
                self.assertGreaterEqual(found, 0, f'out of order: {line}')
                position = found

    def test_printed_conflict_is_the_one_the_script_checks(self):
        printed = re.search(r'```text\n(<<<<<<< HEAD\n.*?)\n```', APPENDIX, re.S).group(1).splitlines()
        self.assertIn("printf '%s\\n' " + ' '.join(f"'{line}'" for line in printed), SCRIPT)

    def test_appendix_is_registered_and_linked(self):
        manifest = (ROOT / 'tools/manifest.py').read_text(encoding='utf-8')
        self.assertIn("('basics', '付録F', 'LinuxとGitの基礎', 0, [])", manifest)
        for name in ['00-guide.md', '06-net.md', '10-env.md']:
            self.assertIn('{{ch:basics}}', (ROOT / 'book' / name).read_text(encoding='utf-8'), name)


if __name__ == '__main__':
    unittest.main()
