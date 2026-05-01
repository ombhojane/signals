#!/usr/bin/env python3
import subprocess
import json
import sys

def run_az_command(cmd):
    """Run Azure CLI command"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "azure.cli"] + cmd.split(),
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return "", str(e), 1

def check_backend():
    print("\n" + "="*60)
    print("Backend Diagnostic Report")
    print("="*60 + "\n")
    
    # 1. Check if backend container app exists
    print("[1] Checking backend container app...")
    stdout, stderr, code = run_az_command(
        "containerapp show --name signals-backend --resource-group signals-rg --query properties.provisioningState"
    )
    
    if code == 0:
        print(f"✓ Backend app exists: {stdout.strip()}")
    else:
        print(f"✗ Backend app error: {stderr}")
        return False
    
    # 2. Check revisions
    print("\n[2] Checking backend revisions...")
    stdout, stderr, code = run_az_command(
        "containerapp revision list --name signals-backend --resource-group signals-rg --query '[].name'"
    )
    
    if code == 0:
        revisions = json.loads(stdout)
        print(f"✓ Revisions found: {revisions}")
        if not revisions:
            print("⚠ WARNING: No revisions found!")
    else:
        print(f"✗ Error getting revisions: {stderr}")
    
    # 3. Check ingress/FQDN
    print("\n[3] Checking backend URL...")
    stdout, stderr, code = run_az_command(
        "containerapp show --name signals-backend --resource-group signals-rg --query properties.configuration.ingress.fqdn"
    )
    
    if code == 0:
        fqdn = stdout.strip().strip('"')
        url = f"https://{fqdn}"
        print(f"✓ Backend URL: {url}")
    else:
        print(f"✗ Error getting URL: {stderr}")
    
    # 4. Check replica count
    print("\n[4] Checking replica configuration...")
    stdout, stderr, code = run_az_command(
        "containerapp show --name signals-backend --resource-group signals-rg --query properties.template.scale"
    )
    
    if code == 0:
        scale = json.loads(stdout)
        print(f"✓ Scale config: {json.dumps(scale, indent=2)}")
    else:
        print(f"✗ Error getting scale: {stderr}")
    
    # 5. Get logs
    print("\n[5] Checking backend logs (last 30 lines)...")
    stdout, stderr, code = run_az_command(
        "containerapp logs show --name signals-backend --resource-group signals-rg --tail 30"
    )
    
    if code == 0:
        if stdout.strip():
            print("✓ Recent logs:")
            print("-" * 60)
            print(stdout)
            print("-" * 60)
        else:
            print("⚠ No logs available (container may not have started yet)")
    else:
        print(f"✗ Error getting logs: {stderr}")
    
    # 6. Check environment variables
    print("\n[6] Checking environment variables...")
    stdout, stderr, code = run_az_command(
        "containerapp show --name signals-backend --resource-group signals-rg --query properties.template.containers[0].env"
    )
    
    if code == 0:
        env_vars = json.loads(stdout) if stdout.strip() else []
        print(f"✓ Environment variables count: {len(env_vars)}")
        for var in env_vars[:5]:
            if 'value' in var:
                print(f"  - {var.get('name', 'unknown')}: {'***' if len(var['value']) > 20 else var['value']}")
    else:
        print(f"✗ Error getting env vars: {stderr}")
    
    print("\n" + "="*60)
    print("Diagnosis Complete")
    print("="*60 + "\n")

if __name__ == "__main__":
    check_backend()
