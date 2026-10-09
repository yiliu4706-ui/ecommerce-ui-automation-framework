"""
Enhanced Test Reporter for DemoBlaze Test Framework
Provides comprehensive test execution reporting with metrics and analytics
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import xml.etree.ElementTree as ET


class TestReporter:
    """Enhanced test reporter with metrics and pass/fail rates"""
    
    def __init__(self, reports_dir: str = "reports"):
        """
        Initialize test reporter.
        
        Args:
            reports_dir: Directory to store reports
        """
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(exist_ok=True)
        self.test_start_time = None
        self.test_end_time = None
        
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive test execution report.
        
        Returns:
            Dict containing comprehensive test metrics
        """
        report = {
            "execution_summary": self._get_execution_summary(),
            "test_metrics": self._analyze_test_results(),
            "browser_coverage": self._get_browser_coverage(),
            "performance_metrics": self._get_performance_metrics(),
            "failure_analysis": self._analyze_failures(),
            "timestamp": datetime.now().isoformat(),
            "framework_info": self._get_framework_info()
        }
        
        # Save comprehensive report
        report_file = self.reports_dir / "comprehensive_test_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
            
        # Generate human-readable HTML report
        self._generate_html_summary_report(report)
        
        return report
    
    def _get_execution_summary(self) -> Dict[str, Any]:
        """Get basic execution summary from pytest results"""
        junit_file = self.reports_dir / "junit.xml"
        json_file = self.reports_dir / "test_results.json"
        
        summary = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0,
            "pass_rate": 0.0,
            "execution_time": 0.0,
            "test_files": []
        }
        
        # Try to read from JSON report first (more detailed)
        if json_file.exists():
            summary.update(self._parse_json_report(json_file))
        # Fallback to JUnit XML
        elif junit_file.exists():
            summary.update(self._parse_junit_report(junit_file))
            
        return summary
    
    def _parse_json_report(self, json_file: Path) -> Dict[str, Any]:
        """Parse pytest-json-report results"""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            summary = data.get('summary', {})
            
            total = summary.get('total', 0)
            passed = summary.get('passed', 0) 
            failed = summary.get('failed', 0)
            skipped = summary.get('skipped', 0)
            error = summary.get('error', 0)
            
            pass_rate = (passed / total * 100) if total > 0 else 0
            
            return {
                "total_tests": total,
                "passed": passed,
                "failed": failed,
                "skipped": skipped,
                "errors": error,
                "pass_rate": round(pass_rate, 2),
                "execution_time": data.get('duration', 0),
                "test_files": list(set([test.get('nodeid', '').split('::')[0] 
                                      for test in data.get('tests', [])]))
            }
        except Exception as e:
            print(f"Error parsing JSON report: {e}")
            return {}
    
    def _parse_junit_report(self, junit_file: Path) -> Dict[str, Any]:
        """Parse JUnit XML results as fallback"""
        try:
            tree = ET.parse(junit_file)
            root = tree.getroot()
            
            # Get testsuite element
            testsuite = root if root.tag == 'testsuite' else root.find('testsuite')
            
            if testsuite is not None:
                total = int(testsuite.get('tests', 0))
                failures = int(testsuite.get('failures', 0))
                errors = int(testsuite.get('errors', 0))
                skipped = int(testsuite.get('skipped', 0))
                passed = total - failures - errors - skipped
                execution_time = float(testsuite.get('time', 0))
                
                pass_rate = (passed / total * 100) if total > 0 else 0
                
                return {
                    "total_tests": total,
                    "passed": passed,
                    "failed": failures,
                    "skipped": skipped,
                    "errors": errors,
                    "pass_rate": round(pass_rate, 2),
                    "execution_time": execution_time,
                    "test_files": []
                }
        except Exception as e:
            print(f"Error parsing JUnit XML: {e}")
            
        return {}
    
    def _analyze_test_results(self) -> Dict[str, Any]:
        """Analyze test results for detailed metrics"""
        json_file = self.reports_dir / "test_results.json"
        
        if not json_file.exists():
            return {"categories": {}, "longest_tests": [], "shortest_tests": []}
            
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            tests = data.get('tests', [])
            
            # Categorize tests by module/file
            categories = {}
            test_durations = []
            
            for test in tests:
                nodeid = test.get('nodeid', '')
                duration = test.get('duration', 0)
                outcome = test.get('outcome', 'unknown')
                
                # Extract test category from file path
                if '::' in nodeid:
                    test_file = nodeid.split('::')[0]
                    category = test_file.replace('tests/', '').replace('.py', '')
                    
                    if category not in categories:
                        categories[category] = {
                            "total": 0, "passed": 0, "failed": 0, 
                            "skipped": 0, "avg_duration": 0
                        }
                    
                    categories[category]["total"] += 1
                    categories[category][outcome] += 1
                    
                    test_durations.append({
                        "name": test.get('keywords', {}).get('test', nodeid),
                        "duration": duration,
                        "category": category,
                        "outcome": outcome
                    })
            
            # Calculate average durations for categories
            for category, stats in categories.items():
                category_tests = [t for t in test_durations if t["category"] == category]
                if category_tests:
                    stats["avg_duration"] = sum(t["duration"] for t in category_tests) / len(category_tests)
            
            # Sort tests by duration
            test_durations.sort(key=lambda x: x["duration"], reverse=True)
            
            return {
                "categories": categories,
                "longest_tests": test_durations[:5],
                "shortest_tests": test_durations[-5:]
            }
            
        except Exception as e:
            print(f"Error analyzing test results: {e}")
            return {"categories": {}, "longest_tests": [], "shortest_tests": []}
    
    def _get_browser_coverage(self) -> Dict[str, Any]:
        """Get browser coverage information"""
        # This would be enhanced with actual browser detection from test runs
        return {
            "supported_browsers": ["chrome", "firefox"],
            "tested_browsers": ["chrome"],  # This could be dynamic
            "browser_specific_failures": {}
        }
    
    def _get_performance_metrics(self) -> Dict[str, Any]:
        """Calculate performance metrics"""
        json_file = self.reports_dir / "test_results.json"
        
        if not json_file.exists():
            return {}
            
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            tests = data.get('tests', [])
            durations = [test.get('duration', 0) for test in tests]
            
            if not durations:
                return {}
                
            return {
                "avg_test_duration": sum(durations) / len(durations),
                "max_test_duration": max(durations),
                "min_test_duration": min(durations),
                "total_execution_time": sum(durations),
                "tests_per_minute": len(durations) / (sum(durations) / 60) if sum(durations) > 0 else 0
            }
            
        except Exception as e:
            print(f"Error calculating performance metrics: {e}")
            return {}
    
    def _analyze_failures(self) -> Dict[str, Any]:
        """Analyze test failures for patterns"""
        json_file = self.reports_dir / "test_results.json"
        
        if not json_file.exists():
            return {"failed_tests": [], "common_errors": []}
            
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            tests = data.get('tests', [])
            failed_tests = [test for test in tests if test.get('outcome') == 'failed']
            
            failure_analysis = {
                "failed_tests": [],
                "common_errors": []
            }
            
            error_patterns = {}
            
            for test in failed_tests:
                test_info = {
                    "name": test.get('nodeid', ''),
                    "duration": test.get('duration', 0),
                    "error_message": ""
                }
                
                # Extract error information
                call_info = test.get('call', {})
                if 'longrepr' in call_info:
                    error_msg = call_info['longrepr']
                    test_info["error_message"] = error_msg[:200] + "..." if len(error_msg) > 200 else error_msg
                    
                    # Count error patterns
                    error_key = error_msg.split('\n')[0][:100] if error_msg else "Unknown error"
                    error_patterns[error_key] = error_patterns.get(error_key, 0) + 1
                
                failure_analysis["failed_tests"].append(test_info)
            
            # Sort common errors by frequency
            failure_analysis["common_errors"] = [
                {"error": error, "count": count} 
                for error, count in sorted(error_patterns.items(), key=lambda x: x[1], reverse=True)
            ][:5]
            
            return failure_analysis
            
        except Exception as e:
            print(f"Error analyzing failures: {e}")
            return {"failed_tests": [], "common_errors": []}
    
    def _get_framework_info(self) -> Dict[str, Any]:
        """Get framework and environment information"""
        return {
            "framework": "Selenium + Pytest",
            "python_version": "3.x",
            "test_framework": "DemoBlaze E-commerce Test Suite",
            "report_generated_at": datetime.now().isoformat(),
            "environment": "CI/CD" if os.getenv('CI') else "Local"
        }
    
    def _generate_html_summary_report(self, report_data: Dict[str, Any]) -> None:
        """Generate human-readable HTML summary report"""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>DemoBlaze Test Execution Summary</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; text-align: center; }}
        .summary {{ background: white; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .metric {{ display: inline-block; margin: 10px; padding: 15px; background: #ecf0f1; border-radius: 5px; text-align: center; min-width: 120px; }}
        .passed {{ background: #2ecc71; color: white; }}
        .failed {{ background: #e74c3c; color: white; }}
        .skipped {{ background: #f39c12; color: white; }}
        .performance {{ background: #3498db; color: white; }}
        .failure-details {{ background: #fff; margin: 10px 0; padding: 15px; border-left: 4px solid #e74c3c; }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background: #34495e; color: white; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🧪 DemoBlaze Test Execution Report</h1>
        <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="summary">
        <h2>📊 Execution Summary</h2>
        <div class="metric">
            <strong>Total Tests</strong><br>
            {report_data['execution_summary']['total_tests']}
        </div>
        <div class="metric passed">
            <strong>Passed</strong><br>
            {report_data['execution_summary']['passed']}
        </div>
        <div class="metric failed">
            <strong>Failed</strong><br>
            {report_data['execution_summary']['failed']}
        </div>
        <div class="metric skipped">
            <strong>Skipped</strong><br>
            {report_data['execution_summary']['skipped']}
        </div>
        <div class="metric performance">
            <strong>Pass Rate</strong><br>
            {report_data['execution_summary']['pass_rate']}%
        </div>
        <div class="metric performance">
            <strong>Duration</strong><br>
            {report_data['execution_summary']['execution_time']:.2f}s
        </div>
    </div>
    
    <div class="summary">
        <h2>🎯 Test Categories</h2>
        <table>
            <tr><th>Category</th><th>Total</th><th>Passed</th><th>Failed</th><th>Pass Rate</th><th>Avg Duration</th></tr>
            {self._generate_category_rows(report_data.get('test_metrics', {}).get('categories', {}))}
        </table>
    </div>
    
    <div class="summary">
        <h2>⚡ Performance Metrics</h2>
        {self._generate_performance_section(report_data.get('performance_metrics', {}))}
    </div>
    
    <div class="summary">
        <h2>❌ Failure Analysis</h2>
        {self._generate_failure_section(report_data.get('failure_analysis', {}))}
    </div>
    
    <div class="summary">
        <h2>🔧 Framework Information</h2>
        <p><strong>Framework:</strong> {report_data.get('framework_info', {}).get('framework', 'N/A')}</p>
        <p><strong>Environment:</strong> {report_data.get('framework_info', {}).get('environment', 'N/A')}</p>
        <p><strong>Generated:</strong> {report_data.get('timestamp', 'N/A')}</p>
    </div>
</body>
</html>
        """
        
        # Save HTML report
        html_file = self.reports_dir / "test_execution_summary.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        print(f"📋 Comprehensive test report generated: {html_file}")
    
    def _generate_category_rows(self, categories: Dict[str, Any]) -> str:
        """Generate HTML table rows for test categories"""
        if not categories:
            return "<tr><td colspan='6'>No category data available</td></tr>"
            
        rows = ""
        for category, stats in categories.items():
            total = stats.get('total', 0)
            passed = stats.get('passed', 0)
            failed = stats.get('failed', 0)
            pass_rate = (passed / total * 100) if total > 0 else 0
            avg_duration = stats.get('avg_duration', 0)
            
            rows += f"""
            <tr>
                <td>{category}</td>
                <td>{total}</td>
                <td>{passed}</td>
                <td>{failed}</td>
                <td>{pass_rate:.1f}%</td>
                <td>{avg_duration:.2f}s</td>
            </tr>
            """
        return rows
    
    def _generate_performance_section(self, metrics: Dict[str, Any]) -> str:
        """Generate performance metrics section"""
        if not metrics:
            return "<p>No performance metrics available</p>"
            
        return f"""
        <div class="metric performance">
            <strong>Avg Test Duration</strong><br>
            {metrics.get('avg_test_duration', 0):.2f}s
        </div>
        <div class="metric performance">
            <strong>Tests per Minute</strong><br>
            {metrics.get('tests_per_minute', 0):.1f}
        </div>
        <div class="metric performance">
            <strong>Longest Test</strong><br>
            {metrics.get('max_test_duration', 0):.2f}s
        </div>
        """
    
    def _generate_failure_section(self, failure_data: Dict[str, Any]) -> str:
        """Generate failure analysis section"""
        failed_tests = failure_data.get('failed_tests', [])
        if not failed_tests:
            return "<p>✅ No test failures detected!</p>"
            
        content = "<h3>Failed Tests:</h3>"
        for test in failed_tests[:5]:  # Show top 5 failures
            content += f"""
            <div class="failure-details">
                <strong>{test.get('name', 'Unknown')}</strong><br>
                <small>Duration: {test.get('duration', 0):.2f}s</small><br>
                <em>{test.get('error_message', 'No error details')}</em>
            </div>
            """
        
        return content


def generate_test_execution_report():
    """Standalone function to generate comprehensive test report"""
    reporter = TestReporter()
    report = reporter.generate_comprehensive_report()
    
    print("=" * 60)
    print("🎯 TEST EXECUTION SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {report['execution_summary']['total_tests']}")
    print(f"✅ Passed: {report['execution_summary']['passed']}")
    print(f"❌ Failed: {report['execution_summary']['failed']}")
    print(f"⏭️  Skipped: {report['execution_summary']['skipped']}")
    print(f"📊 Pass Rate: {report['execution_summary']['pass_rate']}%")
    print(f"⏱️  Duration: {report['execution_summary']['execution_time']:.2f}s")
    print("=" * 60)
    
    return report


if __name__ == "__main__":
    generate_test_execution_report()