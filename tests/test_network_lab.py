"""Chapter 28 must print the lab's router settings as they are, and its commands must be the ones the lab script runs."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / 'labs/network'
CHAPTER = (ROOT / 'book/28-xnet.md').read_text(encoding='utf-8')
SCRIPT = (LAB / 'verify.sh').read_text(encoding='utf-8')
SECTION = CHAPTER[CHAPTER.index('## 手元で通す：社内とクラウドをつなぐ'):CHAPTER.index('### AWSで試す場合の費用')]
NODES = ['pc', 'dns-office', 'router-office', 'hub', 'web-prod', 'dns-cloud', 'web-dev']
# 本文にあって、スクリプトでは形を変えて実行するもの：コンテナに入る操作と、手で止める観察
NOT_RUN_AS_PRINTED = re.compile(r'^cd |^docker compose exec lab bash$|tcpdump')


class NetworkLabTest(unittest.TestCase):
    def test_printed_router_settings_are_the_lab_file(self):
        printed = re.findall(r'```text\n! labs/network/frr/router-office/frr\.conf\n(.*?)\n```', CHAPTER, re.S)
        self.assertEqual(len(printed), 1)
        self.assertEqual(printed[0].strip(), (LAB / 'frr/router-office/frr.conf').read_text(encoding='utf-8').strip())

    def test_the_two_routers_mirror_each_other(self):
        office = (LAB / 'frr/router-office/frr.conf').read_text(encoding='utf-8')
        hub = (LAB / 'frr/hub/frr.conf').read_text(encoding='utf-8')
        for text, own, peer in [(office, '65010', '64512'), (hub, '64512', '65010')]:
            self.assertIn(f'router bgp {own}', text)
            self.assertEqual(text.count(f'remote-as {peer}'), 2)
            self.assertIn('timers bgp 1 3', text)
            self.assertIn('set local-preference 200', text)

    def test_commands_in_the_chapter_are_run_by_the_script(self):
        lines = [line.strip() for block in re.findall(r'```bash\n(.*?)```', SECTION, re.S) for line in block.splitlines()]
        checked = [line for line in lines if line and not NOT_RUN_AS_PRINTED.search(line)]
        self.assertGreaterEqual(len(checked), 40)
        for line in checked:
            self.assertIn(line, SCRIPT, f'the chapter shows a command the lab script never runs: {line}')

    def test_addresses_in_the_chapter_match_the_lab(self):
        lab = (LAB / 'lab.sh').read_text(encoding='utf-8')
        for node, address in [('pc', '192.168.210.10'), ('dns-office', '192.168.210.53'), ('router-office', '192.168.210.254'),
                              ('router-office', '192.168.255.1'), ('hub', '192.168.255.2'), ('hub', '10.210.1.254'),
                              ('hub', '10.210.2.254'), ('web-prod', '10.210.1.10'), ('dns-cloud', '10.210.1.53'),
                              ('web-dev', '10.210.2.10')]:
            self.assertRegex(lab, rf'plug {re.escape(node)} \S+ {re.escape(address)}/\d+ ', f'{node} {address}')
            row = next(line for line in SECTION.splitlines() if line.startswith(f'| {node} |'))
            self.assertIn(address, row)
        dockerfile = (LAB / 'Dockerfile').read_text(encoding='utf-8')
        self.assertIn('for n in pc dns-office router-office hub web-prod web-dev dns-cloud;', dockerfile)
        self.assertEqual(sorted(NODES), sorted('pc dns-office router-office hub web-prod web-dev dns-cloud'.split()))

    def test_the_lab_container_is_cut_off_from_outside(self):
        compose = (LAB / 'compose.yaml').read_text(encoding='utf-8')
        self.assertIn('network_mode: none', compose)
        self.assertNotIn('ports:', compose)
        self.assertNotIn('volumes:', compose, 'a privileged container must not mount folders of the machine')
        self.assertIn('privileged', SECTION, 'the chapter must tell the reader that the container is privileged')


if __name__ == '__main__':
    unittest.main()
