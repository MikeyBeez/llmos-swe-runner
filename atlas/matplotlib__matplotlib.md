CODE ATLAS for matplotlib/matplotlib — where past issues were actually fixed
(from this system's own resolved runs; treat as evidence, verify by reading — past fixes suggest, they do not decide)

- [Bug]: ax.bar raises for all-nan data on matplotlib 3.6.1 
    -> lib/matplotlib/cbook/__init__.py
- Error creating AxisGrid with non-default axis class
    -> lib/mpl_toolkits/axes_grid1/axes_grid.py
- xlim_changed not emitted on shared axis
    -> lib/matplotlib/axis.py
- [Bug]: set_visible() not working for 3d projection 
    -> lib/mpl_toolkits/mplot3d/axes3d.py
- 'Poly3DCollection' object has no attribute '_facecolors2d'
    -> lib/mpl_toolkits/mplot3d/art3d.py
- legend draggable as keyword
    -> lib/matplotlib/legend.py
- [Bug]: Text label with empty line causes a "TypeError: cannot unpack non-iterable NoneType object" i
    -> lib/matplotlib/backends/backend_ps.py
- [Bug]: Constrained layout UserWarning even when False
    -> lib/matplotlib/figure.py
- [Bug]: NumPy 1.24 deprecation warnings
    -> lib/matplotlib/colors.py
- [Bug]: using clf and pyplot.draw in range slider on_changed callback blocks input to widgets
    -> lib/matplotlib/figure.py
- [Bug]: Attribute Error combining matplotlib 3.7.1 and mplcursor on data selection
    -> lib/matplotlib/offsetbox.py
- Update colorbar after changing mappable.norm
    -> lib/matplotlib/colorbar.py
