.PHONY: cleanse pre-commit
# https://stackoverflow.com/questions/2145590/what-is-the-purpose-of-phony-in-a-makefile

cleanse:
	@echo "Cleaning up junk files..."
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -delete
	find . -name '*.DS_Store' -delete
	find . -name '.pytest_cache' -exec rm -rf {} +
	@echo "Cleanup complete."

pre-commit:
	@echo "Running pre-commit checks..."
	pre-commit autoupdate
	pre-commit run --all-files
	@echo "Pre-commit checks complete."
