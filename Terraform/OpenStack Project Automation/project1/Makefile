plan:
	@if [ ! -f "nextcloud" ]; then ssh-keygen -t rsa -f nextcloud; fi
	@tofu init
	@tofu plan

apply:
	@tofu apply -auto-approve