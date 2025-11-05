# Makefile for Auth API Test Suite

.PHONY: help install test test-unit test-integration test-e2e test-cov test-html test-watch test-all test-parallel test-resilience test-security test-adversarial test-reset test-isolation

# Default target
help:
	@echo "Auth API Test Suite"
	@echo "==================="
	@echo ""
	@echo "Available commands:"
	@echo "  install       - Install test dependencies"
	@echo "  test          - Run all tests"
	@echo "  test-unit     - Run unit tests only (fast)"
	@echo "  test-integration  - Run integration tests"
	@echo "  test-e2e      - Run E2E tests (requires API running)"
	@echo "  test-resilience - Run chaos & resilience tests"
	@echo "  test-security - Run security & adversarial tests"
	@echo "  test-adversarial - Run JWT forgery & replay attack tests"
	@echo "  test-cov      - Run tests with coverage"
	@echo "  test-html     - Generate HTML coverage report"
	@echo "  test-watch    - Run tests in watch mode"
	@echo "  test-all      - Run all test types with coverage"
	@echo "  test-parallel - Run tests in parallel"
	@echo "  test-reset    - Reset test database (CLEAN STATE)"
	@echo "  test-isolation - Ensure test isolation before running"
	@echo ""
	@echo "Test markers:"
	@echo "  - unit       Fast, mocked tests"
	@echo "  - integration Real DB/Redis tests"
	@echo "  - e2e        Full API tests"
	@echo "  - slow       Tests >5 seconds"

# Install test dependencies
install:
	@echo "Installing test dependencies..."
	pip install --user -q pytest==7.4.4 pytest-asyncio==0.21.1 pytest-mock==3.12.0 pytest-cov==4.1.0 pytest-html==4.1.1 pytest-xdist==3.5.0
	@echo "✅ Dependencies installed"

# Run all tests
test:
	@echo "Running all tests..."
	pytest -v

# Run unit tests only
test-unit:
	@echo "Running unit tests (fast, mocked)..."
	pytest tests/unit/ -v --tb=short
	@echo "✅ Unit tests complete"

# Run integration tests
test-integration:
	@echo "Running integration tests (real DB/Redis)..."
	pytest tests/integration/ -v --tb=short
	@echo "✅ Integration tests complete"

# Run E2E tests
test-e2e:
	@echo "Running E2E tests (full API)..."
	pytest tests/e2e/ -v --tb=short
	@echo "✅ E2E tests complete"

# Run tests with coverage
test-cov:
	@echo "Running tests with coverage..."
	pytest --cov=app --cov-report=term-missing --cov-fail-under=85 -v
	@echo "✅ Coverage report generated"

# Generate HTML coverage report
test-html:
	@echo "Generating HTML coverage report..."
	pytest --cov=app --cov-report=html --cov-fail-under=85
	@echo "✅ HTML report: htmlcov/index.html"

# Run tests in watch mode (requires pytest-watch)
test-watch:
	@echo "Running tests in watch mode..."
	ptw tests/ -- -v

# Run all test types with coverage
test-all:
	@echo "Running full test suite with coverage..."
	pytest --cov=app --cov-report=term-missing --cov-report=html --cov-fail-under=85 -v
	@echo ""
	@echo "✅ Full test suite complete"
	@echo "📊 Coverage report: htmlcov/index.html"

# Run tests in parallel
test-parallel:
	@echo "Running tests in parallel..."
	pytest tests/unit/ tests/integration/ -n auto --cov=app --cov-report=term-missing
	@echo "✅ Parallel tests complete"

# Run chaos & resilience tests
test-resilience:
	@echo "Running chaos & resilience tests..."
	@echo "⚠️  Testing DB/Redis atomicity and failure scenarios..."
	pytest tests/integration/test_resilience.py -v --tb=short
	@echo "✅ Resilience tests complete"

# Run security & adversarial tests
test-security:
	@echo "Running security & adversarial tests..."
	@echo "🔒 Testing JWT forgery, input validation, and replay attacks..."
	pytest tests/unit/test_security_adversarial.py -v --tb=short
	@echo "✅ Security tests complete"

# Run all security-related tests
test-adversarial: test-security
	@echo "✅ Adversarial testing complete"

