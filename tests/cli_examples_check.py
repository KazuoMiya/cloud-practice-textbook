"""Check the AWS CLI examples printed in the book and the lab documents against the API models shipped with the AWS CLI.

Nothing is executed and no credentials or network are used. For every
`aws <service> <operation> ...` in the manuscript, the script looks the
operation up in the service model that the installed AWS CLI carries, and
checks that

- the operation exists,
- every --option is an input of that operation (or a global/pagination option),
- every field named in --query exists somewhere in the operation's response.

Run: python3 tests/cli_examples_check.py   (does nothing when `aws` is not installed)
"""
import gzip
import json
from pathlib import Path
import re
import shlex
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
STOP = {'|', '||', '&&', ';', '>', '>>', '2>&1'}
GLOBAL = {'--query', '--output', '--profile', '--region', '--no-cli-pager', '--no-paginate', '--debug',
          '--endpoint-url', '--no-verify-ssl', '--color', '--no-sign-request', '--cli-input-json'}
PAGINATION = {'--max-items', '--page-size', '--starting-token'}
# Commands implemented by the CLI itself rather than generated from a service API.
NOT_API = {('sso', 'login'), ('sso', 'logout'), ('ecr', 'get-login-password'), ('logs', 'tail'),
           ('cloudformation', 'deploy'), ('cloudformation', 'package'), ('ssm', 'start-session'),
           ('configure', 'sso'), ('configure', 'export-credentials')}
NOT_API_SERVICES = {'s3', 'configure', 'login', 'logout', 'help', '--version'}
MODEL_NAME = {'s3api': 's3'}


def printed_commands():
    for path in sorted([*(ROOT / 'book').glob('*.md'), *(ROOT / 'labs').rglob('*.md'), *(ROOT / 'labs').rglob('*.sh')]):
        text = path.read_text(encoding='utf-8')
        if path.suffix == '.sh':
            text = '```bash\n' + text + '```'
        found = []
        for block in re.findall(r'```bash\n(.*?)```', text, re.S):
            for line in re.sub(r'\\\n\s*', ' ', block).splitlines():
                line = line.strip()
                if line.startswith('aws '):
                    found.append(line)
                found += [m.rstrip(')') for m in re.findall(r'\$\((aws [^\n]*\))\s*$', line)]
        prose = re.sub(r'```.*?```', '', text, flags=re.S)
        found += re.findall(r'`(aws [^`\n]+)`', prose)
        for command in found:
            yield path.name, command


def arguments(command):
    args = []
    for token in shlex.split(command, comments=True)[1:]:
        if token in STOP or token.startswith('>'):
            break
        args.append(token)
    return args


def xform(name):
    """Operation or member name to its command-line spelling, as botocore does it."""
    plural_acronym = re.search(r'[A-Z]{2,}s$', name)   # TargetGroupARNs -> target-group-arns
    if plural_acronym:
        name = name[:plural_acronym.start()] + '-' + plural_acronym.group().lower()
    name = re.sub(r'(.)([A-Z][a-z]+)', r'\1-\2', name)
    return re.sub(r'([a-z0-9])([A-Z])', r'\1-\2', name).lower()


def identifiers(query):
    query = re.sub(r"'[^']*'|`[^`]*`", '', query)
    # Policy documents are plain strings in the model; the CLI decodes them only at run time
    query = re.sub(r'\b(AssumeRolePolicyDocument|PolicyDocument)\b.*', r'\1', query)
    return {m.group(1) for m in re.finditer(r'([A-Za-z_][A-Za-z0-9_]*)(?!\s*[(:A-Za-z0-9_])', query)}


