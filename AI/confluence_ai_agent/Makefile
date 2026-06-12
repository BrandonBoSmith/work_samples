.PHONY: setup

# Create Python virtual environment named .venv
# and setup all requirements
setup:
	@if [ ! -d ".venv" ]; then \
		echo "Creating the virtual environment .venv"; \
		python3 -m venv .venv; \
	else \
		echo ".venv already exists"; \
	fi
	@echo "Upgrading pip"
	@.venv/bin/pip install --upgrade pip
	@echo "Installing dependencies"
	@.venv/bin/pip install -r requirements.txt
	@echo "Ready to go"
