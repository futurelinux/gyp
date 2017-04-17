#!/usr/bin/env python
# Copyright (c) 2012 Google Inc. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""gyptest.py -- test runner for GYP tests."""

from __future__ import print_function

import argparse
import math
import os
import subprocess
import sys
import time


def is_test_name(f):
  return f.startswith('gyptest') and f.endswith('.py')


def find_all_gyptest_files(directory):
  result = []
  for root, dirs, files in os.walk(directory):
    if '.svn' in dirs:
      dirs.remove('.svn')
    result.extend([ os.path.join(root, f) for f in files if is_test_name(f) ])
  result.sort()
  return result


def main(argv=None):
  if argv is None:
    argv = sys.argv

  parser = argparse.ArgumentParser()
  parser.add_argument("-a", "--all", action="store_true",
      help="run all tests")
  parser.add_argument("-C", "--chdir", action="store",
      help="change to directory")
  parser.add_argument("-f", "--format", action="store", default='',
      help="run tests with the specified formats")
  parser.add_argument("-G", '--gyp_option', action="append", default=[],
      help="Add -G options to the gyp command line")
  parser.add_argument("-l", "--list", action="store_true",
      help="list available tests and exit")
  parser.add_argument("-n", "--no-exec", action="store_true",
      help="no execute, just print the command line")
  parser.add_argument("--path", action="append", default=[],
      help="additional $PATH directory")
  parser.add_argument("-q", "--quiet", action="store_true",
      help="quiet, don't print test command lines")
  parser.add_argument('tests', nargs='*')
  args = parser.parse_args(argv[1:])

  if args.chdir:
    os.chdir(args.chdir)

  if args.path:
    extra_path = [os.path.abspath(p) for p in opts.path]
    extra_path = os.pathsep.join(extra_path)
    os.environ['PATH'] = extra_path + os.pathsep + os.environ['PATH']

  if not args.tests:
    if not args.all:
      sys.stderr.write('Specify -a to get all tests.\n')
      return 1
    args.tests = ['test']

  tests = []
  for arg in args.tests:
    if os.path.isdir(arg):
      tests.extend(find_all_gyptest_files(os.path.normpath(arg)))
    else:
      if not is_test_name(os.path.basename(arg)):
        print(arg, 'is not a valid gyp test name.', file=sys.stderr)
        sys.exit(1)
      tests.append(arg)

  if args.list:
    for test in tests:
      print(test)
    sys.exit(0)

  os.environ['PYTHONPATH'] = os.path.abspath('test/lib')
  if not args.quiet:
    sys.stdout.write('PYTHONPATH=%s\n' % os.environ['PYTHONPATH'])

  if args.gyp_option and not args.quiet:
    sys.stdout.write('Extra Gyp options: %s\n' % args.gyp_option)

  failed = []

  if args.format:
    format_list = args.format.split(',')
  else:
    # TODO:  not duplicate this mapping from pylib/gyp/__init__.py
    format_list = {
      'aix5':     ['make'],
      'freebsd7': ['make'],
      'freebsd8': ['make'],
      'openbsd5': ['make'],
      'cygwin':   ['msvs'],
      'win32':    ['msvs', 'ninja'],
      'linux':    ['make', 'ninja'],
      'linux2':   ['make', 'ninja'],
      'linux3':   ['make', 'ninja'],
      'darwin':   ['make', 'ninja', 'xcode', 'xcode-ninja'],
    }[sys.platform]

  i = 1
  num_tests = len(tests) * len(format_list)
  num_test_digits = math.ceil(math.log(num_tests, 10))
  fmt_str = '[%%%dd/%%%dd] (%%s) %%s' % (
      num_test_digits, num_test_digits)
  run_start = time.time()

  env = os.environ.copy()
  for format_ in format_list:
    env['TESTGYP_FORMAT'] = format_

    gyp_options = []
    for option in args.gyp_option:
      gyp_options += ['-G', option]

    for test in tests:
      cmd = [sys.executable, test] + gyp_options
      sys.stdout.write(fmt_str % (i, num_tests, format_, ' '.join(cmd[1:])))
      sys.stdout.flush()

      start = time.time()
      proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, env=env)
      proc.wait()
      took = time.time() - start

      stdout = proc.stdout.read().decode('utf8')

      if proc.returncode == 2:
        res = 'skipped'
      elif proc.returncode:
        res = 'failed'
        failed.append('(%s) %s' % (format_, test))
      else:
        res = 'passed'

      sys.stdout.write(' %s %.3fs\n' % (res, took))
      sys.stdout.flush()

      if not stdout.endswith('PASSED\n') and not stdout.endswith('NO RESULT\n'):
        for l in stdout.splitlines():
          sys.stdout.write('    %s\n' % l)
        sys.stdout.flush()

      i += 1

  if not args.quiet:
    def report(description, tests):
      if tests:
        if len(tests) == 1:
          sys.stdout.write("\n%s the following test:\n" % description)
        else:
          fmt = "\n%s the following %d tests:\n"
          sys.stdout.write(fmt % (description, len(tests)))
        sys.stdout.write("\t" + "\n\t".join(tests) + "\n")

    report("Failed", failed)

    sys.stdout.write('\nRan %d tests, %d failed in %.3fs.\n' % (
                     num_tests, len(failed), time.time() - run_start))
    sys.stdout.write('\n')
    sys.stdout.flush()

  if failed:
    return 1
  else:
    return 0


if __name__ == "__main__":
  sys.exit(main())
