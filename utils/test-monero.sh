IP=127.0.0.1
PORT=18082
METHOD="get_balance"
PARAMS="{\"account_index\": 1}"
curl \
    http://$IP:$PORT/json_rpc \
    -d '{"jsonrpc":"2.0","id":"0","method":"'$METHOD'","params":'"$PARAMS"'}' \
    -H 'Content-Type: application/json'
