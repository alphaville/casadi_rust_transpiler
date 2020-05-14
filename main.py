import crust_casadi as cc
import casadi.casadi as cs


# --- CasADi: Create function
u = cs.SX.sym('u', 4)
xi = cs.SX.sym('xi', 2)
p = cs.SX.sym('p', 2)
x = cs.norm_2(u)
f = cs.norm_2(x)
fun = cs.Function('f', [u, xi, p], [cs.gradient(f, u)])
print(fun.size_out(0))

fname = 'xcst_kangaroo'
transpiler = cc.CasadiRustTranspiler(fun, fname)
transpiler.transpile()

# --- Compile and call
(u, xi, p) = ([1, 2, 3, 4], [4, 5], [6, 7])
expected = fun(u, xi, p)
transpiler.compile()

print(expected)

result = transpiler.call_rust(u, xi, p)
print(result)
