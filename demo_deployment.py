#!/usr/bin/env python3
"""
Simple deployment demo script
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from deployment.deployment_manager import DeploymentManager

def demo_deployment():
    print("ShellMind Deployment Demo")
    print("=" * 40)

    # Create deployment manager
    print("\n1. Initializing deployment system...")
    dm = DeploymentManager()
    print("   [OK] Deployment manager ready")

    # Analyze project
    print("\n2. Analyzing current project...")
    config = dm.analyze_project(".")
    print(f"   [OK] Architecture: {config['architecture']}")
    print(f"   [OK] Services: {len(config['services'])}")
    for service in config['services']:
        print(f"      - {service['name']} on port {service['port']}")

    # Show deployment options
    print("\n3. Deployment options available:")
    print("   • Docker: dm.deploy(target='docker')")
    print("   • Kubernetes: dm.deploy(target='kubernetes')")
    print("   • Cloud: dm.deploy(target='cloud')")

    print("\n4. Destroy options:")
    print("   • Destroy: dm.destroy()")

    print("\n" + "=" * 40)
    print("Demo complete! The deployment system is ready to use.")
    print("Use the commands above to deploy your project.")

if __name__ == "__main__":
    demo_deployment()