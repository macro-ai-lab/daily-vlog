#!/usr/bin/env python3
"""Generate, audit and package client-aware installers; Python stdlib only."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import zipfile

KIT = Path(__file__).resolve().parents[1]
POLICY = '2026-10-23.1'
VENDOR = '_maintenance/skill-distribution'


def fail(message):
    raise ValueError(message)


def relative(value):
    if not isinstance(value, str) or not re.fullmatch(r'[\w./-]+', value) or PurePosixPath(value).is_absolute() or any(p in ('.', '..') for p in value.split('/')):
        fail('Unsafe relative path: ' + repr(value))
    return value


def read_manifest(repo):
    m = json.loads((repo / 'distribution.json').read_text(encoding='utf-8'))
    if m.get('schema_version') != 1 or m.get('policy_version') != POLICY:
        fail('Unsupported distribution schema/policy')
    if not re.fullmatch(r'[a-z][a-z0-9-]{0,63}', m['name']): fail('Invalid skill name')
    if not re.fullmatch(r'https://github.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', m['repository']): fail('Expected GitHub repository URL')
    if not re.fullmatch(r'v[0-9][A-Za-z0-9_.-]*', m['version']): fail('Invalid release version')
    if Path(m['archive']).name != m['archive'] or not m['archive'].endswith('.zip'): fail('Expected ZIP basename')
    if m.get('clients') != ['codex', 'claude-code'] or m.get('platforms') != ['macos', 'windows-x64']: fail('All four client/OS cases must be declared')
    relative(m['profile'])
    for item in m['include']: relative(item)
    r = m.get('runtime')
    if r:
        if not re.fullmatch(r'[A-Z][A-Z0-9_]*', r['env']): fail('Invalid runtime environment variable')
        for key in ('project_cache', 'user_cache', 'macos_launcher', 'windows_launcher'): relative(r[key])
    return m


def tree_files(folder):
    return sorted((p for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'), key=lambda p: str(p.relative_to(folder)).replace(os.sep, '/'))


def tree_hash(folder):
    h = hashlib.sha256()
    for p in tree_files(folder):
        h.update(str(p.relative_to(folder)).replace(os.sep, '/').encode()); h.update(b'\0'); h.update(p.read_bytes())
    return h.hexdigest()


def rendered(m):
    r = m.get('runtime') or {'env': 'SKILL_RUNTIME', 'project_cache': '.skill-runtime/v1', 'user_cache': m['name'] + '/v1', 'macos_launcher': 'scripts/run.sh', 'windows_launcher': 'scripts/run.ps1'}
    tokens = {'NAME': m['name'], 'SH_RUNTIME': 'true' if m.get('runtime') else 'false', 'PS_RUNTIME': '$true' if m.get('runtime') else '$false', 'RUNTIME_ENV': r['env'], 'PROJECT_CACHE': r['project_cache'], 'USER_CACHE': r['user_cache'], 'SH_LAUNCHER': r['macos_launcher'], 'PROFILE': m['profile']}
    tokens.update({key + '_WIN': value.replace('/', '\\') for key, value in [('PROJECT_CACHE', r['project_cache']), ('USER_CACHE', r['user_cache']), ('PS_LAUNCHER', r['windows_launcher']), ('PROFILE', m['profile'])]})
    files = {}
    for name in ('install.command', 'install-windows.ps1', 'install-windows.cmd'):
        content = (KIT / 'assets' / (name + '.in')).read_text(encoding='utf-8')
        for key, value in tokens.items(): content = content.replace('@' + key + '@', value)
        if re.search(r'@[A-Z_]+@', content): fail('Unexpanded installer template token')
        if name.endswith(('.ps1', '.cmd')): content = content.replace('\r\n', '\n').replace('\n', '\r\n')
        files[name] = (b'\xef\xbb\xbf' if name.endswith('.ps1') else b'') + content.encode()
    return files


def sync(repo):
    m = read_manifest(repo)
    for name, data in rendered(m).items():
        (repo / name).write_bytes(data)
        if name.endswith('.command'): (repo / name).chmod(0o755)
    target = repo / VENDOR
    if target.resolve() != KIT:
        shutil.copytree(KIT, target, dirs_exist_ok=True, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    return m


def files_for_archive(repo, m):
    found = {}
    for item in m['include']:
        target = repo / item
        if not target.exists(): fail('Missing included path: ' + item)
        if target.is_symlink() or getattr(target, 'is_junction', lambda: False)(): fail('Linked package root: ' + item)
        entries = [target] if target.is_file() else target.rglob('*')
        for p in entries:
            rel = p.relative_to(repo)
            if any(n in ('__pycache__', '.DS_Store') for n in rel.parts) or p.suffix == '.pyc': continue
            if p.is_symlink() or getattr(p, 'is_junction', lambda: False)(): fail('Archive source may not contain links/junctions: ' + str(rel))
            if not p.is_file(): continue
            if any(n in ('.git', '.agents', '.claude', '.codex', '.sandbox', 'private', 'outputs', 'work', '.daily-vlog-runtime') for n in rel.parts) or p.name.startswith('.env') or p.name in ('user-overrides.json', 'preferences.md', 'auth.json') or p.suffix in ('.mov', '.MOV', '.mp4'):
                fail('Private/runtime/media file in package: ' + str(rel))
            found[str(rel).replace(os.sep, '/')] = p
    return found


def check(repo, archive=None):
    m = read_manifest(repo)
    for name, expected in rendered(m).items():
        if (repo / name).read_bytes() != expected: fail('Installer drift; run sync: ' + str(repo / name))
    skill = repo / m['name'] / 'SKILL.md'
    if not re.search(r'^name:\s*' + re.escape(m['name']) + r'\s*$', skill.read_text(encoding='utf-8'), re.M): fail('Skill frontmatter/name mismatch')
    if tree_hash(repo / VENDOR) != tree_hash(KIT): fail('Shared maintenance skill is out of sync: ' + str(repo))
    for name in ('README.md', 'INSTALLATION.md', 'COMPATIBILITY.md', 'INSTALLATION-VALIDATION.md', 'AGENTS.md', '.github/workflows/installation.yml'):
        if not (repo / name).is_file(): fail('Missing release contract file: ' + name)
    readme = (repo / 'README.md').read_text(encoding='utf-8')
    if m['version'] not in readme or m['repository'] not in readme: fail('README version/repository does not match manifest')
    ps = (repo / 'install-windows.ps1').read_text(encoding='utf-8-sig')
    if any(s in ps for s in ('HOST_INSTALL_REQUIRED', 'PROJECT_OWNER_MISMATCH', 'WindowsIdentity', 'Get-Acl')): fail('Forbidden account/owner-name installation gate')
    if m.get('runtime'):
        launch = repo / m['name'] / m['runtime']['windows_launcher']
        text = launch.read_text(encoding='utf-8-sig')
        helper = (KIT / 'assets/windows-https.ps1').read_text(encoding='utf-8-sig').strip()
        if helper not in text or 'ARCHIVE_HASH_MISMATCH' not in text: fail('Runtime missing the verified HTTPS fallback/hash contract')
    files = files_for_archive(repo, m)
    if archive:
        with zipfile.ZipFile(archive) as z:
            if z.testzip() is not None: fail('Corrupt ZIP')
            if set(z.namelist()) != set(files): fail('Archive/source inventory mismatch')
            for name, p in files.items():
                if z.read(name) != p.read_bytes(): fail('Stale archive content: ' + name)
            if not ((z.getinfo('install.command').external_attr >> 16) & 0o111): fail('Mac installer lost its executable bit')
    return {'name': m['name'], 'version': m['version'], 'policy': POLICY, 'kit_sha256': tree_hash(KIT), 'files': len(files), 'status': 'passed'}


def package(repo, output):
    result = check(repo)
    files = files_for_archive(repo, read_manifest(repo))
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists(): fail('Output exists; preserve the tested artifact: ' + str(output))
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, p in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = (0o100755 if name.endswith(('.command', '.sh')) else 0o100644) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, p.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    check(repo, output)
    result.update(archive=str(output), sha256=hashlib.sha256(output.read_bytes()).hexdigest())
    return result


def init(repo, name, repository, version, archive):
    if (repo / 'distribution.json').exists(): fail('Existing project manifest is preserved')
    if not (repo / name / 'SKILL.md').is_file(): fail('Create the requested product skill first; init only scaffolds installation')
    if not all((name, repository, version, archive)): fail('init requires name, repository, version and archive')
    for existing in ('README.md', 'INSTALLATION.md', 'AGENTS.md', '.github/workflows/installation.yml'):
        if (repo / existing).exists(): fail('Existing documentation is preserved: ' + existing)
    include = [name, 'README.md', 'INSTALLATION.md', 'COMPATIBILITY.md', 'INSTALLATION-VALIDATION.md', '시작하기.txt', 'install.command', 'install-windows.ps1', 'install-windows.cmd', 'distribution.json', 'AGENTS.md', VENDOR.split('/')[0], '.github', '.gitattributes', '.gitignore']
    m = {'schema_version': 1, 'policy_version': POLICY, 'name': name, 'repository': repository, 'version': version, 'archive': archive, 'clients': ['codex', 'claude-code'], 'platforms': ['macos', 'windows-x64'], 'profile': name + '/preferences.md', 'runtime': None, 'include': include}
    (repo / 'distribution.json').write_text(json.dumps(m, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    replacements = {'@NAME@': name, '@REPOSITORY@': repository, '@VERSION@': version}
    for source, dest in [('README.md.in', 'README.md'), ('INSTALLATION.md.in', 'INSTALLATION.md'), ('AGENTS.md.in', 'AGENTS.md'), ('installation.yml.in', '.github/workflows/installation.yml')]:
        p = repo / dest
        if p.exists(): fail('Existing documentation is preserved: ' + dest)
        text = (KIT / 'assets' / source).read_text(encoding='utf-8')
        for key, value in replacements.items(): text = text.replace(key, value)
        p.parent.mkdir(parents=True, exist_ok=True); p.write_text(text, encoding='utf-8')
    for name_, text in [('COMPATIBILITY.md', '# 검증 상태\n\n네 경우의 설치 코드는 제공하며 실제 실행 결과는 CI와 INSTALLATION-VALIDATION.md에 구분해 기록한다.\n'), ('INSTALLATION-VALIDATION.md', '# 설치 검증\n\n아직 실행하지 않았다. 배포 전에 최종 ZIP의 네 경우 검사와 도구 확인 결과를 기록한다.\n'), ('시작하기.txt', repository + '\nREADME를 읽고 현재 작업 폴더에 설치해줘.\n'), ('.gitattributes', '* text=auto eol=lf\n*.command text eol=lf\n*.sh text eol=lf\n*.ps1 text eol=crlf\n*.cmd text eol=crlf\n'), ('.gitignore', '.DS_Store\n__pycache__/\n*.pyc\n.env*\noutputs/\nprivate/\n')]:
        if not (repo / name_).exists(): (repo / name_).write_text(text, encoding='utf-8')
    sync(repo)
    return check(repo)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=['init', 'sync', 'check', 'package'])
    p.add_argument('--repo', action='append', required=True)
    p.add_argument('--archive'); p.add_argument('--output'); p.add_argument('--require-all', action='store_true')
    p.add_argument('--name'); p.add_argument('--repository'); p.add_argument('--version')
    a = p.parse_args(); repos = [Path(r).resolve() for r in a.repo]
    if a.command != 'check' and len(repos) != 1: p.error('Only check accepts multiple repositories')
    if a.command == 'init': result = init(repos[0], a.name, a.repository, a.version, a.archive)
    elif a.command == 'sync': result = {'name': sync(repos[0])['name'], 'status': 'synchronized'}
    elif a.command == 'package': result = package(repos[0], Path(a.output).resolve())
    else:
        result = [check(r, Path(a.archive).resolve() if a.archive else None) for r in repos]
        if a.require_all:
            registered = {x['repository'] for x in json.loads((KIT / 'references/projects.json').read_text(encoding='utf-8'))['projects']}
            supplied = {read_manifest(r)['repository'] for r in repos}
            if not registered <= supplied: fail('Shared change missing registered projects: ' + ', '.join(sorted(registered - supplied)))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    try: main()
    except (ValueError, KeyError, FileNotFoundError) as exc:
        print('Distribution check failed: ' + str(exc), file=sys.stderr); sys.exit(1)
