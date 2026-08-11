- Seaborn IS matplotlib: nothing is observable until the figure draws.
  The matplotlib rule applies verbatim -- force a draw (fig.canvas.draw()
  or savefig to a BytesIO) before asserting, and use the Agg backend.
  Seaborn plotting functions return the matplotlib Axes (or a FacetGrid
  holding .figure); assert on post-draw state of those objects.
- Categorical/statistical transforms happen at PLOT time: the numbers to
  assert on live in the drawn artists (collections, patches, lines), not
  in the input dataframe. ax.collections / ax.patches after a draw is
  where the evidence is.
