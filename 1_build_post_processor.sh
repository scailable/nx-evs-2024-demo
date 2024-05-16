cd "$(dirname "$0")"

python3 -m venv ~/venvs/evs
. ~/venvs/evs/bin/activate

mkdir build
cd build
cmake ..
make 
sudo cp ./postprocessor-python-example/postprocessor-python-example /opt/networkoptix-metavms/mediaserver/bin/plugins/nxai_plugin/nxai_manager/postprocessors/
