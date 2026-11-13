"""The filled-in parameter sheet in appendix D must show the values of the reference implementation."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / 'labs/terraform'
SHEET = (ROOT / 'book/D-docs.md').read_text(encoding='utf-8')


def lab(name, pattern):
    match = re.search(pattern, (LAB / name).read_text(encoding='utf-8'), re.S)
    assert match, f'{name}: {pattern}'
    return match.group(1)


def default(variable):
    return lab('variables.tf', r'variable "' + variable + r'".*?default\s+= "?([^"\n]+)"?')


class ParameterSheetTest(unittest.TestCase):
    def test_address_design(self):
        vpc = lab('network.tf', r'cidr_block\s+= "(10\.0\.0\.0/16)"')
        self.assertIn(f'| VPCのCIDR | {vpc} |', SHEET)
        rows = re.findall(r'^\s+([a-z]+-[ac])\s+= \{ tier = "([a-z]+)", az = local\.azs\[(\d)\], cidr = "([\d./]+)" \}',
                          (LAB / 'network.tf').read_text(encoding='utf-8'), re.M)
        self.assertEqual(len(rows), 6)
        for name, tier, az, cidr in rows:
            order = '1つ目' if az == '0' else '2つ目'
            self.assertIn(f'| {name} | {order}のAZ | {cidr} | {tier} |', SHEET)

    def test_servers_and_load_balancer(self):
        grace = lab('compute.tf', r'health_check_grace_period = (\d+)')
        percent = lab('compute.tf', r'min_healthy_percentage = (\d+)')
        interval = lab('compute.tf', r'\binterval\s+= (\d+)')
        timeout = lab('compute.tf', r'\btimeout\s+= (\d+)')
        healthy = lab('compute.tf', r'\bhealthy_threshold\s+= (\d+)')
        unhealthy = lab('compute.tf', r'\bunhealthy_threshold\s+= (\d+)')
        delay = lab('compute.tf', r'deregistration_delay = (\d+)')
        matcher = lab('compute.tf', r'matcher\s+= "(\d+)"')
        expected = [
            f'| インスタンスタイプ | {default("instance_type")} |',
            f'| 台数 | 最小{default("app_min_size")}、最大{default("app_max_size")} |',
            f'ELB。猶予期間{grace}秒',
            f'正常な割合の下限{percent}%',
            f'成功コード{matcher}、間隔{interval}秒、タイムアウト{timeout}秒、しきい値は正常{healthy}回・異常{unhealthy}回',
            f'| 登録解除の待ち時間 | {delay}秒 |',
        ]
        for text in expected:
            self.assertIn(text, SHEET)
        self.assertEqual(lab('compute.tf', r'http_tokens\s+= "(\w+)"'), 'required')
        self.assertEqual(lab('compute.tf', r'health_check_type\s+= "(\w+)"'), 'ELB')

    def test_database(self):
        storage = lab('database.tf', r'storage_type\s+= "(\w+)"')
        size = lab('database.tf', r'allocated_storage = (\d+)')
        name = lab('database.tf', r'db_name\s+= "(\w+)"')
        user = lab('database.tf', r'username = "(\w+)"')
        keep = lab('database.tf', r'backup_retention_period = (\d+)')
        expected = [
            f'| エンジンと版 | PostgreSQL {default("db_engine_version")} |',
            f'| インスタンスクラス | {default("db_instance_class")} |',
            f'| 保存領域 | {storage}、{size}GB、暗号化あり |',
            f'| データベース名、管理者の名前 | {name}、{user} |',
            f'| 自動バックアップの保持 | {keep}日 |',
        ]
        for text in expected:
            self.assertIn(text, SHEET)

    def test_security_group_ports(self):
        rules = (LAB / 'security.tf').read_text(encoding='utf-8')
        self.assertEqual(sorted(set(re.findall(r'from_port\s+= (\d+)', rules))), ['5432', '80'])
        for row in ['| app | 受信 | TCP 80 | alb のセキュリティグループ |', '| db | 受信 | TCP 5432 | app のセキュリティグループ |',
                    '| alb | 受信 | TCP 80 | 0.0.0.0/0 |']:
            self.assertIn(row, SHEET)

    def test_fault_names_in_the_book_exist_in_the_script(self):
        script = (ROOT / 'labs/faults/inject.sh').read_text(encoding='utf-8')
        names = re.search(r'^FAULTS=\(([^)]*)\)', script, re.M).group(1).split()
        chapter = (ROOT / 'book/35-ts.md').read_text(encoding='utf-8')
        runbook = (LAB / 'VERIFY.md').read_text(encoding='utf-8')
        self.assertEqual(len(names), 5)
        for name in names:
            self.assertIn(f'入っていた障害：{name}（', chapter)
            self.assertIn(f'| {name} |', runbook)
            self.assertIn(f'    {name})', script)


if __name__ == '__main__':
    unittest.main()
