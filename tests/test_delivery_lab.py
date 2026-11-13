"""Chapter 19's reference implementation: the app, the deploy and rollback scripts run against fake aws/docker commands,
and the chapter must print the lab files as they are."""
from pathlib import Path
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / 'labs/delivery'
CHAPTER = (ROOT / 'book/19-s8.md').read_text(encoding='utf-8')
ACCOUNT = '111122223333'
FAMILY_ARN = f'arn:aws:ecs:ap-northeast-1:{ACCOUNT}:task-definition/cloudbook-app'

# describe-task-definition の応答の形（登録のときには指定できない項目を含む）
REGISTERED = {
    'taskDefinitionArn': f'{FAMILY_ARN}:3',
    'family': 'cloudbook-app',
    'revision': 3,
    'status': 'ACTIVE',
    'requiresAttributes': [{'name': 'com.amazonaws.ecs.capability.logging-driver.awslogs'}],
    'compatibilities': ['EC2', 'FARGATE'],
    'registeredAt': '2026-11-13T10:00:00+09:00',
    'registeredBy': f'arn:aws:sts::{ACCOUNT}:assumed-role/cloudbook-github-deploy/x',
    'networkMode': 'awsvpc',
    'requiresCompatibilities': ['FARGATE'],
    'cpu': '256',
    'memory': '512',
    'executionRoleArn': f'arn:aws:iam::{ACCOUNT}:role/cloudbook-ecs-execution',
    'containerDefinitions': [
        {'name': 'app', 'image': f'{ACCOUNT}.dkr.ecr.ap-northeast-1.amazonaws.com/cloudbook-app:old', 'essential': True},
        {'name': 'sidecar', 'image': 'public.ecr.aws/example/sidecar:1.0', 'essential': False},
    ],
}

# 偽の aws：呼ばれた引数を記録し、決まった応答を返す。FAKE_ROLLED_BACK=1 のときは、
# ECSが前の版に自動で戻した後の状態を返す
FAKE_AWS = r'''#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$*" >> "$FAKE_DIR/aws.log"
case "$1 $2" in
  'sts get-caller-identity') echo 111122223333 ;;
  'ecr get-login-password') echo fake-password ;;
  'ecs describe-task-definition') cat "$FAKE_DIR/registered.json" ;;
  'ecs register-task-definition')
    for arg in "$@"; do case "$arg" in file://*) cp "${arg#file://}" "$FAKE_DIR/next.json" ;; esac; done
    echo arn:aws:ecs:ap-northeast-1:111122223333:task-definition/cloudbook-app:4 ;;
  'ecs update-service') echo ecs-svc/1234 ;;
  'ecs wait') ;;
  'ecs describe-services')
    if [[ "$*" == *rolloutState* ]]; then
      if [ "${FAKE_ROLLED_BACK:-0}" = 1 ]; then rev=3; else rev=4; fi
      printf 'arn:aws:ecs:ap-northeast-1:111122223333:task-definition/cloudbook-app:%s\tCOMPLETED\n' "${FAKE_RUNNING:-$rev}"
    else
      echo arn:aws:ecs:ap-northeast-1:111122223333:task-definition/cloudbook-app:3
    fi ;;
  *) echo "unexpected aws call: $*" >&2; exit 1 ;;
esac
'''
FAKE_DOCKER = r'''#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$*" >> "$FAKE_DIR/docker.log"
if [ "$1" = login ]; then cat > "$FAKE_DIR/password"; fi
'''


