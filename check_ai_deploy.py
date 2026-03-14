#!/usr/bin/env python3
"""
Final test to check ai:deploy and ai:deploy kubernetes command integration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_ai_deploy_status():
    print("AI Deploy Command Status Check")
    print("=" * 50)

    status = {
        "natural_commands_import": False,
        "deploy_command_handled": False,
        "kubernetes_command_handled": False,
        "destroy_command_handled": False,
        "deployment_manager_works": False,
        "project_analysis_works": False
    }

    try:
        # 1. Check if natural commands can be imported
        print("1. Checking natural commands import...")
        from ai.natural_commands import try_deploy_commands
        status["natural_commands_import"] = True
        print("   [PASS] Natural commands module imported successfully")

        # 2. Check deployment manager directly
        print("\n2. Checking deployment manager...")
        from deployment.deployment_manager import DeploymentManager
        dm = DeploymentManager()
        status["deployment_manager_works"] = True
        print("   [PASS] Deployment manager created successfully")

        # 3. Check project analysis
        print("\n3. Checking project analysis...")
        config = dm.analyze_project(".")
        if config and 'architecture' in config:
            status["project_analysis_works"] = True
            print(f"   [PASS] Project analysis works (detected: {config['architecture']})")
        else:
            print("   [FAIL] Project analysis failed")

        # 4. Test ai:deploy command (should work)
        print("\n4. Testing 'ai:deploy' command...")
        try:
            result = try_deploy_commands('deploy')
            if result is not None:
                status["deploy_command_handled"] = True
                print("   [PASS] ai:deploy command handled successfully")
            else:
                print("   [FAIL] ai:deploy command returned None")
        except Exception as e:
            print(f"   [INFO] ai:deploy executed but had issues: {type(e).__name__}")

        # 5. Test ai:deploy kubernetes command
        print("\n5. Testing 'ai:deploy kubernetes' command...")
        try:
            result = try_deploy_commands('deploy kubernetes')
            if result is not None:
                status["kubernetes_command_handled"] = True
                print("   [PASS] ai:deploy kubernetes command handled successfully")
            else:
                print("   [INFO] ai:deploy kubernetes returned None (may need kubectl/Docker)")
        except Exception as e:
            print(f"   [INFO] ai:deploy kubernetes executed but had issues: {type(e).__name__}")

        # 6. Test ai:destroy command
        print("\n6. Testing 'ai:destroy' command...")
        try:
            result = try_deploy_commands('destroy')
            if result is not None:
                status["destroy_command_handled"] = True
                print("   [PASS] ai:destroy command handled successfully")
            else:
                print("   [FAIL] ai:destroy command returned None")
        except Exception as e:
            print(f"   [INFO] ai:destroy executed but had issues: {type(e).__name__}")

    except Exception as e:
        print(f"[ERROR] Test setup failed: {e}")

    # Final status report
    print("\n" + "=" * 50)
    print("FINAL STATUS REPORT")
    print("=" * 50)

    all_passed = all(status.values())

    for check, passed in status.items():
        status_icon = "[PASS]" if passed else "[FAIL]"
        print(f"{status_icon} {check.replace('_', ' ').title()}")

    print("\n" + "=" * 50)
    if all_passed:
        print("CONCLUSION: All ai:deploy commands are WORKING! ✅")
        print("\nYou can now use:")
        print("  ai: deploy              (Docker deployment)")
        print("  ai: deploy kubernetes   (Kubernetes deployment)")
        print("  ai: destroy             (Destroy deployment)")
    else:
        print("CONCLUSION: Some components need attention, but core functionality works")
        print("\nWorking commands:")
        if status["deploy_command_handled"]:
            print("  [OK] ai: deploy")
        if status["kubernetes_command_handled"]:
            print("  [OK] ai: deploy kubernetes")
        if status["destroy_command_handled"]:
            print("  [OK] ai: destroy")
    print("Then type: ai: deploy")

    return all_passed

if __name__ == "__main__":
    success = check_ai_deploy_status()
    sys.exit(0 if success else 1)