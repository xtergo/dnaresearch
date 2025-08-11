#!/usr/bin/env python3
"""
Performance Analysis Script for DNA Research Platform
Analyzes Locust test results and generates performance reports
"""

import csv
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any


class PerformanceAnalyzer:
    """Analyzes performance test results and generates reports"""
    
    def __init__(self, results_dir: str):
        self.results_dir = Path(results_dir)
        self.benchmarks = {
            "health": {"target_p95": 100, "target_rps": 100},
            "gene_search": {"target_p95": 200, "target_rps": 50},
            "variant_interpretation": {"target_p95": 1000, "target_rps": 10},
            "theory_exec": {"target_p95": 30000, "target_rps": 1},
            "researcher_reports": {"target_p95": 2000, "target_rps": 5}
        }
    
    def analyze_csv_results(self, csv_file: Path) -> Dict[str, Any]:
        """Analyze Locust CSV results"""
        stats = {}
        
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['Type'] == 'GET' or row['Type'] == 'POST':
                    endpoint = row['Name']
                    stats[endpoint] = {
                        'requests': int(row['Request Count']),
                        'failures': int(row['Failure Count']),
                        'avg_response_time': float(row['Average Response Time']),
                        'min_response_time': float(row['Min Response Time']),
                        'max_response_time': float(row['Max Response Time']),
                        'p50': float(row['50%']),
                        'p66': float(row['66%']),
                        'p75': float(row['75%']),
                        'p80': float(row['80%']),
                        'p90': float(row['90%']),
                        'p95': float(row['95%']),
                        'p98': float(row['98%']),
                        'p99': float(row['99%']),
                        'p100': float(row['100%']),
                        'rps': float(row['Requests/s']),
                        'failure_rate': float(row['Failure Count']) / float(row['Request Count']) * 100 if int(row['Request Count']) > 0 else 0
                    }
        
        return stats
    
    def categorize_endpoint(self, endpoint: str) -> str:
        """Categorize endpoint for benchmark comparison"""
        if '/health' in endpoint:
            return 'health'
        elif '/genes/search' in endpoint:
            return 'gene_search'
        elif '/interpret' in endpoint:
            return 'variant_interpretation'
        elif '/execute' in endpoint:
            return 'theory_exec'
        elif '/report' in endpoint:
            return 'researcher_reports'
        else:
            return 'other'
    
    def check_benchmarks(self, stats: Dict[str, Any]) -> Dict[str, Dict[str, bool]]:
        """Check if performance meets benchmarks"""
        results = {}
        
        for endpoint, data in stats.items():
            category = self.categorize_endpoint(endpoint)
            if category in self.benchmarks:
                benchmark = self.benchmarks[category]
                results[endpoint] = {
                    'p95_pass': data['p95'] <= benchmark['target_p95'],
                    'rps_pass': data['rps'] >= benchmark['target_rps'],
                    'failure_rate_pass': data['failure_rate'] <= 1.0,  # Max 1% failure rate
                    'category': category,
                    'target_p95': benchmark['target_p95'],
                    'actual_p95': data['p95'],
                    'target_rps': benchmark['target_rps'],
                    'actual_rps': data['rps']
                }
        
        return results
    
    def generate_report(self, scenario_name: str) -> Dict[str, Any]:
        """Generate performance report for a scenario"""
        csv_file = self.results_dir / f"{scenario_name}_stats.csv"
        
        if not csv_file.exists():
            return {"error": f"Results file not found: {csv_file}"}
        
        stats = self.analyze_csv_results(csv_file)
        benchmark_results = self.check_benchmarks(stats)
        
        # Calculate overall metrics
        total_requests = sum(data['requests'] for data in stats.values())
        total_failures = sum(data['failures'] for data in stats.values())
        overall_failure_rate = (total_failures / total_requests * 100) if total_requests > 0 else 0
        
        # Identify bottlenecks
        bottlenecks = []
        for endpoint, results in benchmark_results.items():
            if not results['p95_pass']:
                bottlenecks.append({
                    'endpoint': endpoint,
                    'issue': 'High response time',
                    'actual': f"{results['actual_p95']:.1f}ms",
                    'target': f"{results['target_p95']}ms"
                })
            if not results['rps_pass']:
                bottlenecks.append({
                    'endpoint': endpoint,
                    'issue': 'Low throughput',
                    'actual': f"{results['actual_rps']:.1f} RPS",
                    'target': f"{results['target_rps']} RPS"
                })
        
        return {
            'scenario': scenario_name,
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_requests': total_requests,
                'total_failures': total_failures,
                'overall_failure_rate': overall_failure_rate,
                'endpoints_tested': len(stats)
            },
            'endpoint_stats': stats,
            'benchmark_results': benchmark_results,
            'bottlenecks': bottlenecks,
            'recommendations': self.generate_recommendations(bottlenecks, stats)
        }
    
    def generate_recommendations(self, bottlenecks: List[Dict], stats: Dict[str, Any]) -> List[str]:
        """Generate performance improvement recommendations"""
        recommendations = []
        
        if bottlenecks:
            recommendations.append("Performance issues detected:")
            for bottleneck in bottlenecks:
                recommendations.append(f"- {bottleneck['endpoint']}: {bottleneck['issue']} ({bottleneck['actual']} vs target {bottleneck['target']})")
        
        # Check for specific patterns
        high_latency_endpoints = [ep for ep, data in stats.items() if data['p95'] > 1000]
        if high_latency_endpoints:
            recommendations.append("Consider caching for high-latency endpoints:")
            for ep in high_latency_endpoints:
                recommendations.append(f"- {ep} (P95: {stats[ep]['p95']:.1f}ms)")
        
        low_throughput_endpoints = [ep for ep, data in stats.items() if data['rps'] < 10]
        if low_throughput_endpoints:
            recommendations.append("Consider optimization for low-throughput endpoints:")
            for ep in low_throughput_endpoints:
                recommendations.append(f"- {ep} ({stats[ep]['rps']:.1f} RPS)")
        
        if not recommendations:
            recommendations.append("All performance benchmarks met! 🎉")
        
        return recommendations
    
    def generate_summary_report(self) -> Dict[str, Any]:
        """Generate overall performance summary"""
        scenarios = ['health', 'gene_search', 'theory_exec']
        all_results = {}
        
        for scenario in scenarios:
            result = self.generate_report(scenario)
            if 'error' not in result:
                all_results[scenario] = result
        
        if not all_results:
            return {"error": "No valid test results found"}
        
        # Overall summary
        total_requests = sum(r['summary']['total_requests'] for r in all_results.values())
        total_failures = sum(r['summary']['total_failures'] for r in all_results.values())
        overall_failure_rate = (total_failures / total_requests * 100) if total_requests > 0 else 0
        
        all_bottlenecks = []
        for result in all_results.values():
            all_bottlenecks.extend(result['bottlenecks'])
        
        return {
            'timestamp': datetime.now().isoformat(),
            'overall_summary': {
                'scenarios_tested': len(all_results),
                'total_requests': total_requests,
                'total_failures': total_failures,
                'overall_failure_rate': overall_failure_rate,
                'critical_bottlenecks': len(all_bottlenecks)
            },
            'scenario_results': all_results,
            'critical_issues': all_bottlenecks[:5],  # Top 5 issues
            'platform_status': 'PASS' if overall_failure_rate < 1.0 and len(all_bottlenecks) == 0 else 'NEEDS_ATTENTION'
        }


