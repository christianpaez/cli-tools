IMAGE := pdf-compress

.PHONY: build compress compress-aggressive text-only split

build:
	docker build -t $(IMAGE) .

compress:
	docker run --rm \
		--user $$(id -u):$$(id -g) \
		-v "$(PWD):/data" \
		$(IMAGE) -c \
		'gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 \
		-dPDFSETTINGS=/ebook -dNOPAUSE -dQUIET -dBATCH \
		-sOutputFile=compressed.pdf "$(FILE)"'

compress-aggressive:
	docker run --rm \
		--user $$(id -u):$$(id -g) \
		-v "$(PWD):/data" \
		$(IMAGE) -c \
		'gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 \
		-dNOPAUSE -dQUIET -dBATCH \
		-dDownsampleColorImages=true -dColorImageResolution=72 \
		-dDownsampleGrayImages=true -dGrayImageResolution=72 \
		-dDownsampleMonoImages=true -dMonoImageResolution=72 \
		-dJPEGQ=40 \
		-sOutputFile=compressed-aggressive.pdf "$(FILE)"'

text-only:
	docker run --rm \
		--user $$(id -u):$$(id -g) \
		-v "$(PWD):/data" \
		$(IMAGE) -c \
		'mutool convert -F text -o text-only.txt "$(FILE)"'

split:
	docker run --rm \
		--user $$(id -u):$$(id -g) \
		-v "$(PWD):/data" \
		$(IMAGE) -c \
		'gs -sDEVICE=pdfwrite \
		-dFirstPage=$(START) -dLastPage=$(END) \
		-dNOPAUSE -dQUIET -dBATCH \
		-sOutputFile="$(OUT)" "$(FILE)"'