class Models:
    def __init__(self, data):
        self.data, self.cache = data, {}

    @staticmethod
    def read(folder, name):
        for candidate in (folder / f'{name}.json', folder / f'{name}.json.gz'):
            if candidate.is_file():
                raw = gzip.decompress(candidate.read_bytes()) if candidate.suffix == '.gz' else candidate.read_bytes()
                return json.loads(raw)
        return {}

    def service(self, name):
        name = MODEL_NAME.get(name, name)
        if name not in self.cache:
            versions = sorted(p for p in (self.data / name).glob('*') if p.is_dir()) if (self.data / name).is_dir() else []
            if not versions:
                self.cache[name] = None
            else:
                model = self.read(versions[-1], 'service-2')
                model['_paginated'] = set(self.read(versions[-1], 'paginators-1').get('pagination', {}))
                self.cache[name] = model
        return self.cache[name]

    @staticmethod
    def fields(model, shape_name, seen=None):
        seen = set() if seen is None else seen
        if shape_name in seen:
            return set()
        seen.add(shape_name)
        shape, names = model['shapes'][shape_name], set()
        for member, ref in shape.get('members', {}).items():
            names.add(member)
            names |= Models.fields(model, ref['shape'], seen)
        for key in ('member', 'value'):
            if key in shape:
                names |= Models.fields(model, shape[key]['shape'], seen)
        return names


def find_data():
    exe = Path(shutil.which('aws')).resolve()
    for base in (exe.parent, exe.parent.parent):
        for found in sorted(base.glob('**/botocore/data')):
            if (found / 'ec2').is_dir():
                return found
    return None


def problems(models, args):
    """Problems of one API command, or None when it is not an API command."""
    service, operation = args[0], (args[1] if len(args) > 1 else None)
    if service in NOT_API_SERVICES or (service, operation) in NOT_API or operation is None:
        return None
    model = models.service(service)
    if model is None:
        return [f'unknown service: {service}']
    name = next((op for op in model['operations'] if xform(op) == operation), None)
    if name is None:
        return [f'unknown operation: {service} {operation}']
    found = []
    spec = model['operations'][name]
    members = model['shapes'][spec['input']['shape']].get('members', {}) if 'input' in spec else {}
    allowed = GLOBAL | {'--' + xform(m) for m in members} | {'--no-' + xform(m) for m in members}
    if name in model['_paginated']:
        allowed |= PAGINATION
    unknown = [a for a in args[2:] if a.startswith('--') and a not in allowed]
    if unknown:
        found.append('unknown options: ' + ', '.join(unknown))
    if '--query' in args:
        available = Models.fields(model, spec['output']['shape']) if 'output' in spec else set()
        missing = sorted(identifiers(args[args.index('--query') + 1]) - available)
        if missing:
            found.append('--query names fields that are not in the response: ' + ', '.join(missing))
    return found


def self_test(models):
    """The checker must accept a correct command and reject each kind of mistake."""
    cases = [
        ("aws ec2 describe-subnets --filters Name=vpc-id,Values=x --query 'Subnets[].[SubnetId,CidrBlock]'", 0),
        ("aws ec2 describe-subnets --fliters Name=vpc-id,Values=x", 1),
        ("aws ec2 describe-subnets --query 'Subnets[].CidrBlok'", 1),
        ("aws ec2 describe-subnet", 1),
        ("aws ec3 describe-subnets", 1),
        ("aws ec2 describe-nat-gateways --filters Name=vpc-id,Values=x", 1),
        ("aws autoscaling detach-load-balancer-target-groups --auto-scaling-group-name x --target-group-arns y", 0),
    ]
    return [command for command, expected in cases if len(problems(models, arguments(command)) or []) != expected]


def main():
    if not shutil.which('aws'):
        print('aws CLI not installed: nothing checked')
        return 0
    data = find_data()
    if data is None:
        print('FAIL the service models of the installed AWS CLI were not found')
        return 1
    models = Models(data)
    print(f'models: {data}')
    wrong = self_test(models)
    if wrong:
        print('FAIL the checker itself gives the wrong verdict for:', *wrong, sep='\n    ')
        return 1
    checked, queries, skipped, failures, seen = 0, 0, set(), [], set()
    for chapter, command in printed_commands():
        args = arguments(command)
        if not args or (chapter, tuple(args)) in seen:
            continue
        seen.add((chapter, tuple(args)))
        found = problems(models, args)
        if found is None:
            skipped.add(f'{chapter}: aws {" ".join(args[:2])}')
            continue
        checked += 1
        queries += '--query' in args
        failures += [f'{chapter}: {command}\n    {problem}' for problem in found]

    print(f'checked {checked} API commands ({queries} with --query); {len(skipped)} CLI-only commands not checked')
    for line in sorted(skipped):
        print('  not checked:', line)
    for line in failures:
        print('FAIL', line)
    if not checked:
        print('FAIL no command was checked: the extraction is broken')
        return 1
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
