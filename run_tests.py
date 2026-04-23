#!/usr/bin/env python3
"""Run all unit tests under tests/ and print a clear summary."""

import os
import sys
import unittest

# Make the package importable without installation
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'src'))

TESTS_DIR = os.path.join(PROJECT_ROOT, 'tests')

# ── ANSI colours (disabled automatically on non-TTY) ─────────────────────────
_USE_COLOUR = sys.stdout.isatty()

def _c(code, text):
    return f'\033[{code}m{text}\033[0m' if _USE_COLOUR else text

def green(t):  return _c('92',   t)
def red(t):    return _c('91',   t)
def yellow(t): return _c('93',   t)
def cyan(t):   return _c('96',   t)
def bold(t):   return _c('1',    t)
def dim(t):    return _c('2',    t)


# ── custom test result ────────────────────────────────────────────────────────

class _Result(unittest.TextTestResult):
    """Coloured per-test output."""

    def _short_desc(self, test):
        cls  = type(test).__name__
        meth = test._testMethodName
        doc  = (test._testMethodDoc or '').strip().splitlines()[0] if test._testMethodDoc else ''
        label = f'{cls}.{meth}'
        return (label, doc)

    def startTest(self, test):
        super().startTest(test)
        if self.showAll:
            label, _ = self._short_desc(test)
            self.stream.write(f'  {dim(label)} ... ')
            self.stream.flush()

    def addSuccess(self, test):
        super().addSuccess(test)
        if self.showAll:
            self.stream.writeln(green('PASS'))

    def addFailure(self, test, err):
        super().addFailure(test, err)
        if self.showAll:
            self.stream.writeln(red('FAIL'))

    def addError(self, test, err):
        super().addError(test, err)
        if self.showAll:
            self.stream.writeln(red('ERROR'))

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        if self.showAll:
            self.stream.writeln(yellow(f'SKIP  ({reason})'))

    def printErrors(self):
        if self.failures or self.errors:
            self.stream.writeln('')
        self.printErrorList(red('FAIL'),  self.failures)
        self.printErrorList(red('ERROR'), self.errors)

    def printErrorList(self, flavour, errors):
        for test, err in errors:
            label, doc = self._short_desc(test)
            self.stream.writeln(bold(f'{"─" * 60}'))
            self.stream.writeln(f'{flavour}  {bold(label)}')
            if doc:
                self.stream.writeln(f'       {dim(doc)}')
            self.stream.writeln(err)


class _Runner(unittest.TextTestRunner):
    resultclass = _Result


# ── entry point ───────────────────────────────────────────────────────────────

def main():
    bar  = bold(cyan('═' * 60))
    thin = dim('─' * 60)

    print(f'\n{bar}')
    print(bold(cyan(f'  Unit Tests  →  {TESTS_DIR}')))
    print(f'{bar}\n')

    loader = unittest.TestLoader()
    suite  = loader.discover(start_dir=TESTS_DIR, pattern='test_*.py')

    runner = _Runner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)

    # ── summary ───────────────────────────────────────────────────────────────
    total   = result.testsRun
    n_fail  = len(result.failures)
    n_err   = len(result.errors)
    n_skip  = len(result.skipped)
    n_pass  = total - n_fail - n_err - n_skip

    print(f'\n{thin}')
    print(bold('  Summary'))
    print(thin)
    print(f'  {green("passed")}   {n_pass:>4}')
    if n_fail:  print(f'  {red("failed")}   {n_fail:>4}')
    if n_err:   print(f'  {red("errors")}   {n_err:>4}')
    if n_skip:  print(f'  {yellow("skipped")}  {n_skip:>4}')
    print(f'  {"total"}    {total:>4}')
    print(thin)

    if result.wasSuccessful():
        print(bold(green(f'\n  ✓  All {total} tests passed\n')))
    else:
        print(bold(red(f'\n  ✗  {n_fail + n_err} test(s) did not pass\n')))

    sys.exit(0 if result.wasSuccessful() else 1)


if __name__ == '__main__':
    main()
