FILE?=
run:
	docker build -t rawbatch .
	docker run --rm -v "$(PWD)":/data rawbatch \
		-c '\
		f="$(FILE)"; \
		b="$${f%.*}"; \
		echo "$$b"; \
		darktable-cli "$$f" "$${b}_dt.jpg" ; \
		darktable-cli "$$f" "$${b}_dt_low.jpg" --width 1200 ; \
		convert "$$f" -auto-level "$${b}_im.jpg" ; \
		convert "$$f" -auto-level -resize 1200x -quality 80 "$${b}_im_low.jpg" ; \
		rawtherapee-cli -a -o "$${b}_rt.jpg" -c "$$f" ; \
		rawtherapee-cli -a -j80 -o "$${b}_rt_low.jpg" -c "$$f" \
		'
