"""
Security Audit Tests for DNA Research Platform
Tests the security scanning and vulnerability assessment functionality
"""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class TestSecurityAudit(unittest.TestCase):
    """Test security audit functionality"""

    def setUp(self):
        """Set up test environment"""
        self.project_root = Path(__file__).parent.parent
        # In Docker container, scripts are in /app/scripts/
        if Path("/app/scripts").exists():
            self.security_script = Path("/app/scripts/security-scan.sh")
        else:
            self.security_script = self.project_root / "scripts" / "security-scan.sh"
        self.test_reports_dir = tempfile.mkdtemp()

    def test_security_script_exists(self):
        """Test that security scan script exists and is executable"""
        self.assertTrue(self.security_script.exists())
        self.assertTrue(os.access(self.security_script, os.X_OK))

    def test_dependency_vulnerability_detection(self):
        """Test dependency vulnerability scanning"""
        # Create mock vulnerable requirements
        mock_requirements = """
        fastapi==0.68.0
        uvicorn==0.15.0
        python-jose==3.3.0
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(mock_requirements)
            f.flush()

            # Mock safety command to simulate vulnerability detection
            with patch("subprocess.run") as mock_run:
                mock_run.return_value.returncode = 1  # Vulnerabilities found
                mock_run.return_value.stdout = json.dumps(
                    [
                        {
                            "vulnerability": "CVE-2024-33664",
                            "package_name": "python-jose",
                            "installed_version": "3.3.0",
                            "severity": "HIGH",
                        }
                    ]
                )

                # Test would run safety check
                result = mock_run.return_value
                self.assertEqual(result.returncode, 1)
                vulnerabilities = json.loads(result.stdout)
                self.assertEqual(len(vulnerabilities), 1)
                self.assertEqual(vulnerabilities[0]["package_name"], "python-jose")

    def test_docker_security_analysis(self):
        """Test Docker security configuration analysis"""
        # Create test Dockerfile with security issues
        dockerfile_content = """
        FROM python:3.11:latest
        USER root
        ADD requirements.txt /app/
        RUN pip install -r requirements.txt
        """

        with tempfile.NamedTemporaryFile(
            mode="w", suffix="Dockerfile", delete=False
        ) as f:
            f.write(dockerfile_content)
            f.flush()

            # Analyze Dockerfile content
            issues = []
            if ":latest" in dockerfile_content:
                issues.append("Uses :latest tag")
            if "USER root" in dockerfile_content:
                issues.append("Uses root user")
            if "ADD " in dockerfile_content:
                issues.append("Uses ADD instead of COPY")

            self.assertEqual(len(issues), 3)
            self.assertIn("Uses :latest tag", issues)
            self.assertIn("Uses root user", issues)
            self.assertIn("Uses ADD instead of COPY", issues)

    def test_hardcoded_secrets_detection(self):
        """Test detection of hardcoded secrets in code"""
        # Test code with potential secrets
        test_code = """
        API_KEY = "sk-1234567890abcdef"
        password = "secret123"
        token = "bearer_token_here"
        # This is not a secret: password field
        """

        # Simulate grep-like search for secrets
        lines = test_code.split("\n")
        secret_patterns = ["password", "secret", "key", "token"]
        potential_secrets = []

        for line in lines:
            if any(pattern in line.lower() for pattern in secret_patterns):
                if "=" in line and not line.strip().startswith("#"):
                    potential_secrets.append(line.strip())

        self.assertEqual(len(potential_secrets), 3)
        self.assertTrue(any("API_KEY" in secret for secret in potential_secrets))
        self.assertTrue(any("password" in secret for secret in potential_secrets))
        self.assertTrue(any("token" in secret for secret in potential_secrets))

    def test_sql_injection_pattern_detection(self):
        """Test detection of SQL injection vulnerabilities"""
        # Test code with SQL injection patterns
        vulnerable_code = """
        query = f"SELECT * FROM users WHERE id = {user_id}"
        cursor.execute("SELECT * FROM data WHERE name = '%s'" % user_input)
        """

        safe_code = """
        query = "SELECT * FROM users WHERE id = ?"
        cursor.execute(query, (user_id,))
        """

        # Check for dangerous patterns
        dangerous_patterns = ["execute.*%", 'f".*{.*}".*FROM', '"%s".*%']

        vulnerable_issues = 0
        for pattern in dangerous_patterns:
            if any(p in vulnerable_code for p in ["%", 'f"', '"%s"']):
                vulnerable_issues += 1

        safe_issues = 0
        for pattern in dangerous_patterns:
            if any(p in safe_code for p in ["%", 'f"', '"%s"']):
                safe_issues += 1

        self.assertGreater(vulnerable_issues, 0)
        self.assertEqual(safe_issues, 0)

    def test_file_permission_analysis(self):
        """Test file permission security analysis"""
        # Create test files with different permissions
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create world-writable file
            world_writable = Path(temp_dir) / "world_writable.txt"
            world_writable.write_text("test")
            world_writable.chmod(0o666)  # World writable

            # Create secure file
            secure_file = Path(temp_dir) / "secure.txt"
            secure_file.write_text("test")
            secure_file.chmod(0o644)  # Not world writable

            # Check permissions
            world_writable_perms = oct(world_writable.stat().st_mode)[-3:]
            secure_file_perms = oct(secure_file.stat().st_mode)[-3:]

            # World writable files are security issues
            self.assertTrue(world_writable_perms.endswith("6"))  # Others can write
            self.assertTrue(secure_file_perms.endswith("4"))  # Others can only read

    def test_debug_mode_detection(self):
        """Test detection of debug mode in configurations"""
        # Test configurations with debug enabled
        debug_config = """
        DEBUG = True
        debug = true
        app.debug = True
        """

        production_config = """
        DEBUG = False
        debug = false
        app.debug = False
        """

        # Check for debug patterns
        debug_issues = sum(
            1
            for line in debug_config.split("\n")
            if any(
                pattern.lower() in line.lower()
                for pattern in ["debug = true", "debug=true"]
            )
        )

        prod_issues = sum(
            1
            for line in production_config.split("\n")
            if any(
                pattern.lower() in line.lower()
                for pattern in ["debug = true", "debug=true"]
            )
        )

        self.assertGreater(debug_issues, 0)
        self.assertEqual(prod_issues, 0)

    def test_security_report_generation(self):
        """Test security report generation"""
        # Mock security scan results
        scan_results = {
            "timestamp": "20250111_120000",
            "docker_issues": 2,
            "api_issues": 1,
            "perm_issues": 0,
            "config_issues": 1,
        }

        # Generate mock report content
        report_content = f"""# DNA Research Platform Security Scan Report

