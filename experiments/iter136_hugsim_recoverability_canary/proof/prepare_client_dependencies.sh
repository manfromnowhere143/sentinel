set -eu
sudo -n docker run --name sentinel-i136-deps-20261009 --label sentinel.iteration=136 --entrypoint bash sha256:f73ef38840631211983ea0dde0cf1ecdfa6dbc84ef6cd0bfb900427da6d601cb -c 'python -m pip install --no-cache-dir open3d mediapy && python -m pip freeze && python -c "import open3d,mediapy,torch; print(open3d.__version__,mediapy.__version__,torch.__version__)"'
