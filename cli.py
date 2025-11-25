#!/usr/bin/env python3
"""
HiveMatrix Helm CLI
Command-line interface for managing services
"""

import sys
import json
import argparse
from pathlib import Path
from app import app
from app.service_manager import ServiceManager


def ensure_services_config():
    """
    Ensure helm_services.json exists with full config.
    Auto-regenerates if missing or outdated.
    """
    helm_services_json = Path(__file__).parent / "helm_services.json"

    if not helm_services_json.exists():
        print("helm_services.json not found, generating...")
        _regenerate_services_json()
        return

    try:
        with open(helm_services_json) as f:
            services = json.load(f)

        # Check if any service is missing required fields
        needs_update = False
        for name, config in services.items():
            if 'path' not in config or 'port' not in config:
                needs_update = True
                break

        if needs_update:
            print("helm_services.json is missing required fields, regenerating...")
            _regenerate_services_json()

    except (json.JSONDecodeError, IOError) as e:
        print(f"Error reading helm_services.json: {e}, regenerating...")
        _regenerate_services_json()


def _regenerate_services_json():
    """Run install_manager.py update-config to regenerate service configs"""
    import subprocess
    helm_dir = Path(__file__).parent
    python_bin = helm_dir / "pyenv" / "bin" / "python"

    if not python_bin.exists():
        python_bin = "python3"
    else:
        python_bin = str(python_bin)

    result = subprocess.run(
        [python_bin, "install_manager.py", "update-config"],
        cwd=helm_dir,
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print("✓ Service configuration regenerated successfully")
    else:
        print(f"Warning: Failed to regenerate service config: {result.stderr}")

def status_command(args):
    """Show status of all services"""
    with app.app_context():
        statuses = ServiceManager.get_all_service_statuses()

        print("\n" + "="*80)
        print("HiveMatrix Service Status")
        print("="*80)

        for service_name, status in statuses.items():
            state = status.get('status', 'unknown')
            health = status.get('health', 'unknown')
            pid = status.get('pid', '-')
            port = status.get('configured_port', '-')

            print(f"\n{service_name.upper()}")
            print(f"  Status:  {state}")
            print(f"  Health:  {health}")
            print(f"  Port:    {port}")
            print(f"  PID:     {pid}")

        print("\n" + "="*80 + "\n")

def start_command(args):
    """Start a service"""
    with app.app_context():
        result = ServiceManager.start_service(args.service, args.mode)

        if result['success']:
            print(f"✓ {result['message']}")
            print(f"  PID: {result.get('pid')}")
            print(f"  Port: {result.get('port')}")
        else:
            print(f"✗ {result['message']}")
            sys.exit(1)

def stop_command(args):
    """Stop a service"""
    with app.app_context():
        result = ServiceManager.stop_service(args.service)

        if result['success']:
            print(f"✓ {result['message']}")
        else:
            print(f"✗ {result['message']}")
            sys.exit(1)

def restart_command(args):
    """Restart a service"""
    with app.app_context():
        result = ServiceManager.restart_service(args.service, args.mode)

        if result['success']:
            print(f"✓ {result['message']}")
        else:
            print(f"✗ {result['message']}")
            sys.exit(1)

def list_command(args):
    """List all configured services"""
    with app.app_context():
        services = ServiceManager.get_all_services()

        print("\nConfigured Services:")
        print("-" * 40)
        for name, config in services.items():
            service_type = config.get('type', 'python')
            port = config.get('port', 'N/A')
            print(f"  {name:15} (type: {service_type:10} port: {port})")
        print()

def main():
    parser = argparse.ArgumentParser(
        description='HiveMatrix Helm CLI - Service Management',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s status                    # Show all service statuses
  %(prog)s list                      # List configured services
  %(prog)s start keycloak            # Start Keycloak
  %(prog)s start core                # Start Core service
  %(prog)s stop nexus                # Stop Nexus service
  %(prog)s restart core --mode prod  # Restart Core in production mode
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Status command
    subparsers.add_parser('status', help='Show status of all services')

    # List command
    subparsers.add_parser('list', help='List all configured services')

    # Start command
    start_parser = subparsers.add_parser('start', help='Start a service')
    start_parser.add_argument('service', help='Service name')
    start_parser.add_argument('--mode', choices=['development', 'production'],
                             default='development', help='Run mode (default: development)')

    # Stop command
    stop_parser = subparsers.add_parser('stop', help='Stop a service')
    stop_parser.add_argument('service', help='Service name')

    # Restart command
    restart_parser = subparsers.add_parser('restart', help='Restart a service')
    restart_parser.add_argument('service', help='Service name')
    restart_parser.add_argument('--mode', choices=['development', 'production'],
                               default='development', help='Run mode (default: development)')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Ensure services.json is properly configured before any command
    ensure_services_config()

    # Route to appropriate command
    commands = {
        'status': status_command,
        'list': list_command,
        'start': start_command,
        'stop': stop_command,
        'restart': restart_command
    }

    commands[args.command](args)

if __name__ == '__main__':
    main()
