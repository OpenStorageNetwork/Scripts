#! /bin/bash

# "Facts" based on default Gen2 Pod HW/SW Config
SITE_USER="osnadmin"

declare -A IDRAC_JUMPHOST_MAP=(\
['storcon0']="storcon1" \
['storcon1']="mon0" \
['mon0']="storcon0"
)

function do_preflight {

    # CHECK ARGUMENTS
    if [[ ! -f "$INVPATH" ]]
    then
        echo "You must provide a path to a valid ansible inventory file"
        exit 1
    fi

    if [[ ! -v SERVERNAME ]]
    then
        echo "You must provide a target server name"
        exit 1
    fi

    if [[ -z ${IDRAC_JUMPHOST_MAP[$SERVERNAME]} ]]
    then
      echo "Server name must be one of storcon0, storcon1 or mon0. You supplied $SERVERNAME"
      exit 1
    fi

    # using map as convenient way to test valid hostnames...
    if [[ -v JUMPHOST_NAME ]] && [[ -z ${IDRAC_JUMPHOST_MAP[$JUMPHOST_NAME]} ]]
    then
      echo "Jumphost name must be one of storcon0, storcon1 or mon0. You supplied $JUMPHOST_NAME"
      exit 1
    fi

    # CHECK SW REQUIREMENTS
    if [[ ${BASH_VERSION:0:1} -lt 4 ]]
    then 
        echo 'This script requires bash version 4 or greater'
        exit 1
    fi

    which yq  > /dev/null 2>&1
    if [[ $? != 0 ]]
    then
        echo this script requires yq to be on your path, please install
        exit 1
    fi

    which aws  > /dev/null 2>&1
    if [[ $? != 0 ]]
    then
        echo this script requires aws to be on your path, please install
        exit 1
    fi

    # CHECK REQUIRED KEYS IN ENV
    if [[ -z $AWS_ACCESS_KEY_ID ]] || [[ -z $AWS_SECRET_ACCESS_KEY ]]
    then
        echo "Both AWS_SECRET_ACCESS_KEY and AWS_ACCESS_KEY_ID must be set to run this script"
        exit 1
    fi

}

while getopts 'i:s:j:h' opt; do
  case "$opt" in
    j)
      JUMPHOST_NAME="$OPTARG"
      ;;

    i)
      INVPATH="$OPTARG"
      ;;

    s)
      SERVERNAME="$OPTARG"
      ;;
   
    \?|h)
      echo "Usage: $(basename "$0") -i inventory_file -s servername [-j jumphost]"
      exit 1
      ;;
  esac
done
shift "$((OPTIND -1))"

do_preflight "$@"

# ******** GET JUMPHOST IP FROM INVENTORY *************

# oob IPs have netmask which needs to be stripped
rpat='s/\/[0-9]+[0-9]+//g'
IDRAC_JUMPHOST_NAME=${IDRAC_JUMPHOST_MAP[$SERVERNAME]}
# Use jumphost as passed by user if defined otherwise use 
# host connected to idrac
JH_NAME=${JUMPHOST_NAME:-$IDRAC_JUMPHOST_NAME}
JH=$(yq -r ".all.hosts.$JH_NAME.oob_ip" "$INVPATH")
JUMPHOST_IP=$(echo "$JH" | sed -r "$rpat")

# ******** GET SSH KEY FROM AWS SECRETS MANAGER ********

# Find location of sites secret information
SECRET_NAME=$(yq -r '.all.vars.secret_path' "$INVPATH")
SECRET_REGION=$(yq -r '.all.vars.secret_region' "$INVPATH")

JUMPHOST_KEY=$(\
aws secretsmanager get-secret-value --secret-id="$SECRET_NAME" --region="$SECRET_REGION" --query 'SecretString' |\
 yq -j | \
 yq -r '.site_private_key'
 )

# Add the key to the agent (don't write to local disk...)
echo "${JUMPHOST_KEY}" | ssh-add -

# Create pubkey so we can tell agent which key to use
echo "${JUMPHOST_KEY}" | ssh-keygen -y -f /dev/stdin > "$HOME/.ssh/tmpkey_pub"

# ******** CREATE TEMP CONFIG FILE FOR CONNECTIONS/FORWARDING* *******

# Get unused local ephemeral port
while
  LOCALPORT=$(shuf -n 1 -i 49152-65535)
  netstat -atun | grep -q "$LOCALPORT"
do
  continue
done

cat << EOF > "$HOME/.ssh/tmp_config"
Host jumphost
  User $SITE_USER
  Hostname $JUMPHOST_IP
  IdentityFile $HOME/.ssh/tmpkey_pub

Host target*
  User $SITE_USER
  Hostname $JUMPHOST_IP
  IdentityFile $HOME/.ssh/tmpkey_pub
  LocalForward $LOCALPORT ${SERVERNAME}_idrac:443
  ControlPath /tmp/ssh_tunnel_%h.sock 
  ControlMaster yes
  ExitOnForwardFailure yes
  SessionType none
  ForkAfterAuthentication yes

Host target-proxied
  ProxyJump jumphost
  Hostname $IDRAC_JUMPHOST_NAME


EOF

ssh -F "$HOME/.ssh/tmp_config" "target${JUMPHOST_NAME+-proxied}" && \
echo "ssh tunnel started successfully" || echo "ssh tunnel failed to start"

# ******** LAUNCH BROWSER *************

URL_TARGET="https://localhost:$LOCALPORT"

echo "Opening: $URL_TARGET"

case "$OSTYPE" in
  darwin*)
    open -u "$URL_TARGET"
    ;; 
  linux*)
    xdg-open "$URL_TARGET"
    ;;
  *)
    echo "unsupported: $OSTYPE"
    ;;
esac

( trap exit SIGINT ; read -r -d '' _ </dev/tty )

# Close the ssh tunnel socket and cleanup the key and config info
ssh -S /tmp/ssh_tunnel_%h.sock -O exit target
ssh-add -d "$HOME/.ssh/tmpkey_pub"
rm "$HOME/.ssh/tmpkey_pub"
rm "$HOME/.ssh/tmp_config"

exit 0
