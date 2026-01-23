#!/usr/bin/env python3
import os
import sys
import yaml  # type: ignore
import xml.etree.ElementTree as ET
import json
import glob
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

class CoberturaParser:
    def __init__(self, report_path: Path, repo_root: Path):
        self.report_path = report_path
        self.repo_root = repo_root

    def parse(self) -> Dict[str, Any]:
        if not self.report_path.exists():
            raise FileNotFoundError(f"Report missing: {self.report_path}")

        tree = ET.parse(self.report_path)
        root = tree.getroot()

        # Get global rates
        line_rate = float(root.attrib.get("line-rate", 0))
        branch_rate = float(root.attrib.get("branch-rate", 0))

        # Discover source paths
        sources = []
        sources_elem = root.find("sources")
        if sources_elem is not None:
            for s in sources_elem.findall("source"):
                if s.text:
                    sources.append(Path(s.text))

        file_coverage = {}
        for pkg in root.findall(".//package"):
            for cls in pkg.findall(".//class"):
                filename = cls.attrib.get("filename")
                if not filename:
                    continue

                # Normalize path
                resolved_path = self._resolve_path(filename, sources)
                if not resolved_path:
                    continue

                lines = cls.find("lines")
                if lines is None:
                    continue

                total_lines = 0
                covered_lines = 0
                for line in lines.findall("line"):
                    total_lines += 1
                    if int(line.attrib.get("hits", 0)) > 0:
                        covered_lines += 1
                
                file_coverage[str(resolved_path)] = {
                    "total": total_lines,
                    "covered": covered_lines,
                    "rate": covered_lines / total_lines if total_lines > 0 else 1.0
                }

        return {
            "line_rate": line_rate,
            "branch_rate": branch_rate,
            "files": file_coverage
        }

    def _resolve_path(self, filename: str, sources: List[Path]) -> Optional[Path]:
        # filename in Cobertura is often relative to one of the sources
        for source in sources:
            potential = (source / filename).resolve()
            if potential.exists() and str(potential).startswith(str(self.repo_root.resolve())):
                return potential.relative_to(self.repo_root.resolve())
        
        # Try direct relative to repo root
        potential = (self.repo_root / filename).resolve()
        if potential.exists() and str(potential).startswith(str(self.repo_root.resolve())):
            return potential.relative_to(self.repo_root.resolve())
            
        return None

