.PHONY: install test  

install:
	uv sync

# Default test command
test:
	uv run pytest $(ARGS)
