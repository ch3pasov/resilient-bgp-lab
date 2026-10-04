.PHONY: deploy check test test-unit destroy demo

deploy:
	sudo containerlab deploy -t lab.clab.yml

check:
	./scripts/check_connectivity.py

test:
	./scripts/test_link_failure.py

test-unit:
	python3 -B -m unittest discover -s tests -p 'test_*.py'

destroy:
	sudo containerlab destroy -t lab.clab.yml --cleanup

demo: deploy check test