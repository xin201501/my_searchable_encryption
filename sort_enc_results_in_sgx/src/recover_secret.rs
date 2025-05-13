use pyo3::prelude::*;

// fn call_combine_secret_from_shares(
//     dealer: &PyAny,
//     shares: &PyAny,
//     secret_num: i32,
//     group_num: i32,
// ) -> PyResult<u128> {
//     Python::with_gil(|py| {
//         let lsss_module = PyModule::import(py, "LSSS")?;

//         // 显式创建参数元组
//         let args = (
//                 dealer,
//                 shares,
//                 secret_num,
//                 group_num,
//         );

//         // 调用函数
//         let result = lsss_module
//             .getattr("combine_secret_from_shares")?
//             .call1(args)?;

//         // 转换为 u128
//         let recovered_key: u128 = result.extract()?;
//         Ok(recovered_key)
//     })
// }

fn _c() -> PyResult<()> {
    Python::with_gil(|py| {
        let builtins = PyModule::import(py, "builtins")?;
        let total: i32 = builtins
            .getattr("sum")?
            .call1((vec![1, 2, 3],))?
            .extract()?;
        assert_eq!(total, 6);
        Ok(())
    })
}
