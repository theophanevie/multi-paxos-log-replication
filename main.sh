if [ $# -ne 1  ]; then
    echo "USAGE: $0 <configfile>"
    exit
fi

CONFIG=$1

SERVERS=$(cat "${CONFIG}" | yq '.servers')
CLIENTS=$(cat "${CONFIG}" | yq '.clients | length')

mpiexec  --hostfile hostfile -v -n $((${SERVERS} + ${CLIENTS} + 1)) ./algorep.py run ${CONFIG}
