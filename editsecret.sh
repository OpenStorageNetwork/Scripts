#! /bin/bash

SCRIPT_PATH=${BASH_SOURCE:-$0}
DEFAULT_REGION=us-east-2
SECRET_DOES_NOT_EXIST_MSG=$(cat << EOM
**********SECRET "<<SECRET_NAME>>" DOES NOT EXIT***********

The secret that you have specified, <<SECRET_NAME>>, does not exist.
If you save this buffer, you will create a new secret.

**********SECRET "<<SECRET_NAME>>" DOES NOT EXIT***********

OSN yaml template provided here for conveinience.
---
site_private_key: |
  -----BEGIN OPENSSH PRIVATE KEY-----
  Insert your favorite key material
  indented two spaces as shown here
  Note: VIM indent is set to 2 spaces here
  -----END OPENSSH PRIVATE KEY-----
site_public_key: pubkey
site_root_password: password
site_drac_password: password
EOM
)

function do_preflight {

  # SECRET_REGION should always be defined but defensive
  # code below...
  if [[ ! ( -v SECRET_NAME && -v SECRET_REGION ) ]]
  then
      echo "You must provide a path to a valid osn ansible inventory file or a secret name and region"
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
        echo "export AWS_SECRET_ACCESS_KEY="
        echo "export AWS_ACCESS_KEY_ID="
        exit 1
    fi

}

while getopts 'i:r:s:cdh' opt; do
  case "$opt" in
    c)
      WRITECB=1
      ;;

    i)
      INVFILE="$OPTARG"
      ;;

    d)
      DEBUG=1
      ;;

    s)
      SECRET_NAME="$OPTARG"
      ;;

    r)
      SECRET_REGION="$OPTARG"
      ;;
   
    \?|h)
      echo "Usage: $(basename "$0") [-c] [-d] [-s secret name] [-r secret region ] [-i inventory_file]"
      exit 1
      ;;
  esac
done
shift "$((OPTIND -1))"

# **Note defaults below**
# Specifically provided secret or region will override inventory
if [[ -f "$INVFILE" ]]
then
    SECRET_NAME=${SECRET_NAME:-$(yq -r '.all.vars.secret_path' "$INVFILE")}
    SECRET_REGION=${SECRET_REGION:-$(yq -r '.all.vars.secret_region' "$INVFILE")}
fi

# If we don't have a region at this point, then it hasn't
# been provided in inventory or by -r option. Use
# default.
SECRET_REGION=${SECRET_REGION:-$DEFAULT_REGION}

do_preflight "$@"

# DIRECT - Called directly
if [[ ! -v WRITECB ]]
then
    # Funny syntax at end adds "-d" to commandline if DEBUG is set
    CALLBACK_CMD="$SCRIPT_PATH -r $SECRET_REGION -s $SECRET_NAME ${DEBUG+-d} -c"

    site_secret=$(aws secretsmanager get-secret-value --secret-id="$SECRET_NAME" --region="$SECRET_REGION" --query 'SecretString')
    buffer_text=$(echo "$site_secret" | yq -j)
    buffer_text=${buffer_text:-${SECRET_DOES_NOT_EXIST_MSG//<<SECRET_NAME>>/$SECRET_NAME}}
    
    echo "$buffer_text" | vim \
    -c 'set buftype=acwrite' \
    -c "autocmd BufWriteCmd <buffer> execute \"%!$CALLBACK_CMD\" | set nomod" \
    -c 'set nobackup' \
    -c 'set noswapfile' \
    -c "file awssecrets" \
    -c 'autocmd VimEnter * set nomod | redraw!' \
    -c 'set autoindent expandtab tabstop=2 shiftwidth=2' \
    -
# CALLBACK - Called indirectly from vim on write (per autocmd def above)
else
    STD_IN=$(</dev/stdin)
    if [[ -v DEBUG ]]
    then
        echo "${STD_IN}" | tee editsecret.log
    else
        # check to see if secret exists
        err="$(aws secretsmanager describe-secret --secret-id="$SECRET_NAME" --region="$SECRET_REGION"  2>&1 1>/dev/null)"
        if [[ $err == *ResourceNotFoundException* ]]
        then
            aws secretsmanager create-secret --name="$SECRET_NAME" --region="$SECRET_REGION" --secret-string "$(cat <<< "${STD_IN}")"
        else
            aws secretsmanager put-secret-value --secret-id="$SECRET_NAME" --region="$SECRET_REGION" --secret-string "$(cat <<< "${STD_IN}")"
        fi
    fi
fi

exit 0
