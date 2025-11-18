#!/usr/bin/env python3
"""
Ward Security Deployer
Deployment utilities for Ward Security System
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional

class WardDeployer:
    """Ward Security System Deployer"""

    def __init__(self):
        self.package_root = Path(__file__).parent.parent.parent
        self.ward_dir = self.package_root / ".ward"

    def create_deployment_package(self, target_dir: Path) -> bool:
        """Create a deployment package"""
        try:
            # Create deployment directory structure
            deploy_dir = target_dir / "ward-deployment"
            deploy_dir.mkdir(exist_ok=True)

            # Copy .ward directory
            if self.ward_dir.exists():
                shutil.copytree(self.ward_dir, deploy_dir / ".ward")

            # Copy main scripts
            scripts = ["setup-ward.sh", "ward-cli.sh", "ward-shell"]
            for script in scripts:
                source = self.package_root / script
                if source.exists():
                    shutil.copy2(source, deploy_dir)

            # Copy documentation
            for doc_file in ["README.md", "LICENSE", "CHANGELOG.md"]:
                source = self.package_root / doc_file
                if source.exists():
                    shutil.copy2(source, deploy_dir)

            # Create deployment manifest
            manifest = {
                "version": "2.0.0",
                "created_by": "Ward Security Deployer",
                "files": [
                    ".ward/",
                    "setup-ward.sh",
                    "ward-cli.sh",
                    "ward-shell",
                    "README.md"
                ]
            }

            import json
            (deploy_dir / "manifest.json").write_text(
                json.dumps(manifest, indent=2)
            )

            # Create deployment script
            deploy_script = deploy_dir / "deploy.sh"
            deploy_script.write_text("""#!/bin/bash
# Ward Security Deployment Script

set -euo pipefail

echo "Deploying Ward Security System..."

# Run setup
if [[ -x "setup-ward.sh" ]]; then
    ./setup-ward.sh
else
    echo "Error: setup-ward.sh not found or not executable"
    exit 1
fi

# Verify installation
if [[ -x ".ward/ward-cli.sh" ]]; then
    echo "✓ Ward Security deployed successfully"
    echo "Run './ward-cli.sh status' to verify system status"
else
    echo "Error: Ward CLI not found after installation"
    exit 1
fi
""")
            deploy_script.chmod(0o755)

            # Create archive
            archive_name = f"ward-security-{target_dir.name}.tar.gz"
            subprocess.run([
                "tar", "-czf", str(target_dir / archive_name),
                "-C", str(target_dir), "ward-deployment"
            ], check=True)

            print(f"✓ Deployment package created: {target_dir / archive_name}")
            return True

        except Exception as e:
            print(f"Error creating deployment package: {e}", file=sys.stderr)
            return False

    def deploy_to_directory(self, source_package: Path, target_dir: Path) -> bool:
        """Deploy Ward from package to directory"""
        try:
            # Extract package
            if source_package.suffix == ".gz":
                subprocess.run([
                    "tar", "-xzf", str(source_package),
                    "-C", str(target_dir)
                ], check=True)
            else:
                print(f"Unsupported package format: {source_package.suffix}", file=sys.stderr)
                return False

            # Find and run deployment script
            deploy_script = None
            for root, dirs, files in os.walk(target_dir):
                if "deploy.sh" in files:
                    deploy_script = Path(root) / "deploy.sh"
                    break

            if deploy_script and deploy_script.exists():
                result = subprocess.run([str(deploy_script)], cwd=deploy_script.parent, check=False)
                return result.returncode == 0
            else:
                print("Deployment script not found in package", file=sys.stderr)
                return False

        except Exception as e:
            print(f"Error deploying package: {e}", file=sys.stderr)
            return False

    def main(self) -> int:
        """Main deployer entry point"""
        import argparse

        parser = argparse.ArgumentParser(
            prog="ward-deploy",
            description="Deploy Ward Security System"
        )

        subparsers = parser.add_subparsers(dest="command", help="Available commands")

        # Create package command
        create_parser = subparsers.add_parser("create", help="Create deployment package")
        create_parser.add_argument(
            "target_dir",
            help="Directory to create package in"
        )

        # Deploy command
        deploy_parser = subparsers.add_parser("install", help="Install from package")
        deploy_parser.add_argument(
            "package",
            help="Deployment package file"
        )
        deploy_parser.add_argument(
            "target_dir",
            nargs="?",
            default=".",
            help="Target directory (default: current)"
        )

        args = parser.parse_args()

        if not args.command:
            parser.print_help()
            return 1

        if args.command == "create":
            target_dir = Path(args.target_dir)
            if self.create_deployment_package(target_dir):
                return 0
            else:
                return 1

        elif args.command == "install":
            package = Path(args.package)
            target_dir = Path(args.target_dir)
            if self.deploy_to_directory(package, target_dir):
                return 0
            else:
                return 1

        return 1

if __name__ == "__main__":
    sys.exit(WardDeployer().main())