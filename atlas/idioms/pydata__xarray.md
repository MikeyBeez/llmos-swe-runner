- Assert on .values (numpy) with numpy.testing.assert_allclose or
  assert_identical from xarray.testing -- == on DataArrays returns an
  array, and truthiness of it raises, so a naive assert observes nothing.
- repr/formatting bugs: the observable is the STRING repr(obj) -- assert
  on a stable substring of it.
- Lazy operations compute at access time: force computation (.values,
  .compute(), .load()) before asserting, or the buggy path never runs --
  the xarray analogue of matplotlib draw-before-assert.
