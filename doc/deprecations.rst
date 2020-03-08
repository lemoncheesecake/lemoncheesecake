.. _deprecations:

Deprecations
============

Deprecations may come over new releases. In that case, backward-compatibility will be maintained (at least) until the
next major release, example: something deprecated in version 1.2.0 will continue to work in all 1.x versions coming afterward
until version 2.0.0.

Deprecated in 1.4.5
-------------------

- the ``detached_step`` context manager (whose purpose is to create steps in new threads) has been deprecated; the
  ``set_step`` function can now be used in any context (main thread or new threads)
- the ``detached`` argument of the ``set_step`` is now deprecated
- the ``at_each_event`` option of ``lcc run --save-report`` has been deprecated/renamed in favor of ``at_each_log``

Deprecated in 1.1.0
-------------------

- ``MatchDescriptionTransformer`` has been deprecated/renamed in favor of ``MatcherDescriptionTransformer``