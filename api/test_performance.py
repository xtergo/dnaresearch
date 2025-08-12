"""
Performance tests for DNA Research Platform API
Tests response times and throughput for critical endpoints
"""

import statistics
import time
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient
from main import app


class TestPerformance:
    """Performance test suite for API endpoints"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def measure_response_time(self, client, method, url, **kwargs):
        """Measure response time for a single request"""
        start_time = time.time()
        response = getattr(client, method.lower())(url, **kwargs)
        end_time = time.time()
        return (end_time - start_time) * 1000, response.status_code

    def run_concurrent_requests(self, client, method, url, num_requests=10, **kwargs):
        """Run concurrent requests and measure performance"""
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(
                    self.measure_response_time, client, method, url, **kwargs
                )
                for _ in range(num_requests)
            ]
            results = [future.result() for future in futures]

        response_times = [result[0] for result in results]
        status_codes = [result[1] for result in results]

        return {
            "response_times": response_times,
            "status_codes": status_codes,
            "avg_response_time": statistics.mean(response_times),
            "p95_response_time": statistics.quantiles(response_times, n=20)[
                18
            ],  # 95th percentile
            "success_rate": sum(1 for code in status_codes if 200 <= code < 300)
            / len(status_codes)
            * 100,
        }

    def test_health_endpoint_performance(self, client):
        """Test health endpoint performance - should be < 100ms P95"""
        results = self.run_concurrent_requests(
            client, "GET", "/health", num_requests=20
        )

        assert (
            results["success_rate"] == 100
        ), f"Health endpoint success rate: {results['success_rate']}%"
        assert (
            results["p95_response_time"] < 100
        ), f"Health P95 response time: {results['p95_response_time']:.1f}ms (target: <100ms)"
        assert (
            results["avg_response_time"] < 50
        ), f"Health avg response time: {results['avg_response_time']:.1f}ms (target: <50ms)"

    def test_gene_search_performance(self, client):
        """Test gene search performance - should be < 200ms P95"""
        search_queries = ["BRCA1", "SHANK3", "autism", "22:51150000-51180000"]

        for query in search_queries:
            results = self.run_concurrent_requests(
                client, "GET", f"/genes/search?query={query}", num_requests=10
            )

            assert (
                results["success_rate"] >= 95
            ), f"Gene search success rate for '{query}': {results['success_rate']}%"
            assert (
                results["p95_response_time"] < 200
            ), f"Gene search P95 for '{query}': {results['p95_response_time']:.1f}ms (target: <200ms)"

    def test_variant_interpretation_performance(self, client):
        """Test variant interpretation performance - should be < 1000ms P95"""
        variant_data = {"variant": "c.185delAG", "vcf_data": None}

        results = self.run_concurrent_requests(
            client, "POST", "/genes/BRCA1/interpret", num_requests=5, json=variant_data
        )

        assert (
            results["success_rate"] >= 90
        ), f"Variant interpretation success rate: {results['success_rate']}%"
        assert (
            results["p95_response_time"] < 1000
        ), f"Variant interpretation P95: {results['p95_response_time']:.1f}ms (target: <1000ms)"

    def test_theory_execution_performance(self, client):
        """Test theory execution performance - should be < 30000ms P95"""
        execution_data = {
            "theory": {
                "id": "theory-001",
                "version": "1.0.0",
                "scope": "autism",
                "criteria": {"genes": ["SHANK3"]},
                "evidence_model": {
                    "priors": 0.1,
                    "likelihood_weights": {"variant_hit": 2.0},
                },
            },
            "vcf_data": "#VCFV4.2\n22\t51150000\t.\tA\tT\t60\tPASS",
            "family_id": "test_family",
        }

        # Only run 3 concurrent requests for heavy operations
        results = self.run_concurrent_requests(
            client,
            "POST",
            "/theories/theory-001/execute",
            num_requests=3,
            json=execution_data,
        )

        assert (
            results["success_rate"] >= 80
        ), f"Theory execution success rate: {results['success_rate']}%"
        assert (
            results["p95_response_time"] < 30000
        ), f"Theory execution P95: {results['p95_response_time']:.1f}ms (target: <30000ms)"

    def test_researcher_report_performance(self, client):
        """Test researcher report performance - should be < 2000ms P95"""
        results = self.run_concurrent_requests(
            client, "GET", "/genes/BRCA1/report", num_requests=5
        )

        assert (
            results["success_rate"] >= 90
        ), f"Researcher report success rate: {results['success_rate']}%"
        assert (
            results["p95_response_time"] < 2000
        ), f"Researcher report P95: {results['p95_response_time']:.1f}ms (target: <2000ms)"

    def test_file_upload_url_performance(self, client):
        """Test file upload URL generation performance"""
        upload_data = {
            "filename": "test_data.vcf",
            "file_type": "vcf",
            "file_size": 10000000,
            "checksum": "abc123def456",
        }

        results = self.run_concurrent_requests(
            client, "POST", "/files/presign", num_requests=10, json=upload_data
        )

        assert (
            results["success_rate"] >= 95
        ), f"File upload URL success rate: {results['success_rate']}%"
        assert (
            results["p95_response_time"] < 500
        ), f"File upload URL P95: {results['p95_response_time']:.1f}ms (target: <500ms)"

    def test_consent_validation_performance(self, client):
        """Test consent validation performance"""
        results = self.run_concurrent_requests(
            client, "GET", "/consent/user_001/validate", num_requests=15
        )

        assert (
            results["success_rate"] >= 95
        ), f"Consent validation success rate: {results['success_rate']}%"
        assert (
            results["p95_response_time"] < 1000
        ), f"Consent validation P95: {results['p95_response_time']:.1f}ms (target: <1000ms)"

    def test_theory_listing_performance(self, client):
        """Test theory listing performance"""
        results = self.run_concurrent_requests(
            client, "GET", "/theories?limit=20&offset=0", num_requests=10
        )

        assert (
            results["success_rate"] >= 95
        ), f"Theory listing success rate: {results['success_rate']}%"
        assert (
            results["p95_response_time"] < 1000
        ), f"Theory listing P95: {results['p95_response_time']:.1f}ms (target: <1000ms)"

    def test_overall_system_load(self, client):
        """Test overall system performance under mixed load"""
        # Simulate realistic mixed workload
        endpoints = [
            ("GET", "/health"),
            ("GET", "/genes/search?query=BRCA1"),
            ("GET", "/genes/BRCA1/report"),
            ("GET", "/theories?limit=10"),
            ("GET", "/consent/user_001/validate"),
        ]

        total_requests = 50
        all_response_times = []
        all_status_codes = []

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for i in range(total_requests):
                method, url = endpoints[i % len(endpoints)]
                future = executor.submit(
                    self.measure_response_time, client, method, url
                )
                futures.append(future)

            for future in futures:
                response_time, status_code = future.result()
                all_response_times.append(response_time)
                all_status_codes.append(status_code)

        success_rate = (
            sum(1 for code in all_status_codes if 200 <= code < 300)
            / len(all_status_codes)
            * 100
        )
        avg_response_time = statistics.mean(all_response_times)
        p95_response_time = statistics.quantiles(all_response_times, n=20)[18]

        assert success_rate >= 95, f"Overall system success rate: {success_rate}%"
        assert (
            p95_response_time < 2000
        ), f"Overall system P95: {p95_response_time:.1f}ms (target: <2000ms)"
        assert (
            avg_response_time < 500
        ), f"Overall system avg: {avg_response_time:.1f}ms (target: <500ms)"

        print("\n🚀 Overall System Performance:")
        print(f"  📊 Success Rate: {success_rate:.1f}%")
        print(f"  ⚡ Average Response Time: {avg_response_time:.1f}ms")
        print(f"  📈 P95 Response Time: {p95_response_time:.1f}ms")
        print(f"  🧪 Total Requests: {total_requests}")


@pytest.mark.performance
class TestThroughput:
    """Throughput tests for high-volume scenarios"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_health_endpoint_throughput(self, client):
        """Test health endpoint can handle high request volume"""
        duration = 10  # seconds
        start_time = time.time()
        request_count = 0

        while time.time() - start_time < duration:
            response = client.get("/health")
            assert response.status_code == 200
            request_count += 1

        rps = request_count / duration
        assert rps >= 50, f"Health endpoint RPS: {rps:.1f} (target: >=50)"
        print(f"Health endpoint throughput: {rps:.1f} RPS")

    def test_gene_search_throughput(self, client):
        """Test gene search throughput"""
        duration = 10
        start_time = time.time()
        request_count = 0
        queries = ["BRCA1", "BRCA2", "SHANK3", "APOE"]

        while time.time() - start_time < duration:
            query = queries[request_count % len(queries)]
            response = client.get(f"/genes/search?query={query}")
            assert response.status_code == 200
            request_count += 1

        rps = request_count / duration
        assert rps >= 20, f"Gene search RPS: {rps:.1f} (target: >=20)"
        print(f"Gene search throughput: {rps:.1f} RPS")
