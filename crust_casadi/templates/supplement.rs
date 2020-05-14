fn str_to_arr(x: &String) -> Vec<f64> {
    return x
        .trim_matches(|c| c == '[' || c == ']')
        .split(',')
        .map(|n| n.trim().parse().unwrap())
        .collect();
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
	if args.len() < 4 {
		panic!("Incorrect number of arguments");
	}
    let u = str_to_arr(&args[1]);
    let xi = str_to_arr(&args[2]);
    let p = str_to_arr(&args[3]);
    let x = &[&u[..], &xi[..], &p[..]];
    let res0 = &mut [0.0; {{sz.results}}];
    let res = &mut [&mut res0[..]];
    let mut wspace = Vec::new();
    let mut iwspace = Vec::new();
    {{casadi_function_name}}(x, res, &mut wspace, &mut iwspace);
    println!("{:?}", res[0])
}
