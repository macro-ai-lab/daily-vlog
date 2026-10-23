#!/usr/bin/env python3
"""Test a packaged skill on the current OS, with no agent account or real media."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PureWindowsPath
import platform
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile


def bootstrap_path(env, is_windows):
    if not is_windows:
        return '/usr/bin:/bin:/usr/sbin:/sbin'
    # os.environ is case-insensitive on Windows; dict(os.environ) is not.
    system_root = next((value for key, value in env.items() if key.upper() == 'SYSTEMROOT'), None)
    if not system_root:
        raise ValueError('Windows SystemRoot is unavailable')
    system_root = PureWindowsPath(system_root)
    return ';'.join(map(str, (system_root / 'System32', system_root, system_root / 'System32/WindowsPowerShell/v1.0')))


def run(command, env, work, label, expected=0):
    started = time.monotonic()
    result = subprocess.run(list(map(str, command)), env=env, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=300)
    (work / (label + '.stdout')).write_text(result.stdout, encoding='utf-8')
    (work / (label + '.stderr')).write_text(result.stderr, encoding='utf-8')
    if result.returncode != expected:
        raise RuntimeError(f'{label}: exit {result.returncode}: {result.stderr[-1800:]}')
    return {'step': label, 'exit_code': result.returncode, 'seconds': round(time.monotonic() - started, 2)}, result


def execute(archive, client, work, report_path):
    is_windows = platform.system() == 'Windows'
    if platform.system() not in ('Windows', 'Darwin'): raise ValueError('Native Windows or macOS required; no WSL/Linux substitution')
    bundle = work / '배포 ZIP'; bundle.mkdir(parents=True)
    with zipfile.ZipFile(archive) as z: z.extractall(bundle)
    m = json.loads((bundle / 'distribution.json').read_text(encoding='utf-8'))
    name = m['name']; runtime = m.get('runtime')
    report = {'name': name, 'version': m['version'], 'os': platform.system(), 'client': client, 'archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(), 'frontend_session': 'not_run', 'agent_image_view': 'not_run', 'ui_account_actions': 'not_run', 'scopes': [], 'status': 'running'}
    env = dict(os.environ)
    for key in ('AI_SKILL_CLIENT', 'DAILY_VLOG_RUNTIME', 'DAILY_VLOG_PROFILE'): env.pop(key, None)
    if runtime: env.pop(runtime['env'], None)
    # The harness has Python; the product bootstrap does not inherit it.
    env['PATH'] = bootstrap_path(env, is_windows)
    report['bootstrap_python_on_path'] = shutil.which('python.exe' if is_windows else 'python3', path=env['PATH']) is not None
    env.update(CODEX_HOME=str(work / 'Codex 개인 설정'), CLAUDE_CONFIG_DIR=str(work / 'Claude 개인 설정'))
    cfg = Path(env['CLAUDE_CONFIG_DIR' if client == 'claude-code' else 'CODEX_HOME'])
    profile = cfg / m['profile']; profile.parent.mkdir(parents=True, exist_ok=True)
    profile_data = (json.dumps({'version': 1, 'revision': 0, 'instructions': {}, 'defaults': {}, 'history': []}) if profile.suffix == '.json' else 'isolated personal instruction fixture').encode()
    profile.write_bytes(profile_data)
    verified_runtime = None
    for scope in ('project', 'user'):
        project = work / (scope + ' 작업 폴더'); project.mkdir()
        step_env = dict(env)
        if runtime and scope == 'user': step_env[runtime['env']] = str(verified_runtime)
        if is_windows:
            install = ['powershell.exe', '-NoLogo', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', bundle / 'install-windows.ps1', '-Client', client]
            install += ['-ProjectPath', project] if scope == 'project' else ['-UserScope']
        else:
            install = ['bash', bundle / 'install.command', '--client', client]
            install += ['--project', project] if scope == 'project' else ['--user']
        record = {'scope': scope, 'runtime_mode': 'empty-cache' if scope == 'project' and runtime else ('reused-isolated-cache' if runtime else 'not_required'), 'steps': []}
        step, _ = run(install, step_env, work, scope + '-install'); record['steps'].append(step)
        target = ((project / ('.claude' if client == 'claude-code' else '.agents')) if scope == 'project' else cfg) / 'skills' / name
        if not (target / 'SKILL.md').is_file(): raise AssertionError('Skill missing after installation')
        marker = target.parent / ('.' + name + '-install')
        if marker.read_text(encoding='utf-8').splitlines() != ['skill-install-v1', client, scope]: raise AssertionError('Wrong persistent installation context')
        step, _ = run(install, step_env, work, scope + '-identical-retry'); record['steps'].append(step)
        if profile.read_bytes() != profile_data: raise AssertionError('Private profile was changed')
        if runtime:
            verified_runtime = project / runtime['project_cache'] if scope == 'project' else verified_runtime
            launcher = (['powershell.exe', '-NoLogo', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', target / runtime['windows_launcher']] if is_windows else ['bash', target / runtime['macos_launcher']])
            step, result = run(launcher + ['doctor'], step_env, work, scope + '-new-process-doctor'); record['steps'].append(step)
            doctor = json.loads(result.stdout.lstrip('\ufeff'))
            if doctor['installation']['client'] != client or doctor['installation']['scope'] != scope: raise AssertionError('New process chose another client/scope')
            if Path(doctor['installation']['profile']).resolve() != profile.resolve(): raise AssertionError('New process chose another profile')
            reports = sorted((verified_runtime / 'checks').glob('*/installation-check.json'))
            if not reports: raise AssertionError('No real smoke report')
            smoke = json.loads(reports[-1].read_text(encoding='utf-8'))
            if smoke['status'] != 'passed' or smoke['agent_image_view'] != 'not_checked': raise AssertionError('Unexpected smoke status')
            preview = Path(smoke['preview'])
            if not preview.is_file() or preview.stat().st_size == 0: raise AssertionError('Missing preview')
            report['preview'] = str(preview)
        # A packaged installation may not overwrite a user's modification.
        original = (target / 'SKILL.md').read_bytes()
        (target / 'SKILL.md').write_bytes(original + b'\nfixture modification\n')
        failed = subprocess.run(list(map(str, install)), env=step_env, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=30)
        if not failed.returncode or 'EXISTING_SKILL_DIFFERS' not in (failed.stderr + failed.stdout) or (target / 'SKILL.md').read_bytes() != original + b'\nfixture modification\n': raise AssertionError('Modified installation was overwritten or not refused')
        (target / 'SKILL.md').write_bytes(original)
        record['modified_skill_preserved'] = True
        report['scopes'].append(record)
    if profile.read_bytes() != profile_data: raise AssertionError('Private profile changed')
    report['private_profile_preserved'] = True
    report['status'] = 'passed'
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive', required=True); p.add_argument('--client', choices=['codex', 'claude-code'], required=True)
    p.add_argument('--report', required=True); p.add_argument('--work-directory')
    a = p.parse_args()
    archive = Path(a.archive).resolve(); report = Path(a.report).resolve()
    try:
        if a.work_directory:
            work = Path(a.work_directory).resolve(); work.mkdir(parents=True, exist_ok=False)
            result = execute(archive, a.client, work, report)
        else:
            with tempfile.TemporaryDirectory(prefix='skill-install-') as td: result = execute(archive, a.client, Path(td), report)
    except Exception as exc:
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(json.dumps({'status': 'failed', 'os': platform.system(), 'client': a.client, 'archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(), 'error': str(exc)}, ensure_ascii=False, indent=2), encoding='utf-8')
        raise
    print(json.dumps({'name': result['name'], 'os': result['os'], 'client': result['client'], 'status': result['status'], 'frontend_session': result['frontend_session']}))


if __name__ == '__main__': main()
