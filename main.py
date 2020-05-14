import crust_casadi as cc
import casadi.casadi as cs
import shutil
import subprocess
import json


# --- CasADi: Create function
u = cs.SX.sym('u', 3)
xi = cs.SX.sym('xi', 2)
p = cs.SX.sym('p', 2)
f = cs.sin(cs.norm_2(p))*cs.dot(xi, p)*cs.norm_2(u)
fun = cs.Function('f', [u, xi, p], [f])

fname = 'xcst_kangaroo'
transpiler = cc.CasadiRustTranspiler(fun, fname)
transpiler.transpile()

# --- Compile and call
expected = fun([1, 2, 3], [4, 5], [6, 7])
transpiler.compile()

expected = fun([1, 2, 3], [4, 5], [6, 7])
print(expected)

result = transpiler.call_rust([1, 2, 3], [4, 5], [6, 7])
