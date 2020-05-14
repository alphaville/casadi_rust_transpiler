fn str_to_arr(x: &String) -> Vec<f64> {
    return x
        .trim_matches(|c| c == '[' || c == ']')
        .split(',')
        .map(|n| n.trim().parse().unwrap())
        .collect();
}


fn main() {
    /// Note: Always: 3 inputs, 1 output
    ///
    const DIM_RES: usize = {{sz.result_dim[0]}};
    const DIM_WSPACE: usize = {{sz.wspace}};
    const DIM_IWSPACE: usize = {{sz.result_dim[0]}};

    let args: Vec<String> = std::env::args().collect();
	if args.len() < 4 {
		panic!("Incorrect number of arguments");
	}

    let u: Vec<f64> = str_to_arr(&args[1]);
    let xi: Vec<f64> = str_to_arr(&args[2]);
    let p: Vec<f64> = str_to_arr(&args[3]);
    let x = &[&u[..], &xi[..], &p[..]];

    let mut res0 = [0.0; DIM_RES];
    let res = &mut [&mut res0[..]];

    let mut wspace = Vec::with_capacity(DIM_WSPACE);
    let mut iwspace = Vec::with_capacity(DIM_IWSPACE);
    {{casadi_function_name}}(x,
                             res,
                             &mut wspace,
                             &mut iwspace);
    println!("{:?}", res[0])
}
