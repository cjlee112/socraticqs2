#!/bin/bash

PEP8_CONF_PATH="./config/pep8rc"
PYLINT_CONF_PATH="./config/pylintrc"
LOGS_PATH="./logs"
APPS="accounts chat ct fsm lms lti pages psa mysite test"

function run_pep8 {
    echo "" > $PEP8_CONF_PATH
    for app in $APPS; do
        pep8 --config=$PEP8_CONF_PATH "mysite/${app}" >> $LOGS_PATH/pep8.log
    done

    cat $LOGS_PATH/pep8.log

}

function run_pylint {
    echo "" > $PYLINT_CONF_PATH
    for app in $APPS; do
        pylint --rcfile=$PYLINT_CONF_PATH "mysite/${app}" >> $LOGS_PATH/pylint.log
    done

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

function join_by { local IFS="$1"; shift; echo "$*"; }


case $1 in
    pep8)
            if [ $2 = "all" ] || [ $2 = '' ]; then
                echo "Running pep8 on all apps."
                run_pep8
            else
                echo "Running pep8 on $2 app."
                run_pep8_spec $2
            fi
        ;;

    pylint)
            if [ $2 = "all" ] || [ $2 = '' ]; then
                echo "Running pylint on all apps."
                run_pylint
            else
                echo "Running pylint on $2 app."
                run_pylint_spec $2
            fi
        ;;

    *)
        res="${APPS// /|}"
        echo "Usage: $0 {pep8|pylint} {$res}"
        exit 1
esac
