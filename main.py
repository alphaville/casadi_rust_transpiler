import crust_casadi as cc
import casadi.casadi as cs


u = cs.SX.sym('u', 3)
xi = cs.SX.sym('xi', 2)
p = cs.SX.sym('p', 4)
y = cs.sum1(u)
f = cs.sum1(p) * cs.sum1(xi) * cs.if_else(y <= 1, 2*y, 3*y)
fun = cs.Function('f', [u, xi, p], [f])

transpiler = cc.CasadiRustTranspiler(casadi_function=fun,
                                     function_alias='ifelse0x100',
                                     rust_dir='tests/rust',
                                     c_dir='tests/c')
transpiler.transpile()
transpiler.compile()

(u, xi, p) = ([0.1, 0.2, 0.3], [4, 5], [6, 7, 8, 9])
expected = fun(u, xi, p)
result = transpiler.call_rust(u, xi, p)
