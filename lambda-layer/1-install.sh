python3.12 -m venv create_layer
source create_layer/bin/activate
pip install -r requirements.txt --platform=manylinux2014_aarch64 --only-binary=:all: --target ./create_layer/lib/python3.12/site-packages