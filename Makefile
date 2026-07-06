.PHONY: help sample dashboard review test lint clean

help:
	@echo "make sample     - regenerate synthetic sample data"
	@echo "make dashboard  - build dashboard.sample.html from sample data"
	@echo "make review     - collect YOUR data + build + open dashboard (macOS)"
	@echo "make test       - run the test suite"
	@echo "make lint       - ruff check + format check"
	@echo "make clean      - remove build output and caches (keeps sample)"

sample:
	python3 sample/build_sample_data.py

dashboard: sample
	python3 build_dashboard.py --data sample/sample_data.json --history-dir sample/history --out dashboard.sample.html

review:
	bash scripts/run_review.sh

test:
	python3 -m pytest -q

lint:
	ruff check .
	ruff format --check .

clean:
	rm -f dashboard.html my_activity_data.json *_activity_data.json review.log
	rm -rf __pycache__ tests/__pycache__ .pytest_cache .ruff_cache
