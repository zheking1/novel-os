#!/usr/bin/env python3
"""Sync novel-os-mcp source files to NAS and rebuild."""
import os
import paramiko

NAS_HOST = '${NAS_HOST}'
NAS_USER = 'root'
NAS_PASS = '${NAS_SSH_PASSWORD}'
LOCAL_SRC = r'D:\Project\novels codex\novel-os-mcp\src\novel_os_mcp'
REMOTE_SRC = '/opt/novel-os/novel-os-mcp/src/novel_os_mcp'

FILES_TO_SYNC = [
    'main.py',
    'mcp_core.py',
    'tool_auth.py',
    'deps.py',
    'kb_service.py',
    'multipass.py',
    'p8_services.py',
    'p7_services.py',
    'utils.py',
    'knowledge_service.py',
    'global_settings.py',
    'context_compression.py',
    'character_arc.py',
    'causality.py',
    'novelty.py',
    'pacing.py',
    'style_fingerprint.py',
    'embedding.py',
    'vector.py',
    'degradation.py',
    'cache.py',
    'performance.py',
    'local_service.py',
    'skill_service.py',
]

SYNC_DIRS = ['services', 'tools']

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(NAS_HOST, username=NAS_USER, password=NAS_PASS, timeout=10)
    sftp = ssh.open_sftp()

    # Upload individual files
    for fname in FILES_TO_SYNC:
        local = os.path.join(LOCAL_SRC, fname)
        remote = f"{REMOTE_SRC}/{fname}"
        if os.path.exists(local):
            sftp.put(local, remote)
            print(f"  {fname}")
        else:
            print(f"  SKIP {fname} (not found)")

    # Upload service directories (services/, tools/)
    for dirname in SYNC_DIRS:
        remote_dir = f"{REMOTE_SRC}/{dirname}"
        try:
            sftp.mkdir(remote_dir)
        except OSError:
            pass

        local_dir = os.path.join(LOCAL_SRC, dirname)
        if os.path.isdir(local_dir):
            for fname in os.listdir(local_dir):
                if fname.endswith('.py'):
                    local = os.path.join(local_dir, fname)
                    remote = f"{remote_dir}/{fname}"
                    sftp.put(local, remote)
                    print(f"  {dirname}/{fname}")

    # Remove old services.py if it exists (now replaced by services/ package)
    try:
        sftp.remove(f"{REMOTE_SRC}/services.py")
        print("  removed old services.py")
    except FileNotFoundError:
        pass

    # Also remove backup if exists
    try:
        sftp.remove(f"{REMOTE_SRC}/services_old.py.bak")
    except FileNotFoundError:
        pass

    sftp.close()

    print("\nRebuilding docker...")
    stdin, stdout, stderr = ssh.exec_command(
        'cd /opt/novel-os && docker compose -f docker-compose.yml -f docker-compose.app.example.yml build novel-os-mcp 2>&1',
        timeout=300,
    )
    stdout.channel.set_combine_stderr(True)
    for line in iter(stdout.readline, ''):
        print(line, end='')

    print("\nRestarting container...")
    stdin, stdout, stderr = ssh.exec_command(
        'cd /opt/novel-os && docker compose -f docker-compose.yml -f docker-compose.app.example.yml up -d novel-os-mcp 2>&1',
        timeout=60,
    )
    stdout.channel.set_combine_stderr(True)
    for line in iter(stdout.readline, ''):
        print(line, end='')

    ssh.close()
    print("\nDone!")

if __name__ == '__main__':
    main()
