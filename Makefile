.PHONY: setup setup-python setup-ui pull-model pull-summarizer pull-models run run-backend run-ui test test-unit test-integration

# Full setup: Python deps + UI deps (run `make pull-models` separately for Ollama)
setup: setup-python setup-ui

setup-python:
	uv sync --all-extras

setup-ui:
	# --legacy-peer-deps works around eslint version conflict in upstream UI repo
	cd ui && npm install --legacy-peer-deps

# Ollama model management (only needed for local models)
pull-model:
	@. .env 2>/dev/null; MODEL=$${MODEL:-ollama:gemma4:26b}; \
	OLLAMA_MODEL=$${MODEL#ollama:}; \
	echo "Pulling $$OLLAMA_MODEL..."; \
	ollama pull $$OLLAMA_MODEL

pull-summarizer:
	@. .env 2>/dev/null; SUMMARIZER_MODEL=$${SUMMARIZER_MODEL:-ollama:gemma4:e4b}; \
	OLLAMA_MODEL=$${SUMMARIZER_MODEL#ollama:}; \
	echo "Pulling $$OLLAMA_MODEL..."; \
	ollama pull $$OLLAMA_MODEL

pull-models: pull-model pull-summarizer

# Run both servers (backend on :2024, UI on :3000)
run:
	@echo "Starting LangGraph dev server and Deep Agents UI..."
	@echo "Backend: http://127.0.0.1:2024"
	@echo "UI:      http://localhost:3000"
	@echo ""
	@echo "In the UI, set:"
	@echo "  Deployment URL: http://127.0.0.1:2024"
	@echo "  Assistant ID:   deep_agent"
	@echo ""
	$(MAKE) run-backend & $(MAKE) run-ui & wait

run-backend:
	uv run langgraph dev --no-browser --config langgraph.json

run-ui:
	cd ui && npm run dev

# Tests
test: test-unit

test-unit:
	uv run pytest tests/ -v -m "not integration"

test-integration:
	uv run pytest tests/ -v -m integration
