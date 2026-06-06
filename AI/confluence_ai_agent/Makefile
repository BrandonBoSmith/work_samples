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
	@echo "Activating .venv and installing dependencies"
	@source .venv/bin/activate && \
		echo "Upgrading pip"; \
		pip install pip --upgrade; \
		echo "Installing dependencies"; \
		pip install -r requirements.txt; \
		echo "Ready to go"; \