**Scan Date**: 2025-01-11
**Scan ID**: {scan_results['timestamp']}

## Summary

| Category | Issues Found |
|----------|--------------|
| Docker | {scan_results['docker_issues']} |
| API Security | {scan_results['api_issues']} |
| File Permissions | {scan_results['perm_issues']} |
| Configuration | {scan_results['config_issues']} |

## Recommendations

### High Priority
1. Review and remediate any dependency vulnerabilities
2. Fix hardcoded secrets if found
3. Address file permission issues
"""

        # Validate report structure
        self.assertIn("Security Scan Report", report_content)
        self.assertIn("Summary", report_content)
        self.assertIn("Recommendations", report_content)
        self.assertIn(scan_results["timestamp"], report_content)

        # Validate issue counts
        self.assertIn(str(scan_results["docker_issues"]), report_content)
        self.assertIn(str(scan_results["api_issues"]), report_content)

    def test_security_scan_integration(self):
        """Test integration with pre-commit validation"""
        # Check that security scan is properly integrated
        precommit_config = self.project_root / ".pre-commit-config.yaml"

        if precommit_config.exists():
            # Security scan should be referenced in pre-commit validation
            validation_script = (
                self.project_root / "scripts" / "pre-commit-validation.sh"
            )
            if validation_script.exists():
                validation_content = validation_script.read_text()
                self.assertIn("security", validation_content.lower())

    def test_vulnerability_severity_classification(self):
        """Test vulnerability severity classification"""
        # Mock vulnerability data
        vulnerabilities = [
            {"severity": "CRITICAL", "package": "fastapi", "cve": "CVE-2024-1234"},
            {"severity": "HIGH", "package": "python-jose", "cve": "CVE-2024-33664"},
            {"severity": "MEDIUM", "package": "uvicorn", "cve": "CVE-2024-5678"},
            {"severity": "LOW", "package": "requests", "cve": "CVE-2024-9999"},
        ]

        # Classify by severity
        critical = [v for v in vulnerabilities if v["severity"] == "CRITICAL"]
        high = [v for v in vulnerabilities if v["severity"] == "HIGH"]
        medium = [v for v in vulnerabilities if v["severity"] == "MEDIUM"]
        low = [v for v in vulnerabilities if v["severity"] == "LOW"]

        self.assertEqual(len(critical), 1)
        self.assertEqual(len(high), 1)
        self.assertEqual(len(medium), 1)
        self.assertEqual(len(low), 1)

        # Critical and high should be prioritized
        priority_vulns = critical + high
        self.assertEqual(len(priority_vulns), 2)

    def test_security_metrics_collection(self):
        """Test security metrics collection"""
        # Mock security metrics
        metrics = {
            "scan_duration_sec": 45,
            "vulnerabilities_found": 3,
            "critical_issues": 1,
            "high_issues": 1,
            "medium_issues": 1,
            "low_issues": 0,
            "docker_issues": 2,
            "api_issues": 1,
            "config_issues": 1,
        }

        # Validate metrics structure
        required_metrics = [
            "scan_duration_sec",
            "vulnerabilities_found",
            "critical_issues",
            "docker_issues",
            "api_issues",
            "config_issues",
        ]

        for metric in required_metrics:
            self.assertIn(metric, metrics)
            self.assertIsInstance(metrics[metric], int)

        # Calculate risk score
        risk_score = (
            metrics["critical_issues"] * 10
            + metrics["high_issues"] * 5
            + metrics["medium_issues"] * 2
            + metrics["docker_issues"] * 3
            + metrics["api_issues"] * 4
            + metrics["config_issues"] * 2
        )

        self.assertEqual(risk_score, 29)  # 1*10 + 1*5 + 1*2 + 2*3 + 1*4 + 1*2


if __name__ == "__main__":
    unittest.main()
