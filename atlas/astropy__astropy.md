CODE ATLAS for astropy/astropy — where past issues were actually fixed
(from this system's own resolved runs; treat as evidence, verify by reading — past fixes suggest, they do not decide)

- Modeling's `separability_matrix` does not compute separability correctly for nested CompoundModels
    -> astropy/modeling/separable.py, pyproject.toml
- In v5.3, NDDataRef mask propagation fails when one of the operand does not have a mask
    -> astropy/nddata/mixins/ndarithmetic.py, pyproject.toml
