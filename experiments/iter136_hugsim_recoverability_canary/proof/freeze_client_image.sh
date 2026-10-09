set -eu
sudo -n docker commit sentinel-i136-deps-20261009 sentinel-i136-client:20261009
sudo -n docker image inspect sentinel-i136-client:20261009 --format '{{.Id}}'
sudo -n docker run --rm --name sentinel-i136-client-import --gpus all -v /opt/sentinel-stack/UniAD_SIM:/model -v /opt/sentinel-stack/UniAD/ckpts:/model/ckpts -v /opt/sentinel-stack/hugsim-shim:/shim -w /model -e PYTHONPATH=.:/shim -e SENTINEL_ENABLED=1 --entrypoint python sentinel-i136-client:20261009 -u tools/closeloop/e2e.py --help
