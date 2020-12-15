pdf_src = rapport
pdf_dest = rapport-ALGOREP
template = https://raw.githubusercontent.com/Wandmalfarbe/pandoc-latex-template/master/eisvogel.tex
config ?= config/basic.yaml

all: launch

env:
	if [ ! -d "env" ]; then \
		(python -m venv env; . env/bin/activate; pip install -r requirements.txt) \
	fi

launch: env
	(. env/bin/activate; ./main.sh $(config))

pdf:
	pandoc $(pdf_src).md --standalone --toc --toc-depth 2 -f markdown --template=$(template) -o $(pdf_dest).pdf

test: env
	(. env/bin/activate; pytest)
