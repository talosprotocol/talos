#!/usr/bin/env python3
"""Collect system and environment metadata for performance benchmarks.

Outputs JSON with git SHA, timestamps, hardware specs, Python versions, etc.
This metadata ensures benchmark results are reproducible and comparable.

Usage:
    python scripts/perf/collect_env.py > artifacts/perf/metadata.json
"""

import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def get_git_sha():
    """Get current git commit SHA."""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "unknown"


def get_git_sha_short():
    """Get short git commit SHA."""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--short', 'HEAD'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "unknown"


def get_cpu_info():
    """Get CPU model and core count."""
    system = platform.system()
    
    if system == "Darwin":  # macOS
        try:
            # Get CPU brand
            result = subprocess.run(
                ['sysctl', '-n', 'machdep.cpu.brand_string'],
                capture_output=True,
                text=True,
                check=True
            )
            cpu_model = result.stdout.strip()
            
            # Get core count
            result = subprocess.run(
                ['sysctl', '-n', 'hw.physicalcpu'],
                capture_output=True,
                text=True,
                check=True
            )
            cpu_cores = int(result.stdout.strip())
            
            return cpu_model, cpu_cores
        except subprocess.CalledProcessError:
            pass
    
    elif system == "Linux":
        try:
            # Try reading from /proc/cpuinfo
            with open('/proc/cpuinfo', 'r') as f:
                lines = f.readlines()
                model_name = None
                cores = 0
                for line in lines:
                    if 'model name' in line and not model_name:
                        model_name = line.split(':')[1].strip()
                    if 'processor' in line:
                        cores += 1
                return model_name or "Unknown", cores
        except:
            pass
    
    # Fallback
    return platform.processor() or "Unknown", None


def get_ram_gb():
    """Get total RAM in GB."""
    system = platform.system()
    
    if system == "Darwin":  # macOS
        try:
            result = subprocess.run(
                ['sysctl', '-n', 'hw.memsize'],
                capture_output=True,
                text=True,
                check=True
            )
            bytes_ram = int(result.stdout.strip())
            return round(bytes_ram / (1024**3))
        except subprocess.CalledProcessError:
            pass
    
    elif system == "Linux":
        try:
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    if 'MemTotal' in line:
                        kb = int(line.split()[1])
                        return round(kb / (1024**2))
        except:
            pass
    
    return None


def get_battery_status():
    """Check if running on battery (macOS only)."""
    system = platform.system()
    
    if system == "Darwin":
        try:
            result = subprocess.run(
                ['pmset', '-g', 'batt'],
                capture_output=True,
                text=True,
                check=True
            )
            output = result.stdout
            # Check if "Now drawing from 'Battery Power'"
            return "'Battery Power'" in output or "'Batterie'" in output
        except subprocess.CalledProcessError:
            pass
    
    return None


def get_python_packages():
    """Get versions of key Python dependencies."""
    packages = {}
    
    try:
        import pytest
        packages['pytest'] = pytest.__version__
    except ImportError:
        packages['pytest'] = None
    
    try:
        import cryptography
        packages['cryptography'] = cryptography.__version__
    except ImportError:
        packages['cryptography'] = None
    
    try:
        import pydantic
        packages['pydantic'] = pydantic.__version__
    except ImportError:
        packages['pydantic'] = None
    
    return packages


def main():
    """Collect and output metadata as JSON."""
    cpu_model, cpu_cores = get_cpu_info()
    ram_gb = get_ram_gb()
    battery = get_battery_status()
    packages = get_python_packages()
    
    metadata = {
        "schema_version": "1.0",
        "git_sha": get_git_sha(),
        "git_sha_short": get_git_sha_short(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "os": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "description": f"{platform.system()} {platform.release()}"
        },
        "cpu": {
            "model": cpu_model,
            "cores": cpu_cores,
        },
        "ram_gb": ram_gb,
        "python": {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "packages": packages
        },
        "on_battery": battery,
        "containerized": False,  # TODO: detect if running in container
    }
    
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
