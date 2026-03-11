use pyo3::{
    Py, Python,
    types::{PyAnyMethods, PyModule, PyModuleMethods},
};

/// Trait for attaching submodules to a PyModule and registering them in sys.modules for proper
/// import behavior.
pub trait PyModuleExt<'py> {
    /// self is going to
    /// be a base module.
    ///
    /// py - Python token
    /// to interact with python objects and modules.
    ///
    /// wrapped_submod - a function that generates
    /// a module.
    ///
    /// Typically, when used with #[pymodule],
    /// you need to wrap this module in pyo3::wrap_pymodule!(mod);
    ///
    /// Usage example:
    ///
    /// ```rust
    ///#[pymodule]
    ///pub mod inner_mod{
    ///  #[pymodule_export]
    ///  use super::Inner;
    ///}
    ///
    ///#[pymodule]
    ///pub mod outer_mod{
    ///
    ///  #[pymodule_export]
    ///  use super::Outer;
    ///
    ///  #[pymodule_init]
    ///  pub fn init(m: &Bound<'_, PyModule>) -> PyResult<()> {
    ///      m.attach_submodule_with_sys(m.py(), pyo3::wrap_pymodule!(super::inner_mod))?;
    ///  }
    ///}
    /// ```
    ///
    fn attach_submodule_with_sys<ModFN>(
        &self,
        py: Python<'py>,
        wrapped_submod: ModFN,
    ) -> pyo3::PyResult<()>
    where
        ModFN: Fn(Python<'py>) -> Py<PyModule>;
}

impl<'py, T> PyModuleExt<'py> for T
where
    T: PyModuleMethods<'py>,
{
    fn attach_submodule_with_sys<ModFN>(
        &self,
        py: Python<'py>,
        wrapped_submod: ModFN,
    ) -> pyo3::PyResult<()>
    where
        ModFN: Fn(Python<'py>) -> Py<PyModule>,
    {
        let submod = wrapped_submod(py).into_bound(py);
        self.add_submodule(&submod)?;
        let sys_name = format!(
            "{}.{}",
            self.name()?.extract::<String>()?,
            submod.name()?.extract::<String>()?,
        );
        py.import("sys")?
            .getattr("modules")?
            .set_item(sys_name, &submod)?;
        Ok(())
    }
}
