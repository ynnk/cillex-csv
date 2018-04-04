
.PHONY: build



jade:
	@echo "\n ---------------------------"
	@echo " * Building flask templates"
	@echo " * Requires NODEJS + jade "
	@echo " ---------------------------\n"

	cd ./templates && node ${NODE_MODULES}/jade/bin/jade.js -P *.jade

statics :
	@echo "\n ---------------------------"
	@echo " * Building statics"
	@echo " ---------------------------\n"

	cp -rv ../../botapad/static ./


build : jade statics

run : build
	export APP_DEBUG=true; python cillex.py  --port 5004
