#! /usr/bin/env python
# $Id: DD.py,v 1.2 2001/11/05 19:53:33 zeller Exp $
# Enhanced Delta Debugging class
# Copyright (c) 1999, 2000, 2001 Andreas Zeller.

# This module (written in Python) implements the base delta debugging
# algorithms and is at the core of all our experiments.  This should
# easily run on any platform and any Python version since 1.6.
#
# To plug this into your system, all you have to do is to create a
# subclass with a dedicated `test()' method.  Basically, you would
# invoke the DD test case minimization algorithm (= the `ddmin()'
# method) with a list of characters; the `test()' method would combine
# them to a document and run the test.  This should be easy to realize
# and give you some good starting results; the file includes a simple
# sample application.
#
# This file is in the public domain; feel free to copy, modify, use
# and distribute this software as you wish - with one exception.
# Passau University has filed a patent for the use of delta debugging
# on program states (A. Zeller: `Isolating cause-effect chains',
# Saarland University, 2001).  The fact that this file is publicly
# available does not imply that I or anyone else grants you any rights
# related to this patent.
#
# The use of Delta Debugging to isolate failure-inducing code changes
# (A. Zeller: `Yesterday, my program worked', ESEC/FSE 1999) or to
# simplify failure-inducing input (R. Hildebrandt, A. Zeller:
# `Simplifying failure-inducing input', ISSTA 2000) is, as far as I
# know, not covered by any patent, nor will it ever be.  If you use
# this software in any way, I'd appreciate if you include a citation
# such as `This software uses the delta debugging algorithm as
# described in (insert one of the papers above)'.
#
# All about Delta Debugging is found at the delta debugging web site,
#
#               http://www.st.cs.uni-sb.de/dd/
#
# Happy debugging,
#
# Andreas Zeller


# Start with some helpers.
class OutcomeCache:
    # This class holds test outcomes for configurations.  This avoids
    # running the same test twice.

    # The outcome cache is implemented as a tree.  Each node points
    # to the outcome of the remaining list.
    #
    # Example: ([1, 2, 3], PASS), ([1, 2], FAIL), ([1, 4, 5], FAIL):
    #
    #      (2, FAIL)--(3, PASS)
    #     /
    # (1, None)
    #     \
    #      (4, None)--(5, FAIL)

    def __init__(self):
        self.tail = {}  # Points to outcome of tail
        self.result = None  # Result so far

    def add(self, c, result):
        """Add (C, RESULT) to the cache.  C must be a list of scalars."""
        cs = c[:]
        cs.sort()

        p = self
        for start in range(len(c)):
            if c[start] not in p.tail:
                p.tail[c[start]] = OutcomeCache()
            p = p.tail[c[start]]

        p.result = result

    def lookup(self, c):
        """Return RESULT if (C, RESULT) is in the cache; None, otherwise."""
        p = self
        for start in range(len(c)):
            if c[start] not in p.tail:
                return None
            p = p.tail[c[start]]

        return p.result

    def lookup_superset(self, c, start=0):
        """Return RESULT if there is some (C', RESULT) in the cache with
        C' being a superset of C or equal to C.  Otherwise, return None."""

        # FIXME: Make this non-recursive!
        if start >= len(c):
            if self.result:
                return self.result
            elif self.tail != {}:
                # Select some superset
                superset = self.tail[self.tail.keys()[0]]
                return superset.lookup_superset(c, start + 1)
            else:
                return None

        if c[start] in self.tail:
            return self.tail[c[start]].lookup_superset(c, start + 1)

        # Let K0 be the largest element in TAIL such that K0 <= C[START]
        k0 = None
        for k in self.tail.keys():
            if (k0 is None or k > k0) and k <= c[start]:
                k0 = k

        if k0 is not None:
            return self.tail[k0].lookup_superset(c, start)

        return None

    def lookup_subset(self, c):
        """Return RESULT if there is some (C', RESULT) in the cache with
        C' being a subset of C or equal to C.  Otherwise, return None."""
        p = self
        for start in range(len(c)):
            if c[start] in p.tail:
                p = p.tail[c[start]]

        return p.result