class CoverageCoordinator:
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.artifacts_dir = workspace_root / "artifacts" / "coverage"
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

    def discover_manifests(self) -> List[Dict[str, Any]]:
        manifest_paths = []
        search_dirs = [self.workspace_root, self.workspace_root / "deploy" / "repos"]
        
        exclude_dirs = {".git", "node_modules", "target", "dist", "__pycache__"}

        for start_dir in search_dirs:
            if not start_dir.exists():
                continue
            for root, dirs, files in os.walk(start_dir):
                dirs[:] = [d for d in dirs if d not in exclude_dirs]
                if ".agent" in dirs:
                    manifest_file = Path(root) / ".agent" / "test_manifest.yml"
                    if manifest_file.exists():
                        manifest_paths.append(manifest_file)
        
        manifests = []
        seen_ids = set()
        for mp in manifest_paths:
            with open(mp) as f:
                manifest = yaml.safe_load(f)
                manifest["_path"] = mp
                manifest["_repo_dir"] = mp.parent.parent
                
                repo_id = manifest.get("repo_id")
                if not repo_id:
                    print(f"❌ Missing repo_id in {mp}")
                    sys.exit(1)
                if repo_id in seen_ids:
                    print(f"❌ Duplicate repo_id '{repo_id}' found at {mp}")
                    sys.exit(1)
                seen_ids.add(repo_id)
                manifests.append(manifest)
        
        return manifests

    def validate_repo(self, manifest: Dict[str, Any]) -> Dict[str, Any]:
        repo_id = manifest["repo_id"]
        repo_dir = manifest["_repo_dir"]
        coverage_cfg = manifest.get("coverage", {})
        
        result = {
            "repo_id": repo_id,
            "status": "pass",
            "coverage": {},
            "report_path": None,
            "errors": []
        }

        if not coverage_cfg.get("enabled"):
            result["status"] = "skipped"
            return result

        report_rel_path = coverage_cfg.get("report_path", "artifacts/coverage/coverage.xml")
        report_path = repo_dir / report_rel_path
        result["report_path"] = str(report_path.relative_to(self.workspace_root))

        if not report_path.exists():
            result["status"] = "fail"
            result["errors"].append(f"Missing coverage report: {report_rel_path}")
            return result

        try:
            parser = CoberturaParser(report_path, repo_dir)
            data = parser.parse()
        except Exception as e:
            result["status"] = "fail"
            result["errors"].append(f"Failed to parse Cobertura: {str(e)}")
            return result

        # Check Global Thresholds
        thresholds = coverage_cfg.get("thresholds", {})
        line_req = thresholds.get("line", 0)
        branch_req = thresholds.get("branch", 0)

        actual_line = data["line_rate"]
        actual_branch = data["branch_rate"]

        line_pass = actual_line >= line_req
        branch_pass = actual_branch >= branch_req

        result["coverage"] = {
            "line_pct": actual_line,
            "branch_pct": actual_branch,
            "thresholds": {
                "line": {"required": line_req, "actual": actual_line, "pass": line_pass},
                "branch": {"required": branch_req, "actual": actual_branch, "pass": branch_pass}
            },
            "path_thresholds": []
        }

        if not line_pass:
            result["status"] = "fail"
            result["errors"].append(f"Global line coverage {actual_line:.2%} < {line_req:.2%}")
        if not branch_pass:
            result["status"] = "fail"
            result["errors"].append(f"Global branch coverage {actual_branch:.2%} < {branch_req:.2%}")

        # Check Path Thresholds
        path_thresholds = coverage_cfg.get("path_thresholds", {})
        for pattern, cfg in path_thresholds.items():
            req = cfg.get("line", 0)
            
            # Find files matching pattern relative to repo_dir
            matched_files = []
            for p in repo_dir.glob(pattern):
                if p.is_file():
                    rel_p = p.relative_to(repo_dir)
                    matched_files.append(str(rel_p))

            if not matched_files:
                result["status"] = "fail"
                result["errors"].append(f"Path threshold glob '{pattern}' matched zero files")
                continue

            total_lines = 0
            covered_lines = 0
            for f in matched_files:
                if f in data["files"]:
                    total_lines += data["files"][f]["total"]
                    covered_lines += data["files"][f]["covered"]
            
            actual = covered_lines / total_lines if total_lines > 0 else 1.0
            path_pass = actual >= req
            
            result["coverage"]["path_thresholds"].append({
                "glob": pattern,
                "required": req,
                "actual": actual,
                "pass": path_pass
            })

            if not path_pass:
                result["status"] = "fail"
                result["errors"].append(f"Path coverage for '{pattern}' {actual:.2%} < {req:.2%}")

        return result

    def run(self, requested_repo_ids: Optional[List[str]] = None):
        print(f"🚀 Coverage Coordinator - {datetime.now().isoformat()}")
        manifests = self.discover_manifests()
        
        final_results = []
        for m in manifests:
            repo_id = m["repo_id"]
            if requested_repo_ids and repo_id not in requested_repo_ids:
                continue
            
            print(f"📦 checking {repo_id}...")
            res = self.validate_repo(m)
            final_results.append(res)
            
            if res["status"] == "pass":
                print(f"  ✅ Line: {res['coverage']['line_pct']:.2%}")
            elif res["status"] == "fail":
                print(f"  ❌ FAILED")
                for err in res["errors"]:
                    print(f"     - {err}")

        summary = {
            "generated_at": datetime.now().isoformat(),
            "repos": final_results
        }
        
        summary_path = self.artifacts_dir / "summary.json"
        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n📄 Summary: {summary_path}")
        
        if any(r["status"] == "fail" for r in final_results):
            sys.exit(1)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace-root", default=".")
    parser.add_argument("--repos", nargs="*", help="Specific repo IDs to check")
    args = parser.parse_args()
    
    coordinator = CoverageCoordinator(Path(args.workspace_root).resolve())
    coordinator.run(args.repos)
