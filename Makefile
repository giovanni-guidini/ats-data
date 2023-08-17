include .venv/tokens
UPLOAD_URL=http://localhost:8000
TOKEN=${LOCAL_CODECOV_TOKEN}
STATIC_TOKEN=${LOCAL_CODECOV_STATIC_TOKEN}

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

static-analysis:
	codecovcli --url=${UPLOAD_URL} static-analysis --folders-to-exclude=.venv --token=${STATIC_TOKEN}

label-analysis:
	codecovcli --url=${UPLOAD_URL} label-analysis --base-sha=$(shell git rev-parse HEAD^) --token=${STATIC_TOKEN}


