.PHONY: deploy check test destroy demo

deploy:
	sudo containerlab deploy -t lab.clab.yml

check:
	./scripts/check_connectivity.py

test:
	./scripts/test_link_failure.py

destroy:
	sudo containerlab destroy -t lab.clab.yml --cleanup

demo: deploy check test