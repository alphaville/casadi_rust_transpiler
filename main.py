import crust_casadi as cc

file_name = 'c/xgrd_belfast.c'
function_name = 'grad_phi_ZPljYgYgKSBLjmbdpTRb_f0'
crust = cc.Crust(file_name, function_name)
crust.parse()
crust.to_rust_file("rust/rusty_function.rs")
