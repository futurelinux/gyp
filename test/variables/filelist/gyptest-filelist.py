#!/usr/bin/env python

# Copyright (c) 2012 Google Inc. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""
Test variable expansion of '<|(list.txt ...)' syntax commands.
"""

import TestGyp

test = TestGyp.TestGyp()

if test.format == 'xcode-ninja':
  test.skip_test(bug=527)

CHDIR = 'src'
test.run_gyp('filelist2.gyp', chdir=CHDIR)

test.build('filelist2.gyp', 'foo', chdir=CHDIR)
contents = test.read('src/dummy_foo').replace('\r', '')
expect = 'John\nJacob\nJingleheimer\nSchmidt\n'
if not test.match(contents, expect):
  print "Unexpected contents of `src/dummy_foo'"
  test.diff(expect, contents, 'src/dummy_foo')
  test.fail_test()

test.pass_test()
