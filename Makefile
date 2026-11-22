.PHONY: setup test notebook html clean
NB = notebooks/01_time_management_analysis.ipynb

setup:      ## create a virtual environment and install dependencies
	python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt && pip install -e .

test:       ## run unit + data-integrity tests
	pytest -q

notebook:   ## re-execute the notebook top to bottom (regenerates figures/ and results/tables/)
	jupyter nbconvert --to notebook --execute --inplace $(NB)

html:       ## export an HTML copy of the executed notebook to docs/
	jupyter nbconvert --to html --output-dir docs $(NB)
