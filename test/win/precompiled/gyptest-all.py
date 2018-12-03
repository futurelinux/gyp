#!/usr/bin/env python

# Copyright (c) 2011 Google Inc. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""
Verifies that precompiled headers can be specified.
"""

import TestGyp

import sys

if sys.platform == 'win32':
    test = TestGyp.TestGyp(formats=['msvs', 'ninja'], workdir='workarea_all')

    if test.format == 'msvs':
        # TODO: Figure out why this test is failing and fix it.
        test.skip_test()

    test.run_gyp('hello.gyp')
    test.build('hello.gyp', 'hello')
    test.run_built_executable('hello', stdout="Hello, world!\nHello, two!\n")
    test.up_to_date('hello.gyp', test.ALL)
    test.pass_test()