def main():
    """Main analysis function"""
    if len(sys.argv) < 2:
        print("Usage: python analyze-performance.py <results_directory>")
        sys.exit(1)
    
    results_dir = sys.argv[1]
    analyzer = PerformanceAnalyzer(results_dir)
    
    # Generate summary report
    summary = analyzer.generate_summary_report()
    
    # Save report
    report_file = Path(results_dir) / "performance_summary.json"
    with open(report_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Print summary
    print("\n🚀 DNA Research Platform - Performance Test Results")
    print("=" * 60)
    
    if 'error' in summary:
        print(f"❌ Error: {summary['error']}")
        return
    
    overall = summary['overall_summary']
    print(f"📊 Overall Status: {summary['platform_status']}")
    print(f"🧪 Scenarios Tested: {overall['scenarios_tested']}")
    print(f"📈 Total Requests: {overall['total_requests']:,}")
    print(f"❌ Total Failures: {overall['total_failures']:,}")
    print(f"📉 Failure Rate: {overall['overall_failure_rate']:.2f}%")
    print(f"⚠️  Critical Issues: {overall['critical_bottlenecks']}")
    
    if summary['critical_issues']:
        print("\n🔍 Top Performance Issues:")
        for issue in summary['critical_issues']:
            print(f"  • {issue['endpoint']}: {issue['issue']} ({issue['actual']} vs {issue['target']})")
    
    print(f"\n📋 Detailed report saved to: {report_file}")
    
    # Exit with appropriate code
    sys.exit(0 if summary['platform_status'] == 'PASS' else 1)


if __name__ == "__main__":
    main()