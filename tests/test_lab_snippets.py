"""The Terraform code printed in the book must be the code in labs/terraform, character for character."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / 'labs/terraform'
MARK = '# labs/terraform/'


def printed_excerpts():
    for path in sorted((ROOT / 'book').glob('*.md')):
        text = path.read_text(encoding='utf-8')
        for block in re.findall(r'```hcl\n(.*?)\n```', text, re.S):
            first, _, body = block.partition('\n')
            if first.startswith(MARK):
                yield path.name, first[len(MARK):].strip(), body


class LabSnippetTest(unittest.TestCase):
    def test_every_printed_excerpt_is_in_the_lab(self):
        excerpts = list(printed_excerpts())
        self.assertGreaterEqual(len(excerpts), 10, 'the chapter should quote the reference implementation')
        for chapter, name, body in excerpts:
            with self.subTest(chapter=chapter, file=name):
                source = (LAB / name).read_text(encoding='utf-8')
                self.assertIn(body, source, f'{chapter}: excerpt of {name} differs from labs/terraform/{name}')

    def test_files_listed_in_the_chapter_exist(self):
        chapter = (ROOT / 'book/18-s7.md').read_text(encoding='utf-8')
        listed = re.findall(r'^\| ((?:tests/)?[a-z_]+\.(?:tf|tftest\.hcl)) \|', chapter, re.M)
        self.assertGreaterEqual(len(listed), 9)
        for name in listed:
            self.assertTrue((LAB / name).is_file(), f'labs/terraform/{name} is listed in the chapter but missing')

    def test_user_data_matches_the_script_in_chapter_14(self):
        chapter = (ROOT / 'book/14-s3.md').read_text(encoding='utf-8')
        printed = re.findall(r'```bash\n(#!/bin/bash\n.*?)\n```', chapter, re.S)[0]
        self.assertEqual(printed.strip(), (LAB / 'user_data.sh').read_text(encoding='utf-8').strip())

    def test_lab_never_contains_state_or_secrets(self):
        names = [p.name for p in LAB.rglob('*') if p.is_file()]
        self.assertFalse([n for n in names if n.endswith(('.tfstate', '.tfstate.backup')) or n == 'terraform.tfvars'])
        self.assertIn('.terraform.lock.hcl', names, 'the provider lock file must be committed')
        for path in LAB.rglob('*.tf'):
            source = path.read_text(encoding='utf-8')
            self.assertIsNone(re.search(r'AKIA[0-9A-Z]{16}', source), path.name)
            self.assertIsNone(re.search(r'^\s*password\s*=', source, re.M), f'{path.name}: no password argument')


if __name__ == '__main__':
    unittest.main()
