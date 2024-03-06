install:
	pip install --upgrade pip &&\
		pip install -r requirements.txt

test:
	python3 harbor-clean.py --project PROJECT_NAME --days 120 --count 4 --user USERNAME --password PASSWORD --url https://testurlharbor 

format:	
	black *.py 

lint:
	pylint --disable=R,C --ignore-patterns=test_.*?py *.py

refactor: format lint
		
toml:
	black .
	flake8
	isort .
