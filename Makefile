include .venv/tokens
UPLOAD_URL=http://localhost
TOKEN=${LOCAL_CODECOV_TOKEN}

lint:
	pip install black==22.3.0 isort==5.10.1
	black .
	isort --profile=black .


upload:
	codecovcli --url=${UPLOAD_URL} create-commit --fail-on-error --token=${TOKEN}
	codecovcli --url=${UPLOAD_URL} create-report --fail-on-error --token=${TOKEN}
	pytest --cov=. --cov-context=test
	codecovcli --url=${UPLOAD_URL} --codecov-yml-path=codecov.yml do-upload --plugin pycoverage --plugin compress-pycoverage --fail-on-error --token=${TOKEN} --flag local
	rm .coverage
	rm coverage.codecov.json