# Reset test database to clean state (CRITICAL for reproducibility)
test-reset:
	@echo "⚠️  Resetting test database to clean state..."
	docker compose -f docker-compose.test.yml down -v 2>/dev/null || true
	docker compose -f docker-compose.test.yml up -d test-postgres test-redis
	@sleep 3  # Wait for DB to be ready
	@echo "✅ Test database reset and ready"

# Ensure test isolation (clean database before running tests)
test-isolation: test-reset
	@echo "🧪 Test isolation ensured (clean DB/Redis)"
	@echo "Running unit tests (no DB needed)..."
	pytest tests/unit/ -v --tb=short -x
	@echo "✅ Unit tests passed with clean isolation"

# Run specific test file
test-file:
	@if [ -z "$(FILE)" ]; then \
		echo "Usage: make test-file FILE=path/to/test.py"; \
		exit 1; \
	fi
	@echo "Running test file: $(FILE)"
	pytest $(FILE) -v

# Run specific test
test-single:
	@if [ -z "$(TEST)" ]; then \
		echo "Usage: make test-single TEST=path/to/test.py::TestClass::test_method"; \
		exit 1; \
	fi
	@echo "Running test: $(TEST)"
	pytest $(TEST) -v -s

# Run tests by marker
test-marker:
	@if [ -z "$(MARKER)" ]; then \
		echo "Usage: make test-marker MARKER=unit"; \
		echo "Available markers: unit, integration, e2e, slow"; \
		exit 1; \
	fi
	@echo "Running tests with marker: $(MARKER)"
	pytest -m $(MARKER) -v

# Clean test artifacts
clean:
	@echo "Cleaning test artifacts..."
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf __pycache__/
	rm -rf tests/__pycache__/
	rm -rf tests/*/__pycache__/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Clean complete"

# Start test database
test-db-up:
	@echo "Starting test database..."
	docker compose -f docker-compose.test.yml up -d test-postgres test-redis
	@echo "✅ Test database running"

# Stop test database
test-db-down:
	@echo "Stopping test database..."
	docker compose -f docker-compose.test.yml down
	@echo "✅ Test database stopped"

# Reset test database
test-db-reset:
	@echo "Resetting test database..."
	docker compose -f docker-compose.test.yml down -v
	docker compose -f docker-compose.test.yml up -d test-postgres test-redis
	@echo "✅ Test database reset"

# Check test status
test-status:
	@echo "Test Suite Status:"
	@echo "=================="
	@echo ""
	@echo "Test files created:"
	@find tests/ -name "test_*.py" | wc -l | xargs -I {} echo "  - {} test files"
	@echo ""
	@echo "Test directories:"
	@ls -d tests/*/ | sed 's/^/  - /'
	@echo ""
	@echo "Coverage target: 90%+"

# Validate test suite
validate:
	@echo "Validating test suite..."
	@echo ""
	@echo "Checking test structure..."
	@test -f tests/conftest.py && echo "✅ conftest.py exists" || echo "❌ conftest.py missing"
	@test -f pytest.ini && echo "✅ pytest.ini exists" || echo "❌ pytest.ini missing"
	@test -f requirements-dev.txt && echo "✅ requirements-dev.txt exists" || echo "❌ requirements-dev.txt missing"
	@test -d tests/unit && echo "✅ tests/unit/ exists" || echo "❌ tests/unit/ missing"
	@test -d tests/integration && echo "✅ tests/integration/ exists" || echo "❌ tests/integration/ missing"
	@test -d tests/e2e && echo "✅ tests/e2e/ exists" || echo "❌ tests/e2e/ missing"
	@test -d tests/fixtures && echo "✅ tests/fixtures/ exists" || echo "❌ tests/fixtures/ missing"
	@echo ""
	@echo "Checking test files..."
	@test -f tests/unit/test_registration_service.py && echo "✅ registration service tests" || echo "❌ registration service tests missing"
	@test -f tests/unit/test_password_validation_service.py && echo "✅ password validation tests" || echo "❌ password validation tests missing"
	@test -f tests/unit/test_password_reset_service.py && echo "✅ password reset tests" || echo "❌ password reset tests missing"
	@test -f tests/unit/test_email_service.py && echo "✅ email service tests" || echo "❌ email service tests missing"
	@echo ""
	@echo "✅ Test suite validation complete"
