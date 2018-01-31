

jade:
	@echo "\n ---------------------------"
	@echo " * Building flask templates"
	@echo " * Requires NODEJS + jade "
	@echo " ---------------------------\n"

	cd ./templates && node ${NODE_MODULES}/jade/bin/jade.js -P *.jade

    