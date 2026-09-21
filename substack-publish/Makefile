IMAGE = substack-pub

build:
	docker build -t $(IMAGE) .

# make run FILE=post.md
run: build
	docker run --rm \
		-v "$${PWD}:/app" \
		-w /app \
		$(IMAGE) "$${FILE}" $${TITLE:+$${TITLE}}
