#!/bin/bash

PEP8_CONF_PATH="./config/pep8rc"
PYLINT_CONF_PATH="./config/pylintrc"
LOGS_PATH="./logs"

function run_pep8 {

    pep8 --config=$PEP8_CONF_PATH mysite/lti > $LOGS_PATH/pep8.log
    pep8 --config=$PEP8_CONF_PATH mysite/psa >> $LOGS_PATH/pep8.log
    pep8 --config=$PEP8_CONF_PATH mysite/ct >> $LOGS_PATH/pep8.log
    pep8 --config=$PEP8_CONF_PATH mysite/fsm >> $LOGS_PATH/pep8.log
    pep8 --config=$PEP8_CONF_PATH mysite/mysite >> $LOGS_PATH/pep8.log
    
    cat $LOGS_PATH/pep8.log

}

function run_pylint {

    pylint --rcfile=$PYLINT_CONF_PATH mysite/lti > $LOGS_PATH/pylint.log
    pylint --rcfile=$PYLINT_CONF_PATH mysite/psa >> $LOGS_PATH/pylint.log
    pylint --rcfile=$PYLINT_CONF_PATH mysite/ct >> $LOGS_PATH/pylint.log
    pylint --rcfile=$PYLINT_CONF_PATH mysite/fsm >> $LOGS_PATH/pylint.log
    pylint --rcfile=$PYLINT_CONF_PATH mysite/mysite >> $LOGS_PATH/pylint.log

    cat $LOGS_PATH/pylint.log

}

function run_pep8_spec {

    pep8 --config=$PEP8_CONF_PATH mysite/$1 > $LOGS_PATH/pep8.log
    
    cat $LOGS_PATH/pep8.log

}

function run_pylint_spec {

    pylint --rcfile=$PYLINT_CONF_PATH mysite/$1 > $LOGS_PATH/pylint.log

    cat $LOGS_PATH/pylint.log

}

case $1 in
    pep8)
            if [ $2 = "all" ]; then
                echo "Running pep8 on all apps."
                run_pep8
            else
                echo "Running pep8 on $2 app."
                run_pep8_spec $2
            fi
        ;;

    pylint)
            if [ $2 = "all" ]; then
                echo "Running pylint on all apps."
                run_pylint
            else
                echo "Running pylint on $2 app."
                run_pylint_spec $2
            fi
        ;;

    *)
        echo "Usage: $0 {pep8|pylint} {lti|psa|fsm|ct|mysite|all}"
        exit 1
esac