class FakeTools:
    def __init__(self):
        self.dir = Path(tempfile.mkdtemp())
        bin_dir = self.dir / 'bin'
        bin_dir.mkdir()
        for name, text in [('aws', FAKE_AWS), ('docker', FAKE_DOCKER)]:
            (bin_dir / name).write_text(text)
            (bin_dir / name).chmod(0o755)
        (self.dir / 'registered.json').write_text(json.dumps(REGISTERED))
        self.env = {**os.environ, 'PATH': f'{bin_dir}:{os.environ["PATH"]}', 'FAKE_DIR': str(self.dir),
                    'AWS_REGION': 'ap-northeast-1', 'ECR_REPOSITORY': 'cloudbook-app',
                    'ECS_CLUSTER': 'cloudbook', 'ECS_SERVICE': 'cloudbook-app', 'IMAGE_TAG': '0123abc'}

    def run(self, script, *args, **env):
        return subprocess.run(['bash', str(LAB / script), *args], env={**self.env, **env},
                              capture_output=True, text=True, timeout=60)

    def log(self, name):
        path = self.dir / f'{name}.log'
        return path.read_text().splitlines() if path.exists() else []

    def cleanup(self):
        shutil.rmtree(self.dir)


@unittest.skipUnless(shutil.which('jq'), 'jq is not installed')
class DeployScriptTest(unittest.TestCase):
    def setUp(self):
        self.fake = FakeTools()
        self.addCleanup(self.fake.cleanup)

    def test_deploy_builds_pushes_registers_and_switches(self):
        result = self.fake.run('deploy.sh')
        self.assertEqual(result.returncode, 0, result.stderr)
        image = f'{ACCOUNT}.dkr.ecr.ap-northeast-1.amazonaws.com/cloudbook-app:0123abc'
        docker = self.fake.log('docker')
        self.assertEqual(docker[0], f'login --username AWS --password-stdin {ACCOUNT}.dkr.ecr.ap-northeast-1.amazonaws.com')
        self.assertEqual(docker[1], f'build --platform linux/amd64 --build-arg APP_VERSION=0123abc -t {image} app')
        self.assertEqual(docker[2], f'push {image}')
        self.assertEqual((self.fake.dir / 'password').read_text().strip(), 'fake-password')

        sent = json.loads((self.fake.dir / 'next.json').read_text())
        for key in ['taskDefinitionArn', 'revision', 'status', 'requiresAttributes', 'compatibilities', 'registeredAt', 'registeredBy']:
            self.assertNotIn(key, sent)
        self.assertEqual(sent['containerDefinitions'][0]['image'], image)
        self.assertEqual(sent['containerDefinitions'][1], REGISTERED['containerDefinitions'][1])
        self.assertEqual(sent['executionRoleArn'], REGISTERED['executionRoleArn'])

        aws = self.fake.log('aws')
        self.assertIn(f'ecs update-service --cluster cloudbook --service cloudbook-app --task-definition {FAMILY_ARN}:4 '
                      "--query service.deployments[0].id --output text", aws)
        self.assertIn(f'bash rollback.sh {FAMILY_ARN}:3', result.stdout)

    def test_deploy_fails_when_ecs_rolled_back_by_itself(self):
        result = self.fake.run('deploy.sh', FAKE_ROLLED_BACK='1')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('新しい版に入れ替わりませんでした', result.stderr)

    def test_push_only_does_not_touch_ecs(self):
        env = {k: v for k, v in self.fake.env.items() if k not in ('ECS_CLUSTER', 'ECS_SERVICE')}
        self.fake.env = env
        result = self.fake.run('deploy.sh', '--push-only', IMAGE_TAG='first')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(any(line.startswith('ecs ') for line in self.fake.log('aws')))
        self.assertTrue(self.fake.log('docker')[-1].endswith('/cloudbook-app:first'))

    def test_latest_and_unknown_options_are_refused_before_anything_runs(self):
        self.assertNotEqual(self.fake.run('deploy.sh', IMAGE_TAG='latest').returncode, 0)
        self.assertEqual(self.fake.run('deploy.sh', '--push').returncode, 2)
        self.assertNotEqual(self.fake.run('deploy.sh', ECS_SERVICE='').returncode, 0)
        self.assertEqual(self.fake.log('aws') + self.fake.log('docker'), [])

    def test_rollback_switches_back_and_checks_the_result(self):
        result = self.fake.run('rollback.sh', 'cloudbook-app:4')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('ecs update-service --cluster cloudbook --service cloudbook-app --task-definition cloudbook-app:4 '
                      '--query service.deployments[0].id --output text', self.fake.log('aws'))
        self.assertIn('かかった時間', result.stdout)
        wrong = self.fake.run('rollback.sh', 'cloudbook-app:2')
        self.assertNotEqual(wrong.returncode, 0)


