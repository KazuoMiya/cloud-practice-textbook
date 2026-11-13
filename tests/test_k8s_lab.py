"""Chapter 31 must print the lab files as they are, and its commands must be the ones the lab script runs."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / 'labs/k8s'
CHAPTER = (ROOT / 'book/31-k8s.md').read_text(encoding='utf-8')
SCRIPT = (LAB / 'verify.sh').read_text(encoding='utf-8')
CHANGES_STATE = re.compile(r'^(kind (create|delete) |kubectl (apply|drain|uncordon)|kubectl -n cloudbook (set image|patch|rollout undo|rollout status|rollout history))')


class KubernetesLabTest(unittest.TestCase):
    def test_printed_manifests_are_the_lab_files(self):
        printed = re.findall(r'```yaml\n# labs/k8s/([\w.]+)\n(.*?)\n```', CHAPTER, re.S)
        self.assertEqual(sorted(name for name, _ in printed), ['kind.yaml', 'web.yaml'])
        for name, body in printed:
            self.assertEqual(body.strip(), (LAB / name).read_text(encoding='utf-8').strip(), name)

    def test_commands_in_the_chapter_are_run_by_the_script(self):
        section = CHAPTER[CHAPTER.index('## 手元のクラスターで確かめる'):CHAPTER.index('## EKSでは、誰が何を管理するか')]
        lines = [line.strip() for block in re.findall(r'```bash\n(.*?)```', section, re.S) for line in block.splitlines()]
        checked = [line for line in lines if CHANGES_STATE.match(line)]
        self.assertGreaterEqual(len(checked), 10)
        for line in checked:
            self.assertIn(line, SCRIPT, f'the chapter shows a command the lab script never runs: {line}')

    def test_names_used_in_the_chapter_match_the_manifests(self):
        web = (LAB / 'web.yaml').read_text(encoding='utf-8')
        kind = (LAB / 'kind.yaml').read_text(encoding='utf-8')
        self.assertIn('name: cloudbook', kind)
        self.assertEqual(len(re.findall(r'- role: worker', kind)), 2)
        self.assertIn('namespace: cloudbook', web)
        self.assertIn('replicas: 2 ', web)
        self.assertIn('image: nginx:1.27-alpine', web)
        for text in ['replicas: 2', 'nginx:1.28-alpine', 'cloudbook-worker2']:
            self.assertIn(text, CHAPTER)
            self.assertIn(text, SCRIPT)


if __name__ == '__main__':
    unittest.main()