# Main Delta Debugging algorithm.
class DD:
    # Delta debugging base class.  To use this class for a particular
    # setting, create a subclass with an overloaded `test()' method.
    #
    # Main entry points are:
    # - `ddmin()' which computes a minimal failure-inducing configuration, and
    # - `dd()' which computes a minimal failure-inducing difference.
    #
    # See also the usage sample at the end of this file.
    #
    # For further fine-tuning, you can implement an own `resolve()'
    # method (tries to add or remove configuration elements in case of
    # inconsistencies), or implement an own `split()' method, which
    # allows you to split configurations according to your own
    # criteria.
    #
    # The class includes other previous delta debugging alorithms,
    # which are obsolete now; they are only included for comparison
    # purposes.

    # Test outcomes.
    PASS = "PASS"
    FAIL = "FAIL"
    UNRESOLVED = "UNRESOLVED"

    # Resolving directions.
    ADD = "ADD"  # Add deltas to resolve
    REMOVE = "REMOVE"  # Remove deltas to resolve

    # Debugging output (set to 1 to enable)
    debug_test = 0
    debug_dd = 0
    debug_split = 0
    debug_resolve = 0

    def __init__(self):
        self.__resolving = 0
        self.__last_reported_length = 0
        self.monotony = 0
        self.outcome_cache = OutcomeCache()
        self.cache_outcomes = 1
        self.minimize = 1
        self.assume_axioms_hold = 1

    # Helpers
    def __listminus(self, c1, c2):
        """Return a list of all elements of C1 that are not in C2."""
        s2 = {}
        for delta in c2:
            s2[delta] = 1

        c = []
        for delta in c1:
            if delta not in s2:
                c.append(delta)

        return c

    def __listintersect(self, c1, c2):
        """Return the common elements of C1 and C2."""
        s2 = {}
        for delta in c2:
            s2[delta] = 1

        c = []
        for delta in c1:
            if delta in s2:
                c.append(delta)

        return c

    def __listunion(self, c1, c2):
        """Return the union of C1 and C2."""
        s1 = {}
        for delta in c1:
            s1[delta] = 1

        c = c1[:]
        for delta in c2:
            if delta not in s1:
                c.append(delta)

        return c

    def __listsubseteq(self, c1, c2):
        """Return 1 if C1 is a subset or equal to C2."""
        s2 = {}
        for delta in c2:
            s2[delta] = 1

        for delta in c1:
            if delta not in s2:
                return 0

        return 1

    # Output
    def coerce(self, c):
        """Return the configuration C as a compact string"""
        # Default: use printable representation
        return repr(c)

    def pretty(self, c):
        """Like coerce(), but sort beforehand"""
        sorted_c = c[:]
        sorted_c.sort()
        return self.coerce(sorted_c)

    # Testing
    def test(self, c):
        """Test the configuration C.  Return PASS, FAIL, or UNRESOLVED"""
        c.sort()

        # If we had this test before, return its result
        if self.cache_outcomes:
            cached_result = self.outcome_cache.lookup(c)
            if cached_result is not None:
                return cached_result

        if self.monotony:
            # Check whether we had a passing superset of this test before
            cached_result = self.outcome_cache.lookup_superset(c)
            if cached_result == self.PASS:
                return self.PASS

            cached_result = self.outcome_cache.lookup_subset(c)
            if cached_result == self.FAIL:
                return self.FAIL

        if self.debug_test:
            print()
            print("test(" + self.coerce(c) + ")...")

        outcome = self._test(c)

        if self.debug_test:
            print("test(" + self.coerce(c) + ") = " + repr(outcome))

        if self.cache_outcomes:
            self.outcome_cache.add(c, outcome)

        return outcome

    def _test(self, c):
        """Stub to overload in subclasses"""
        return self.UNRESOLVED  # Placeholder

    # Splitting
    def split(self, c, n):
        """Split C into [C_1, C_2, ..., C_n]."""
        if self.debug_split:
            print("split(" + self.coerce(c) + ", " + repr(n) + ")...")

        outcome = self._split(c, n)

        if self.debug_split:
            print("split(" + self.coerce(c) + ", " + repr(n) + ") = " + repr(outcome))

        return outcome

    def _split(self, c, n):
        """Stub to overload in subclasses"""
        subsets = []
        start = 0
        for i in range(n):
            subset = c[start:start + (len(c) - start) // (n - i)]
            subsets.append(subset)
            start = start + len(subset)
        return subsets

    # Resolving
    def resolve(self, csub, c, direction):
        """If direction == ADD, resolve inconsistency by adding deltas
           to CSUB.  Otherwise, resolve by removing deltas from CSUB."""

        if self.debug_resolve:
            print("resolve(" + repr(csub) + ", " + self.coerce(c) + ", " + repr(direction) + ")...")

        outcome = self._resolve(csub, c, direction)

        if self.debug_resolve:
            print("resolve(" + repr(csub) + ", " + self.coerce(c) + ", " + repr(direction) + ") = " + repr(outcome))

        return outcome

    def _resolve(self, csub, c, direction):
        """Stub to overload in subclasses."""
        # By default, no way to resolve
        return None

    # Test with fixes
    def test_and_resolve(self, csub, r, c, direction):
        """Repeat testing CSUB + R while unresolved."""

        initial_csub = csub[:]
        c2 = self.__listunion(r, c)

        csubr = self.__listunion(csub, r)
        t = self.test(csubr)

        # necessary to use more resolving mechanisms which can reverse each
        # other, can (but needn't) be used in subclasses
        self._resolve_type = 0

        while t == self.UNRESOLVED:
            self.__resolving = 1
            csubr = self.resolve(csubr, c, direction)

            if csubr is None:
                # Nothing left to resolve
                break

            if len(csubr) >= len(c2):
                # Added everything: csub == c2. ("Upper" Baseline)
                # This has already been tested.
                csubr = None
                break

            if len(csubr) <= len(r):
                # Removed everything: csub == r. (Baseline)
                # This has already been tested.
                csubr = None
                break

            t = self.test(csubr)

        self.__resolving = 0
        if csubr is None:
            return self.UNRESOLVED, initial_csub

        # assert t == self.PASS or t == self.FAIL
        csub = self.__listminus(csubr, r)
        return t, csub

    # Inquiries
    def resolving(self):
        """Return 1 while resolving."""
        return self.__resolving

    # Logging
    def report_progress(self, c, title):
        if len(c) != self.__last_reported_length:
            print()
            print(title + ": " + repr(len(c)) + " deltas left:", self.coerce(c))
            self.__last_reported_length = len(c)

    def test_mix(self, csub, c, direction):
        if self.minimize:
            (t, csub) = self.test_and_resolve(csub, [], c, direction)
            if t == self.FAIL:
                return (t, csub)

        return (t, csub)

    # Delta Debugging (new ISSTA version)
    def ddgen(self, c, minimize, maximize):
        """Return a 1-minimal failing subset of C"""

        self.minimize = minimize

        n = 2
        self.CC = c

        if self.debug_dd:
            print("dd(" + self.pretty(c) + ", " + repr(n) + ")...")

        outcome = self._dd(c, n)

        if self.debug_dd:
            print("dd(" + self.pretty(c) + ", " + repr(n) + ") = " + repr(outcome))

        return outcome

    def _dd(self, c, n):
        """Stub to overload in subclasses"""

        # assert self.test([]) == self.PASS

        run = 1
        cbar_offset = 0

        # We replace the tail recursion from the paper by a loop
        while 1:
            tc = self.test(c)
            # assert tc == self.FAIL or tc == self.UNRESOLVED # Comment this assertion, because we treat having the warning as PASS

            if n > len(c):
                # No further minimizing
                print("dd: done")
                return c

            self.report_progress(c, "dd")

            cs = self.split(c, n)

            print()
            print("dd (run #" + repr(run) + "): trying", end=' ')
            for i in range(n):
                if i > 0:
                    print("+", end=' ')
                print(len(cs[i]), end=' ')
            print()

            c_failed = 0
            cbar_failed = 0

            next_c = c[:]
            next_n = n

            # Check subsets
            for i in range(n):
                if self.debug_dd:
                    print("dd: trying", self.pretty(cs[i]))
                # do test here
                (t, cs[i]) = self.test_mix(cs[i], c, self.REMOVE)

                if t == self.FAIL:
                    # Found
                    if self.debug_dd:
                        print("dd: found", len(cs[i]), "deltas:", end=' ')
                        print(self.pretty(cs[i]))

                    c_failed = 1
                    next_c = cs[i]
                    next_n = 2
                    cbar_offset = 0
                    self.report_progress(next_c, "dd")
                    break

            if not c_failed:
                # Check complements
                cbars = n * [self.UNRESOLVED]

                # print("cbar_offset =", cbar_offset)

                for j in range(n):
                    i = (j + int(cbar_offset)) % n
                    cbars[i] = self.__listminus(c, cs[i])
                    t, cbars[i] = self.test_mix(cbars[i], c, self.ADD)

                    doubled = self.__listintersect(cbars[i], cs[i])
                    if doubled != []:
                        cs[i] = self.__listminus(cs[i], doubled)

                    if t == self.FAIL:
                        if self.debug_dd:
                            print("dd: reduced to", len(cbars[i]), end=' ')
                            print("deltas:", end=' ')
                            print(self.pretty(cbars[i]))

                        cbar_failed = 1
                        next_c = self.__listintersect(next_c, cbars[i])
                        next_n = next_n - 1
                        self.report_progress(next_c, "dd")

                        # In next run, start removing the following subset
                        cbar_offset = i
                        break

            if not c_failed and not cbar_failed:
                if n >= len(c):
                    # No further minimizing
                    print("dd: done")
                    return c

                next_n = min(len(c), n * 2)
                print("dd: increase granularity to", next_n)
                cbar_offset = (cbar_offset * next_n) / n

            c = next_c
            n = next_n
            run = run + 1

    def ddmin(self, c):
        return self.ddgen(c, 1, 0)

    def ddmax(self, c):
        return self.ddgen(c, 0, 1)

    def ddmix(self, c):
        return self.ddgen(c, 1, 1)
