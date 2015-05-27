#!/bin/bash
VENV_PATH="./.env"
PEP8_CONF_PATH="./config/pep8.conf"
LOGS_PATH="./logs"

function run_pep8 {

    $VENV_PATH/bin/pep8 --config=$PEP8_CONF_PATH mysite/lti > $LOGS_PATH/pep8.log
    $VENV_PATH/bin/pep8 --config=$PEP8_CONF_PATH mysite/psa >> $LOGS_PATH/pep8.log
    $VENV_PATH/bin/pep8 --config=$PEP8_CONF_PATH mysite/ct >> $LOGS_PATH/pep8.log
    $VENV_PATH/bin/pep8 --config=$PEP8_CONF_PATH mysite/mysite >> $LOGS_PATH/pep8.log
    
    cat $LOGS_PATH/pep8.log

}

function run_pylint {

    $VENV_PATH/bin/pylint --errors-only mysite/lti > $LOGS_PATH/pylint.log
    $VENV_PATH/bin/pylint --errors-only mysite/psa >> $LOGS_PATH/pylint.log
    $VENV_PATH/bin/pylint --errors-only mysite/ct >> $LOGS_PATH/pylint.log
    $VENV_PATH/bin/pylint --errors-only mysite/mysite >> $LOGS_PATH/pylint.log

    cat $LOGS_PATH/pylint.log

}

case $1 in
    pep8)
            run_pep8
        ;;

    pylint)
            run_pylint
        ;;

    *)
        echo "Usage: $0 {pep8|pylint}"
        exit 1
esac
