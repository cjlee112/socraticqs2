#!/bin/bash
VENV_PATH="./.env"
PEP8_CONF_PATH="./config/pep8.conf"
LOGS_PATH="./logs"

function start_check {

    $VENV_PATH/bin/pep8 --show-source --show-pep8 --config=$PEP8_CONF_PATH mysite/lti > $LOGS_PATH/pep8.log
    $VENV_PATH/bin/pep8 --show-source --show-pep8 --config=$PEP8_CONF_PATH mysite/psa >> $LOGS_PATH/pep8.log
    $VENV_PATH/bin/pep8 --show-source --show-pep8 --config=$PEP8_CONF_PATH mysite/ct >> $LOGS_PATH/pep8.log
    $VENV_PATH/bin/pep8 --show-source --show-pep8 --config=$PEP8_CONF_PATH mysite/mysite >> $LOGS_PATH/pep8.log
    less $LOGS_PATH/pep8.log

}

case $1 in
    all)
            start_check
        ;;

    ct)
            $VENV_PATH/bin/pep8 --show-source --show-pep8 --config=$PEP8_CONF_PATH mysite/ct > $LOGS_PATH/pep8.log || { less $LOGS_PATH/pep8.log; }
        ;;

    lti)
            $VENV_PATH/bin/pep8 --show-source --show-pep8 --config=$PEP8_CONF_PATH mysite/lti > $LOGS_PATH/pep8.log || { less $LOGS_PATH/pep8.log; }
        ;;

    psa)
            $VENV_PATH/bin/pep8 --show-source --show-pep8 --config=$PEP8_CONF_PATH mysite/psa > $LOGS_PATH/pep8.log || { less $LOGS_PATH/pep8.log; }
        ;;

    *)
        echo "Usage: $0 {all|ct|lti|psa}"
        exit 1
esac
