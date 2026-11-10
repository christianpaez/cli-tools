IMAGE = notion-jekyll
SITE ?= $(HOME)/personal-website
ENV_FILE ?= .env

build:
	docker build -t $(IMAGE) .

export: build
	docker run --rm \
		--env-file "$(ENV_FILE)" \
		-e SITE_DIR=/site \
		-u $(shell id -u):$(shell id -g) \
		-v "$(SITE):/site" \
		$(IMAGE)
