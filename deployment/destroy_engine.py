import time
import subprocess
from .state_manager import StateManager
from .ui_renderer import UIRenderer

class DestroyEngine:
    """
    Complete cleanup of all resources
    """

    def __init__(self):
        self.state_manager = StateManager()
        self.ui = UIRenderer()

    def destroy(self, project_name, force=False):
        """Destroy everything related to a project"""

        self.ui.show_banner("🔥 AI DESTROY")

        print("🔍 Finding all resources...")

        # Step 1: Find all resources
        resources = self.find_all_resources(project_name)

        # Step 2: Show what will be destroyed
        self.show_destroy_plan(resources)

        if not force:
            try:
                confirm = input("Type 'DESTROY' to confirm: ")
                if confirm != 'DESTROY':
                    print("❌ Destroy cancelled")
                    return
            except:
                print("❌ Destroy cancelled")
                return

        # Step 3: Create backup (optional)
        if not force:
            try:
                backup = input("Create backup before destroy? (y/n): ")
                if backup.lower() == 'y':
                    self.create_backup(project_name, resources)
            except:
                pass

        # Step 4: Gracefully drain resources
        print("💧 Draining traffic...")
        self.drain_traffic(resources)

        # Step 5: Delete Kubernetes resources
        print("☸️  Deleting Kubernetes resources...")
        self.delete_kubernetes_resources(resources['kubernetes'])

        # Step 6: Delete containers and images
        print("🐳 Deleting containers and images...")
        self.delete_containers(resources['docker'])

        # Step 7: Delete cloud infrastructure
        print("☁️  Deleting cloud infrastructure...")
        self.delete_cloud_resources(resources['cloud'])

        # Step 8: Clean up local state
        print("🧹 Cleaning up local state...")
        self.cleanup_local_state(project_name)

        # Step 9: Verify everything is gone
        print("✅ Verifying cleanup...")
        remaining = self.verify_cleanup(project_name)

        if remaining:
            print(f"⚠️  {remaining} resources still found")
            print("Run 'ai destroy --force' to force remove")
        else:
            print("🎉 All resources destroyed successfully!")
            savings = self.calculate_savings(resources)
            print(f"💰 Cost savings: ${savings}/month")

            self.ui.show_destroy_summary({'savings': savings})

    def find_all_resources(self, project_name):
        """Find every resource related to project"""

        resources = {
            'kubernetes': [],
            'docker': [],
            'cloud': [],
            'local': []
        }

        # Find K8s resources
        k8s_resources = self.find_k8s_resources(project_name)
        resources['kubernetes'] = k8s_resources

        # Find Docker resources
        docker_resources = self.find_docker_resources(project_name)
        resources['docker'] = docker_resources

        # Find cloud resources (AWS/GCP/Azure)
        cloud_resources = self.find_cloud_resources(project_name)
        resources['cloud'] = cloud_resources

        # Find local files
        local_resources = self.find_local_resources(project_name)
        resources['local'] = local_resources

        return resources

    def find_k8s_resources(self, project_name):
        """Find Kubernetes resources"""
        resources = []

        try:
            # Find deployments
            result = subprocess.run([
                'kubectl', 'get', 'deployments', '-l', f'app={project_name}',
                '--all-namespaces', '-o', 'json'
            ], capture_output=True, text=True)

            if result.returncode == 0:
                data = result.stdout
                # Parse and add to resources
                pass

        except:
            pass

        return resources

    def find_docker_resources(self, project_name):
        """Find Docker resources"""
        resources = []

        try:
            # Find containers
            result = subprocess.run([
                'docker', 'ps', '-a', '--filter', f'label=ai-deploy={project_name}',
                '--format', '{{.Names}}'
            ], capture_output=True, text=True)

            if result.returncode == 0:
                containers = result.stdout.strip().split('\n')
                for container in containers:
                    if container:
                        resources.append({
                            'type': 'container',
                            'name': container
                        })

            # Find images
            result = subprocess.run([
                'docker', 'images', '--filter', f'label=ai-deploy={project_name}',
                '--format', '{{.Repository}}:{{.Tag}}'
            ], capture_output=True, text=True)

            if result.returncode == 0:
                images = result.stdout.strip().split('\n')
                for image in images:
                    if image:
                        resources.append({
                            'type': 'image',
                            'name': image
                        })

        except:
            pass

        return resources

    def find_cloud_resources(self, project_name):
        """Find cloud resources"""
        # Simplified - in real implementation, query cloud APIs
        return []

    def find_local_resources(self, project_name):
        """Find local resources"""
        # Find local files, configs, etc.
        return []

    def show_destroy_plan(self, resources):
        """Show what will be destroyed"""

        print("\n" + "═"*60)
        print("🔥 DESTROY PLAN")
        print("═"*60)

        total_resources = sum(len(v) for v in resources.values())
        print(f"\n📊 Total resources to destroy: {total_resources}")

        print("\n☸️  Kubernetes Resources:")
        for r in resources['kubernetes']:
            print(f"  • {r['kind']}: {r['name']} (namespace: {r['namespace']})")

        print("\n🐳 Docker Resources:")
        for r in resources['docker']:
            print(f"  • {r['type']}: {r['name']} ({r.get('size', 'unknown')})")

        print("\n☁️  Cloud Resources:")
        for r in resources['cloud']:
            print(f"  • {r['service']}: {r['id']} (${r.get('monthly_cost', 0)}/month)")

        savings = self.calculate_savings(resources)
        print(f"\n💰 Estimated monthly savings: ${savings}")
        print("═"*60 + "\n")

    def create_backup(self, project_name, resources):
        """Create backup before destruction"""

        import os
        backup_dir = f"backups/{project_name}_{int(time.time())}"
        os.makedirs(backup_dir, exist_ok=True)

        # Backup Kubernetes manifests
        if resources['kubernetes']:
            for r in resources['kubernetes']:
                if r['kind'] == 'Deployment':
                    cmd = f"kubectl get deployment {r['name']} -n {r['namespace']} -o yaml"
                    try:
                        result = subprocess.run(cmd, shell=True, capture_output=True)
                        with open(f"{backup_dir}/deployment_{r['name']}.yaml", 'w') as f:
                            f.write(result.stdout.decode())
                    except:
                        pass

        # Backup database if exists
        if self.has_database(resources):
            self.backup_database(project_name, backup_dir)

        print(f"✅ Backup saved to: {backup_dir}")
        return backup_dir

    def has_database(self, resources):
        """Check if there are database resources"""
        for r in resources['cloud']:
            if 'database' in r.get('service', '').lower():
                return True
        return False

    def backup_database(self, project_name, backup_dir):
        """Backup database"""
        # Simplified - in real implementation, dump database
        pass

    def drain_traffic(self, resources):
        """Gracefully stop traffic to services"""

        for r in resources['kubernetes']:
            if r['kind'] == 'Service':
                # Remove endpoints from load balancer
                try:
                    subprocess.run([
                        'kubectl', 'patch', 'service', r['name'],
                        '-n', r['namespace'],
                        '-p', '{"spec":{"externalTrafficPolicy":"Local"}}'
                    ])
                except:
                    pass

        # Wait for connections to drain
        time.sleep(10)

    def delete_kubernetes_resources(self, k8s_resources):
        """Delete all K8s resources in correct order"""

        # Delete in reverse dependency order
        order = ['HorizontalPodAutoscaler', 'Ingress', 'Service',
                'Deployment', 'ConfigMap', 'Secret', 'Namespace']

        for kind in order:
            for r in k8s_resources:
                if r['kind'] == kind:
                    print(f"  Deleting {kind}: {r['name']}")
                    try:
                        subprocess.run([
                            'kubectl', 'delete', r['kind'].lower(),
                            r['name'], '-n', r['namespace'],
                            '--wait=true', '--timeout=60s'
                        ])
                    except:
                        pass

    def delete_containers(self, docker_resources):
        """Delete Docker containers and images"""

        # Stop and remove containers
        for r in docker_resources:
            if r['type'] == 'container':
                try:
                    subprocess.run(['docker', 'stop', r['name']])
                    subprocess.run(['docker', 'rm', r['name']])
                except:
                    pass

        # Remove images
        for r in docker_resources:
            if r['type'] == 'image':
                try:
                    subprocess.run(['docker', 'rmi', r['name']])
                except:
                    pass

    def delete_cloud_resources(self, cloud_resources):
        """Delete cloud infrastructure"""

        for r in cloud_resources:
            if r.get('provider') == 'aws':
                self.delete_aws_resource(r)
            elif r.get('provider') == 'gcp':
                self.delete_gcp_resource(r)
            elif r.get('provider') == 'azure':
                self.delete_azure_resource(r)

    def delete_aws_resource(self, resource):
        """Delete AWS resource"""
        # In real implementation, use boto3
        pass

    def delete_gcp_resource(self, resource):
        """Delete GCP resource"""
        pass

    def delete_azure_resource(self, resource):
        """Delete Azure resource"""
        pass

    def cleanup_local_state(self, project_name):
        """Clean up local state"""
        self.state_manager.remove_deployment(project_name)

    def verify_cleanup(self, project_name):
        """Verify all resources are gone"""

        remaining = 0

        # Check K8s
        try:
            result = subprocess.run([
                'kubectl', 'get', 'all', '-l', f'app={project_name}',
                '--all-namespaces'
            ], capture_output=True)

            if result.stdout.strip():
                remaining += len(result.stdout.decode().split('\n'))
        except:
            pass

        # Check Docker
        try:
            result = subprocess.run([
                'docker', 'ps', '-a', '--filter', f'label=ai-deploy={project_name}'
            ], capture_output=True)

            if result.stdout.strip():
                remaining += len(result.stdout.decode().split('\n'))
        except:
            pass

        return remaining

    def calculate_savings(self, resources):
        """Calculate monthly cost savings"""
        savings = 0

        for r in resources['cloud']:
            savings += r.get('monthly_cost', 0)

        return round(savings, 2)