class TaskDefinitionFieldsTest(unittest.TestCase):
    """Every field describe-task-definition returns must either be removed by render-taskdef.jq or be accepted by register-task-definition."""

    def test_render_removes_exactly_the_read_only_fields(self):
        sys.path.insert(0, str(ROOT / 'tests'))
        import cli_examples_check as check
        if not shutil.which('aws'):
            self.skipTest('aws CLI not installed')
        models = check.Models(check.find_data())
        ecs = models.service('ecs')
        returned = set(ecs['shapes']['TaskDefinition']['members'])
        accepted = set(ecs['shapes']['RegisterTaskDefinitionRequest']['members'])
        removed = set(re.findall(r'\.(\w+)', re.search(r'del\((.*?)\)', (LAB / 'render-taskdef.jq').read_text(), re.S).group(1)))
        self.assertEqual(returned - accepted, removed, 'fields the API returns but registration refuses must be exactly the deleted ones')


class AppTest(unittest.TestCase):
    def test_app_unit_tests_pass(self):
        result = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests'], cwd=LAB / 'app',
                                capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stderr)


class ChapterMatchesLabTest(unittest.TestCase):
    def printed(self, header):
        blocks = re.findall(r'```\w+\n# ' + re.escape(header) + r'\n(.*?)\n```', CHAPTER, re.S)
        self.assertEqual(len(blocks), 1, f'the chapter must print {header} once')
        return blocks[0].strip()

    def test_printed_files_are_the_lab_files(self):
        for name in ['app/Dockerfile', 'workflow/app-delivery.yml']:
            body = (LAB / name).read_text(encoding='utf-8').strip()
            body = '\n'.join(line for line in body.splitlines() if not line.startswith('# 第19章'))
            self.assertEqual(self.printed(f'labs/delivery/{name}'), body.strip(), name)

    def test_names_agree_between_workflow_terraform_and_scripts(self):
        workflow = (LAB / 'workflow/app-delivery.yml').read_text(encoding='utf-8')
        for line in ['ECR_REPOSITORY: cloudbook-app', 'ECS_CLUSTER: cloudbook', 'ECS_SERVICE: cloudbook-app', 'aws-region: ap-northeast-1',
                     'IMAGE_TAG: ${{ github.sha }}', 'environment: production', 'run: bash deploy.sh', 'run: make -C app test']:
            self.assertIn(line, workflow)
        infra = ''.join(p.read_text(encoding='utf-8') for p in (LAB / 'infra').glob('*.tf'))
        self.assertIn('default     = "cloudbook"', infra)
        self.assertIn(':environment:production', infra)
        self.assertIn('name                   = "app"', infra)
        self.assertIn('.name == "app"', (LAB / 'render-taskdef.jq').read_text())

    def test_actions_are_pinned_like_the_book_repository(self):
        ours = (ROOT / '.github/workflows/labs.yml').read_text() + (ROOT / '.github/workflows/deploy.yml').read_text()
        workflow = (LAB / 'workflow/app-delivery.yml').read_text()
        uses = re.findall(r'uses: (\S+@\S+)', workflow)
        self.assertGreaterEqual(len(uses), 3)
        for use in uses:
            self.assertRegex(use, r'@[0-9a-f]{40}$')
        self.assertIn('actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1', ours)


if __name__ == '__main__':
    unittest.main()
