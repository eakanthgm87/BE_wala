#!/usr/bin/env python3
"""
Test deployment from smart directory
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from deployment.deployment_manager import DeploymentManager

def test_smart_deployment():
    print("Testing deployment from smart/ directory")
    print("=" * 50)

    # Check if smart directory exists
    smart_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'smart')
    print(f"Smart directory path: {smart_dir}")
    print(f"Smart directory exists: {os.path.exists(smart_dir)}")

    if not os.path.exists(smart_dir):
        print("ERROR: Smart directory not found!")
        return

    # Change to smart directory
    os.chdir(smart_dir)
    print(f"Changed to directory: {os.getcwd()}")

    # List files in smart directory
    print(f"Files in smart directory: {os.listdir('.')}")

    dm = DeploymentManager()

    # Analyze project
    print("\n1. Analyzing project...")
    config = dm.analyze_project(".")
    print(f"   Frameworks: {config['frameworks']}")
    print(f"   Architecture: {config['architecture']}")

    # Get project info
    print("\n2. Getting project info...")
    info = dm.project_analyzer.get_project_info(".")
    print(f"   Framework: {info['framework']}")
    print(f"   Has Dockerfile: {info['has_dockerfile']}")

    # Generate Dockerfile
    print("\n3. Generating Dockerfile...")
    dockerfile_path = dm.dockerfile_generator.generate_dockerfile(info, ".")
    print(f"   Dockerfile created: {dockerfile_path}")

    # Read the generated Dockerfile
    print("\n4. Generated Dockerfile content:")
    with open(dockerfile_path, 'r') as f:
        content = f.read()
        print("   " + content.replace('\n', '\n   '))

    print("\n5. Testing Docker build...")
    try:
        result = dm.docker_engine.build_image_legacy(".", "test-smart-app")
        print(f"   Build result: {result}")
    except Exception as e:
        print(f"   Build failed: {e}")

if __name__ == "__main__":
    test_smart_deployment()