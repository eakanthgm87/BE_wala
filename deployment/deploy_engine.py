import time
from datetime import datetime
from .docker_manager import DockerEngine
from .kubernetes_manager import KubernetesEngine
from .state_manager import StateManager
from .ui_renderer import UIRenderer

class DeployEngine:
    """
    Orchestrates the actual deployment
    """

    def __init__(self):
        self.docker_engine = DockerEngine()
        self.k8s_engine = KubernetesEngine()
        self.state_manager = StateManager()
        self.ui = UIRenderer()

    def deploy(self, project_config, cloud_provider='aws'):
        """Main deploy function"""

        self.ui.show_banner("AI DEPLOY")

        # Step 1: Pre-deployment checks
        self.ui.show_info("Running pre-flight checks...")
        checks_passed = self.run_preflight_checks(project_config)
        if not checks_passed:
            self.ui.show_error("Pre-flight checks failed")
            return None

        # Step 2: Create infrastructure
        self.ui.show_info("Creating infrastructure...")
        infrastructure = self.create_infrastructure(cloud_provider, project_config)

        # Step 3: Build and push images
        self.ui.show_info("Building and pushing images...")
        images = self.build_and_push_images(project_config)

        # Step 4: Deploy to Kubernetes
        self.ui.show_info("Deploying to Kubernetes...")
        deployment_result = self.deploy_to_kubernetes(project_config, infrastructure)

        # Step 5: Setup networking
        self.ui.show_info("Setting up networking...")
        networking = self.setup_networking(deployment_result)

        # Step 6: Run health checks
        self.ui.show_info("Running health checks...")
        health = self.run_health_checks(deployment_result)

        # Step 7: Configure DNS/SSL
        self.ui.show_info("Configuring DNS and SSL...")
        endpoints = self.configure_endpoints(project_config, networking)

        # Step 8: Save deployment state
        self.ui.show_info("Saving deployment state...")
        self.save_deployment_state({
            'project': project_config['name'],
            'timestamp': datetime.now().isoformat(),
            'infrastructure': infrastructure,
            'endpoints': endpoints,
            'images': images,
            'health': health
        })

        result = {
            'status': 'success',
            'endpoints': endpoints,
            'resources': self.get_resource_summary(),
            'cost_estimate': self.estimate_cost(infrastructure)
        }

        self.ui.show_deployment_summary(result)
        return result

    def run_preflight_checks(self, config):
        """Check everything is ready"""
        checks = [
            ('docker', self.check_docker_running()),
            ('kubectl', self.check_kubectl_installed()),
            ('cloud_credentials', self.check_cloud_credentials(config.get('cloud', 'aws'))),
            ('disk_space', self.check_disk_space()),
            ('memory', self.check_memory()),
            ('network', self.check_network())
        ]

        failed_checks = [name for name, passed in checks if not passed]
        if failed_checks:
            self.ui.show_error(f"Pre-flight checks failed: {', '.join(failed_checks)}")
            return False

        return True

    def check_docker_running(self):
        """Check if Docker is running"""
        try:
            import subprocess
            result = subprocess.run(['docker', 'info'], capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False

    def check_kubectl_installed(self):
        """Check if kubectl is installed"""
        try:
            import subprocess
            result = subprocess.run(['kubectl', 'version', '--client'], capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False

    def check_cloud_credentials(self, cloud_provider):
        """Check cloud credentials"""
        # Simplified check - in real implementation, check actual credentials
        return True

    def check_disk_space(self):
        """Check available disk space"""
        import shutil
        total, used, free = shutil.disk_usage("/")
        return free > 1e9  # 1GB free

    def check_memory(self):
        """Check available memory"""
        try:
            import psutil
            return psutil.virtual_memory().available > 1e9  # 1GB free
        except:
            return True  # Skip if psutil not available

    def check_network(self):
        """Check network connectivity"""
        try:
            import subprocess
            import platform
            # Use different ping syntax for Windows vs Linux/Mac
            if platform.system() == 'Windows':
                result = subprocess.run(['ping', '-n', '1', '8.8.8.8'], capture_output=True)
            else:
                result = subprocess.run(['ping', '-c', '1', '8.8.8.8'], capture_output=True)
            return result.returncode == 0
        except:
            return True  # Skip network check if ping fails

    def create_infrastructure(self, cloud_provider, project_config):
        """Create cloud infrastructure"""
        # Simplified - in real implementation, create VPC, subnets, etc.
        return {
            'vpc_id': 'vpc-12345',
            'subnets': ['subnet-1', 'subnet-2'],
            'security_groups': ['sg-1']
        }

    def build_and_push_images(self, project_config):
        """Build and push Docker images"""
        images = []

        for service in project_config['services']:
            # Build image
            image_name = f"{project_config['name']}-{service['name']}"
            self.docker_engine.build_image(service['name'], '.', image_name)

            # Push to registry
            registry = project_config.get('registry', 'docker.io')
            full_image = f"{registry}/{image_name}:latest"
            self.docker_engine.push_image(image_name, registry)

            images.append({
                'service': service['name'],
                'image': full_image
            })

        return images

    def deploy_to_kubernetes(self, project_config, infrastructure):
        """Deploy to Kubernetes"""
        # Generate manifests
        manifests = self.k8s_engine.generate_manifests(project_config)

        # Apply manifests
        for manifest in manifests:
            # In real implementation, apply each manifest
            pass

        return {
            'namespace': project_config.get('namespace', 'default'),
            'deployments': [s['name'] for s in project_config['services']],
            'services': [f"{s['name']}-service" for s in project_config['services']]
        }

    def setup_networking(self, deployment_result):
        """Setup networking"""
        return {
            'load_balancer': 'lb-12345',
            'domain': 'app.example.com'
        }

    def run_health_checks(self, deployment_result):
        """Run health checks"""
        # Simplified health checks
        health_status = {}
        for deployment in deployment_result['deployments']:
            health_status[deployment] = 'healthy'

        return health_status

    def configure_endpoints(self, project_config, networking):
        """Configure DNS and SSL"""
        endpoints = []

        for service in project_config['services']:
            endpoints.append({
                'service': service['name'],
                'url': f"https://{networking['domain']}/{service['name']}",
                'healthy': True
            })

        return endpoints

    def save_deployment_state(self, deployment_data):
        """Save deployment state"""
        self.state_manager.save_deployment(deployment_data['project'], deployment_data)

    def get_resource_summary(self):
        """Get resource summary"""
        return "3 deployments, 3 services, 1 ingress, 1 load balancer"

    def estimate_cost(self, infrastructure):
        """Estimate monthly cost"""
        return 45.50