from pathlib import Path
import yaml

class KubeYamlGenerator:
    """Generates Kubernetes YAML files for deployment"""

    def generate_manifests(self, project_config):
        """Generate all K8s manifests"""

        manifests = []

        # 1. Namespace
        manifests.append(self.create_namespace(project_config))

        # 2. ConfigMaps
        manifests.extend(self.create_configmaps(project_config))

        # 3. Secrets
        manifests.extend(self.create_secrets(project_config))

        # 4. Deployments
        for service in project_config['services']:
            manifests.append(self.create_deployment(service))
            manifests.append(self.create_service(service))

            # Add HPA if needed
            if service.get('autoscale'):
                manifests.append(self.create_hpa(service))

            # Add PDB if HA required
            if service.get('ha'):
                manifests.append(self.create_pdb(service))

        # 5. Ingress
        manifests.append(self.create_ingress(project_config))

        # 6. Network Policies
        manifests.extend(self.create_network_policies(project_config))

        # 7. Service Monitor (for Prometheus)
        if project_config.get('monitoring'):
            manifests.append(self.create_service_monitor(project_config))

        return manifests

    def create_namespace(self, project_config):
        """Create namespace manifest"""
        return {
            'apiVersion': 'v1',
            'kind': 'Namespace',
            'metadata': {
                'name': project_config.get('namespace', 'default'),
                'labels': {
                    'app': project_config['name'],
                    'managed-by': 'ai-deploy'
                }
            }
        }

    def create_configmaps(self, project_config):
        """Create ConfigMap manifests"""
        configmaps = []

        for service in project_config['services']:
            if service.get('config'):
                configmap = {
                    'apiVersion': 'v1',
                    'kind': 'ConfigMap',
                    'metadata': {
                        'name': f"{service['name']}-config",
                        'namespace': service.get('namespace', 'default')
                    },
                    'data': service['config']
                }
                configmaps.append(configmap)

        return configmaps

    def create_secrets(self, project_config):
        """Create Secret manifests"""
        secrets = []

        for service in project_config['services']:
            if service.get('secrets'):
                secret = {
                    'apiVersion': 'v1',
                    'kind': 'Secret',
                    'metadata': {
                        'name': f"{service['name']}-secret",
                        'namespace': service.get('namespace', 'default')
                    },
                    'type': 'Opaque',
                    'data': service['secrets']  # Should be base64 encoded
                }
                secrets.append(secret)

        return secrets

    def create_deployment(self, service):
        """Create optimized deployment"""

        # Calculate resources based on service type
        resources = self.calculate_resources(service)

        deployment = {
            'apiVersion': 'apps/v1',
            'kind': 'Deployment',
            'metadata': {
                'name': service['name'],
                'namespace': service.get('namespace', 'default'),
                'labels': {
                    'app': service['name'],
                    'managed-by': 'ai-deploy',
                    'version': service.get('version', 'latest')
                }
            },
            'spec': {
                'replicas': service.get('replicas', 3),
                'selector': {
                    'matchLabels': {
                        'app': service['name']
                    }
                },
                'strategy': {
                    'type': 'RollingUpdate',
                    'rollingUpdate': {
                        'maxSurge': '25%',
                        'maxUnavailable': '25%'
                    }
                },
                'template': {
                    'metadata': {
                        'labels': {
                            'app': service['name'],
                            'version': service.get('version', 'latest')
                        },
                        'annotations': {
                            'prometheus.io/scrape': 'true',
                            'prometheus.io/port': str(service['port'])
                        }
                    },
                    'spec': {
                        'containers': [{
                            'name': service['name'],
                            'image': f"{service['image']}:{service.get('version', 'latest')}",
                            'imagePullPolicy': 'Always',
                            'ports': [{
                                'containerPort': service['port'],
                                'name': 'http',
                                'protocol': 'TCP'
                            }],
                            'env': self.create_env_vars(service),
                            'resources': resources,
                            'livenessProbe': {
                                'httpGet': {
                                    'path': '/health',
                                    'port': service['port']
                                },
                                'initialDelaySeconds': 30,
                                'periodSeconds': 10,
                                'timeoutSeconds': 5,
                                'failureThreshold': 3
                            },
                            'readinessProbe': {
                                'httpGet': {
                                    'path': '/ready',
                                    'port': service['port']
                                },
                                'initialDelaySeconds': 5,
                                'periodSeconds': 5,
                                'timeoutSeconds': 3,
                                'successThreshold': 1
                            },
                            'lifecycle': {
                                'preStop': {
                                    'exec': {
                                        'command': ['/bin/sh', '-c', 'sleep 10']
                                    }
                                }
                            }
                        }],
                        'terminationGracePeriodSeconds': 30,
                        'securityContext': {
                            'runAsNonRoot': True,
                            'runAsUser': 1000,
                            'fsGroup': 2000
                        },
                        'affinity': self.create_affinity(service),
                        'tolerations': self.create_tolerations(service)
                    }
                }
            }
        }
        return deployment

    def calculate_resources(self, service):
        """Calculate optimal resources based on service type"""

        base_resources = {
            'requests': {
                'memory': '256Mi',
                'cpu': '250m'
            },
            'limits': {
                'memory': '512Mi',
                'cpu': '500m'
            }
        }

        # Adjust based on service type
        service_type = service.get('type', 'api')
        if service_type == 'database':
            base_resources['requests']['memory'] = '1Gi'
            base_resources['limits']['memory'] = '2Gi'
        elif service_type == 'api':
            base_resources['requests']['memory'] = '512Mi'
            base_resources['limits']['memory'] = '1Gi'
        elif service_type == 'frontend':
            base_resources['requests']['memory'] = '128Mi'
            base_resources['limits']['memory'] = '256Mi'

        return base_resources

    def create_env_vars(self, service):
        """Create environment variables"""
        env_vars = []

        for key, value in service.get('env_vars', {}).items():
            env_vars.append({
                'name': key,
                'value': str(value)
            })

        return env_vars

    def create_affinity(self, service):
        """Create affinity rules"""
        return {}

    def create_tolerations(self, service):
        """Create tolerations"""
        return []

    def create_service(self, service):
        """Create service manifest"""
        svc = {
            'apiVersion': 'v1',
            'kind': 'Service',
            'metadata': {
                'name': f"{service['name']}-service",
                'namespace': service.get('namespace', 'default'),
                'labels': {
                    'app': service['name']
                }
            },
            'spec': {
                'selector': {
                    'app': service['name']
                },
                'ports': [{
                    'protocol': 'TCP',
                    'port': service['port'],
                    'targetPort': service['port'],
                    'name': 'http'
                }],
                'type': service.get('service_type', 'ClusterIP')
            }
        }
        return svc

    def create_hpa(self, service):
        """Create Horizontal Pod Autoscaler"""

        hpa = {
            'apiVersion': 'autoscaling/v2',
            'kind': 'HorizontalPodAutoscaler',
            'metadata': {
                'name': f"{service['name']}-hpa",
                'namespace': service.get('namespace', 'default')
            },
            'spec': {
                'scaleTargetRef': {
                    'apiVersion': 'apps/v1',
                    'kind': 'Deployment',
                    'name': service['name']
                },
                'minReplicas': service.get('min_replicas', 2),
                'maxReplicas': service.get('max_replicas', 10),
                'metrics': [
                    {
                        'type': 'Resource',
                        'resource': {
                            'name': 'cpu',
                            'target': {
                                'type': 'Utilization',
                                'averageUtilization': 70
                            }
                        }
                    },
                    {
                        'type': 'Resource',
                        'resource': {
                            'name': 'memory',
                            'target': {
                                'type': 'Utilization',
                                'averageUtilization': 80
                            }
                        }
                    }
                ],
                'behavior': {
                    'scaleDown': {
                        'stabilizationWindowSeconds': 300,
                        'policies': [{
                            'type': 'Percent',
                            'value': 10,
                            'periodSeconds': 60
                        }]
                    },
                    'scaleUp': {
                        'stabilizationWindowSeconds': 0,
                        'policies': [{
                            'type': 'Percent',
                            'value': 100,
                            'periodSeconds': 60
                        }]
                    }
                }
            }
        }
        return hpa

    def create_pdb(self, service):
        """Create Pod Disruption Budget"""
        pdb = {
            'apiVersion': 'policy/v1',
            'kind': 'PodDisruptionBudget',
            'metadata': {
                'name': f"{service['name']}-pdb",
                'namespace': service.get('namespace', 'default')
            },
            'spec': {
                'minAvailable': '50%',
                'selector': {
                    'matchLabels': {
                        'app': service['name']
                    }
                }
            }
        }
        return pdb

    def create_ingress(self, project_config):
        """Create Ingress manifest"""
        ingress = {
            'apiVersion': 'networking.k8s.io/v1',
            'kind': 'Ingress',
            'metadata': {
                'name': f"{project_config['name']}-ingress",
                'namespace': project_config.get('namespace', 'default'),
                'annotations': {
                    'nginx.ingress.kubernetes.io/rewrite-target': '/',
                    'cert-manager.io/cluster-issuer': 'letsencrypt-prod'
                }
            },
            'spec': {
                'tls': [{
                    'hosts': [project_config.get('domain', 'app.local')],
                    'secretName': f"{project_config['name']}-tls"
                }],
                'rules': [{
                    'host': project_config.get('domain', 'app.local'),
                    'http': {
                        'paths': []
                    }
                }]
            }
        }

        # Add paths for each service
        for service in project_config['services']:
            path = {
                'path': service.get('path', '/'),
                'pathType': 'Prefix',
                'backend': {
                    'service': {
                        'name': f"{service['name']}-service",
                        'port': {
                            'number': service['port']
                        }
                    }
                }
            }
            ingress['spec']['rules'][0]['http']['paths'].append(path)

        return ingress

    def create_network_policies(self, project_config):
        """Create Network Policies"""
        policies = []

        for service in project_config['services']:
            policy = {
                'apiVersion': 'networking.k8s.io/v1',
                'kind': 'NetworkPolicy',
                'metadata': {
                    'name': f"{service['name']}-netpol",
                    'namespace': service.get('namespace', 'default')
                },
                'spec': {
                    'podSelector': {
                        'matchLabels': {
                            'app': service['name']
                        }
                    },
                    'policyTypes': ['Ingress', 'Egress'],
                    'ingress': [{
                        'from': [{
                            'podSelector': {
                                'matchLabels': {
                                    'app': service['name']
                                }
                            }
                        }],
                        'ports': [{
                            'protocol': 'TCP',
                            'port': service['port']
                        }]
                    }],
                    'egress': [{
                        'to': [],
                        'ports': [{
                            'protocol': 'TCP',
                            'port': 53
                        }, {
                            'protocol': 'UDP',
                            'port': 53
                        }]
                    }]
                }
            }
            policies.append(policy)

        return policies

    def create_service_monitor(self, project_config):
        """Create Service Monitor for Prometheus"""
        return {
            'apiVersion': 'monitoring.coreos.com/v1',
            'kind': 'ServiceMonitor',
            'metadata': {
                'name': f"{project_config['name']}-monitor",
                'namespace': project_config.get('namespace', 'default')
            },
            'spec': {
                'selector': {
                    'matchLabels': {
                        'app': project_config['name']
                    }
                },
                'endpoints': [{
                    'port': 'http',
                    'path': '/metrics',
                    'interval': '30s'
                }]
            }
        }

    # Legacy methods for compatibility
    def generate_deployment_yaml(self, image_name="myapp", port=8000, replicas=3, output_path="."):
        """Generate Kubernetes deployment YAML"""
        output_path = Path(output_path)

        # Create service config
        service = {
            'name': 'myapp',
            'image': image_name,
            'port': port,
            'replicas': replicas,
            'version': 'latest',
            'type': 'api'
        }

        deployment = self.create_deployment(service)
        svc = self.create_service(service)

        # Convert to YAML string
        manifests = [deployment, svc]
        yaml_content = ""
        for manifest in manifests:
            yaml_content += yaml.dump(manifest) + "---\n"

        yaml_path = output_path / "deployment.yaml"
        with open(yaml_path, "w") as f:
            f.write(yaml_content)

        return str(yaml_path)

    def generate_service_yaml(self, port=8000, output_path="."):
        """Generate separate service YAML if needed"""
        output_path = Path(output_path)

        service = {
            'name': 'myapp',
            'port': port,
            'service_type': 'LoadBalancer'
        }

        svc = self.create_service(service)

        yaml_path = output_path / "service.yaml"
        with open(yaml_path, "w") as f:
            f.write(yaml.dump(svc))

        return str(yaml_path)