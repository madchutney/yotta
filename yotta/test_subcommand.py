# Copyright 2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import os
import logging
import re

# validate, , validate things, internal
from .lib import validate
# CMakeGen, , generate build files, internal
from .lib import cmakegen


def addOptions(parser):
    parser.add_argument(
        "--all", dest='all', default=False, action='store_true',
        help='Run the tests for all dependencies too, not just this module.'
    )

def findCTests(builddir, recurse_yotta_modules=False):
    ''' returns a list of (directory_path, [list of test commands]) '''
    # we don't run ctest -N to get the list of tests because unfortunately it
    # only lists the names, not the test commands. The best way to get at these
    # seems to be to parse the CTestTestfile.cmake files, which kinda sucks,
    # but works... Patches welcome.
    tests = []
    add_test_re = re.compile('add_test\\([^" ]*\s*"(.*)"\\)')
    for root, dirs, files in os.walk(builddir, topdown=True):
        if not recurse_yotta_modules:
            dirs = [d for d in dirs if d != 'ym']
        if 'CTestTestfile.cmake' in files:
            with open(os.path.join(root, 'CTestTestfile.cmake'), 'r') as ctestf:
                dir_tests = []
                for line in ctestf:
                    if line.startswith('add_test'):
                        match = add_test_re.search(line)
                        if match:
                            dir_tests.append(match.group(1))
                        else:
                            logging.error(
                                "unknown CTest Syntax '%s', please report this error at http://github.com/ARMmbed/yotta/issues" %
                                line.rstrip('\n')
                            )
                if len(dir_tests):
                    tests.append((root, dir_tests))
    return tests

def execCommand(args, following_args):
    cwd = os.getcwd()

    c = validate.currentDirectoryModule()
    if not c:
        return 1

    target, errors = c.satisfyTarget(args.target)
    if errors:
        for error in errors:
            logging.error(error)
        return 1

    builddir = os.path.join(cwd, 'build', target.getName())
 
    # get the list of tests we need to run, if --all is specified we also run
    # the tests for all of our submodules, otherwise we just run the tests for
    # this module. 
    tests = findCTests(builddir, recurse_yotta_modules=args.all)


    returncode = 0
    for dirname, test_exes in tests:
        # !!! FIXME: find the module associated with the specified directory,
        # read it's testReporter command if it has one, and pipe the test
        # output for all of its tests through its test reporter
        for test in test_exes:
            for err in target.test(dirname, test):
                logging.error(err)
                returncode += 1
    
    return returncode

