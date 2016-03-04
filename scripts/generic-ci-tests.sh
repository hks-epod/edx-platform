#!/usr/bin/env bash
set -e

###############################################################################
#
#   generic-ci-tests.sh
#
#   Execute all tests for edx-platform.
#
#   This script can be called from CI jobs that define
#   these environment variables:
#
#   `TEST_SUITE` defines which kind of test to run.
#   Possible values are:
#
#       - "quality": Run the quality (pep8/pylint) checks
#       - "lms-unit": Run the LMS Python unit tests
#       - "cms-unit": Run the CMS Python unit tests
#       - "js-unit": Run the JavaScript tests
#       - "commonlib-unit": Run Python unit tests from the common/lib directory
#       - "commonlib-js-unit": Run the JavaScript tests and the Python unit
#           tests from the common/lib directory
#       - "lms-acceptance": Run the acceptance (Selenium/Lettuce) tests for
#           the LMS
#       - "cms-acceptance": Run the acceptance (Selenium/Lettuce) tests for
#           Studio
#       - "bok-choy": Run acceptance tests that use the bok-choy framework
#
#   `SHARD` is a number indicating which subset of the tests to build.
#
#       For "bok-choy" and "lms-unit", the tests are put into shard groups
#       using the nose'attr' decorator (e.g. "@attr('shard_1')"). Anything with
#       the 'shard_n' attribute will run in the nth shard. If there isn't a
#       shard explicitly assigned, the test will run in the last shard (the one
#       with the highest number).
#
#   Jenkins-specific configuration details:
#
#   - The edx-platform git repository is checked out by the Jenkins git plugin.
#   - Jenkins logs in as user "jenkins"
#   - The Jenkins file system root is "/home/jenkins"
#   - An init script creates a virtualenv at "/home/jenkins/edx-venv"
#     with some requirements pre-installed (such as scipy)
#
#  Jenkins worker setup:
#  See the edx/configuration repo for Jenkins worker provisioning scripts.
#  The provisioning scripts install requirements that this script depends on!
#
###############################################################################

# If the environment variable 'SHARD' is not set, default to 'all'.
# This could happen if you are trying to use this script from
# jenkins and do not define 'SHARD' in your multi-config project.
# Note that you will still need to pass a value for 'TEST_SUITE'
# or else no tests will be executed.
SHARD=${SHARD:="all"}
NUMBER_OF_BOKCHOY_THREADS=${NUMBER_OF_BOKCHOY_THREADS:=1}

# Clean up previous builds
git clean -qxfd

case "$TEST_SUITE" in

    "quality")
        echo "git show -1"
        git show -1
        echo "Finding fixme's and storing report..."
        paver find_fixme > fixme.log || { cat fixme.log; EXIT=1; }
        echo "Finding pep8 violations and storing report..."
        paver run_pep8 > pep8.log || { cat pep8.log; EXIT=1; }
        exit $EXIT
        ;;

    "lms-unit")
        paver install_prereqs
        ;;

    "cms-unit")
        paver help test_system -s cms --extra_args="--with-flaky" --cov_args="-p"
        ;;

    "commonlib-unit")
        paver help test_lib --extra_args="--with-flaky" --cov_args="-p"
        ;;

    "js-unit")
        paver help test_js --coverage
        paver help diff_coverage
        ;;

    "commonlib-js-unit")
        paver help test_js --coverage --skip_clean || { EXIT=1; }
        paver help test_lib --skip_clean --extra_args="--with-flaky" --cov_args="-p" || { EXIT=1; }

        # This is to ensure that the build status of the shard is properly set.
        # Because we are running two paver commands in a row, we need to capture
        # their return codes in order to exit with a non-zero code if either of
        # them fail. We put the || clause there because otherwise, when a paver
        # command fails, this entire script will exit, and not run the second
        # paver command in this case statement. So instead of exiting, the value
        # of a variable named EXIT will be set to 1 if either of the paver
        # commands fail. We then use this variable's value as our exit code.
        # Note that by default the value of this variable EXIT is not set, so if
        # neither command fails then the exit command resolves to simply exit
        # which is considered successful.
        exit $EXIT
        ;;

    "lms-acceptance")
        paver help test_acceptance -s lms --extra_args="-v 3"
        ;;

    "cms-acceptance")
        paver help test_acceptance -s cms --extra_args="-v 3"
        ;;

    "bok-choy")
        case "$SHARD" in

            "all")
                paver help test_bokchoy
                ;;

            "1")
                paver help test_bokchoy -n $NUMBER_OF_BOKCHOY_THREADS --extra_args="-a shard_1 --with-flaky"
                ;;

            "2")
                paver help test_bokchoy -n $NUMBER_OF_BOKCHOY_THREADS --extra_args="-a 'shard_2' --with-flaky"
                ;;

            "3")
                paver help test_bokchoy -n $NUMBER_OF_BOKCHOY_THREADS --extra_args="-a 'shard_3' --with-flaky"
                ;;

            "4")
                paver help test_bokchoy -n $NUMBER_OF_BOKCHOY_THREADS --extra_args="-a 'shard_4' --with-flaky"
                ;;

            "5")
                paver help test_bokchoy -n $NUMBER_OF_BOKCHOY_THREADS --extra_args="-a 'shard_5' --with-flaky"
                ;;

            "6")
                paver help test_bokchoy -n $NUMBER_OF_BOKCHOY_THREADS --extra_args="-a 'shard_6' --with-flaky"
                ;;

            "7")
                paver help test_bokchoy -n $NUMBER_OF_BOKCHOY_THREADS --extra_args="-a 'shard_7' --with-flaky"
                ;;

            "8")
                paver help test_bokchoy -n $NUMBER_OF_BOKCHOY_THREADS --extra_args="-a 'shard_8' --with-flaky"
                ;;

            "9")
                paver help test_bokchoy -n $NUMBER_OF_BOKCHOY_THREADS --extra_args="-a shard_1=False,shard_2=False,shard_3=False,shard_4=False,shard_5=False,shard_6=False,shard_7=False,shard_8=False,a11y=False --with-flaky"
                ;;

            # Default case because if we later define another bok-choy shard on Jenkins
            # (e.g. Shard 5) in the multi-config project and expand this file
            # with an additional case condition, old branches without that commit
            # would not execute any tests on the worker assigned to that shard
            # and thus their build would fail.
            # This way they will just report 1 test executed and passed.
            *)
                # Need to create an empty test result so the post-build
                # action doesn't fail the build.
                # May be unnecessary if we changed the "Skip if there are no test files"
                # option to True in the jenkins job definitions.
                mkdir -p reports/bok_choy
                cat > reports/bok_choy/xunit.xml <<END
<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="nosetests" tests="1" errors="0" failures="0" skip="0">
<testcase classname="acceptance.tests" name="shard_placeholder" time="0.001"></testcase>
</testsuite>
END
                ;;
        esac
        ;;
esac
