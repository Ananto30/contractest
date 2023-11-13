.PHONY: format
format:
	@echo "Formatting code..."
	@isort contractest
	@black contractest --line-length 89

.PHONY: test
test:
	@echo "Running tests..."
	@python -m contractest.test_service

.PHONY: proxy
proxy:
	@echo "Running proxy..."
	@python -m contractest.proxy