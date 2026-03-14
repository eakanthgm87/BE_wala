import time

class UIRenderer:
    """Beautiful terminal output for deployment operations"""

    def show_deploy_progress(self, stages):
        """Show animated progress"""

        width = 60
        for stage in stages:
            # Progress bar
            bar = "█" * int(width * stage['progress'])
            bar += "░" * (width - len(bar))

            print(f"\r{stage['name']}: [{bar}] {stage['progress']*100:.0f}%", end="")

            if stage['progress'] == 1:
                print(f" [DONE] {stage.get('message', '')}")

            time.sleep(0.1)

    def show_deployment_summary(self, result):
        """Show beautiful summary"""

        print("\n" + "="*60)
        print("DEPLOYMENT SUCCESSFUL!")
        print("="*60)

        # Endpoints table
        print("\nEndpoints:")
        for endpoint in result.get('endpoints', []):
            print(f"  * {endpoint['service']}: {endpoint['url']} ({'Healthy' if endpoint.get('healthy') else 'Checking'})")

        # Resource summary
        if 'resources' in result:
            print(f"\nResources: {result['resources']}")

        if 'cost_estimate' in result:
            print(f"Monthly cost: ${result['cost_estimate']}")

        print("="*60 + "\n")

    def show_destroy_progress(self, stages):
        """Show destroy progress"""
        for stage in stages:
            print(f"[DESTROY] {stage['name']}: {stage.get('status', 'In progress...')}")
            time.sleep(0.5)

    def show_destroy_summary(self, result):
        """Show destroy summary"""
        print("\n" + "═"*60)
        print("🧹 DESTRUCTION COMPLETE!")
        print("═"*60)

        if 'savings' in result:
            print(f"💰 Monthly savings: ${result['savings']}")

        print("✅ All resources cleaned up")
        print("═"*60 + "\n")

    def show_error(self, error):
        """Show error message"""
        print(f"\n[ERROR] {error}\n")

    def show_warning(self, warning):
        """Show warning message"""
        print(f"\n[WARNING] {warning}\n")

    def show_info(self, info):
        """Show info message"""
        print(f"[INFO] {info}")

    def show_success(self, message):
        """Show success message"""
        print(f"[SUCCESS] {message}")

    def show_spinner(self, message, duration=2):
        """Show a simple spinner"""
        spinner = ['/', '-', '\\', '|']
        for i in range(duration * 4):
            print(f"\r{spinner[i % len(spinner)]} {message}", end="")
            time.sleep(0.1)
        print(f"\r[DONE] {message} complete")

    def show_banner(self, title):
        """Show a banner"""
        width = 60
        print("\n" + "="*width)
        print(f"{' ' * ((width - len(title)) // 2)}{title}")
        print("="*width + "\n")