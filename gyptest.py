#!/usr/bin/env python
# Copyright (c) 2012 Google Inc. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""gyptest.py -- test runner for GYP tests."""

from __future__ import print_function

import argparse
import math
import os
import platform
import subprocess
import sys
import time


def is_test_name(f):
  return f.startswith('gyptest') and f.endswith('.py')


def find_all_gyptest_files(directory):
  result = []
  for root, dirs, files in os.walk(directory):
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
  os.environ['PYTHONUNBUFFERED'] = '1'

  # Log some system configuration info.
  if not args.quiet:
    print('Test configuration:')
    if sys.platform == 'darwin':
      import TestMac
      print('  Mac %s %s' % (platform.mac_ver()[0], platform.mac_ver()[2]))
      print('  Xcode %s' % TestMac.Xcode.Version())
    elif sys.platform == 'win32':
      sys.path.append(os.path.abspath('pylib'))
      import gyp.MSVSVersion
      print('  Win %s %s\n' % platform.win32_ver()[0:2])
      print('  MSVS %s' %
            gyp.MSVSVersion.SelectVisualStudioVersion().Description())
    elif sys.platform in ('linux', 'linux2'):
      print('  Linux %s' % ' '.join(platform.linux_distribution())
    print('  Python %s' % platform.python_version())
    print('  PYTHONPATH=%s' % os.environ['PYTHONPATH'])
    print()

  if args.gyp_option and not args.quiet:
    print('Extra Gyp options: %s\n' % args.gyp_option)

  failed = []

  if args.format:
    format_list = args.format.split(',')
  else:
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

  gyp_options = []
  for option in args.gyp_option:
    gyp_options += ['-G', option]

  run_start = time.time()
  env = os.environ.copy()

  i = 1
  num_tests = len(tests) * len(format_list)
  num_test_digits = math.ceil(math.log(num_tests, 10))
  fmt_str = '[%%%dd/%%%dd] (%%s) %%s' % (
      num_test_digits, num_test_digits)

  for format_ in format_list:
    env['TESTGYP_FORMAT'] = format_

    for test in tests:
      cmd = [sys.executable, test] + gyp_options
      print(fmt_str % (i, num_tests, format_, ' '.join(cmd[1:])), end='')
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

      print(' %s %.3fs' % (res, took))

      if not stdout.endswith('PASSED\n') and not stdout.endswith('NO RESULT\n'):
        for l in stdout.splitlines():
          print('    %s' % l)

      i += 1

  if not args.quiet:
    def report(description, tests):
      if tests:
        if len(tests) == 1:
          print("\n%s the following test:" % description)
        else:
          fmt = "\n%s the following %d tests:"
          print(fmt % (description, len(tests)))
        print("\t" + "\n\t".join(tests))

    report("Failed", failed)

    print('\nRan %d tests, %d failed in %.3fs.' % (
          num_tests, len(failed), time.time() - run_start))
    print()

  if failed:
    return 1
  else:
    return 0


if __name__ == "__main__":
  sys.exit(main())
