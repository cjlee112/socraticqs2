#!/bin/bash

PEP8_CONF_PATH="./config/pep8rc"
PYLINT_CONF_PATH="./config/pylintrc"
LOGS_PATH="./logs"

function run_pep8 {

    pep8 --config=$PEP8_CONF_PATH mysite/lti > $LOGS_PATH/pep8.log
    pep8 --config=$PEP8_CONF_PATH mysite/psa >> $LOGS_PATH/pep8.log
    pep8 --config=$PEP8_CONF_PATH mysite/ct >> $LOGS_PATH/pep8.log
    pep8 --config=$PEP8_CONF_PATH mysite/mysite >> $LOGS_PATH/pep8.log
    
    cat $LOGS_PATH/pep8.log

}

function run_pylint {

    pylint --rcfile=$PYLINT_CONF_PATH mysite/lti > $LOGS_PATH/pylint.log
    pylint --rcfile=$PYLINT_CONF_PATH mysite/psa >> $LOGS_PATH/pylint.log
    pylint --rcfile=$PYLINT_CONF_PATH mysite/ct >> $LOGS_PATH/pylint.log
    pylint --rcfile=$PYLINT_CONF_PATH mysite/mysite >> $LOGS_PATH/pylint.log

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
