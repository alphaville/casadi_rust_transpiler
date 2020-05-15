import unittest
import crust_casadi as cc
import casadi.casadi as cs


class CrustIntegrationTest(unittest.TestCase):

    def test_integration_1(self):
        u = cs.SX.sym('u', 3)
        xi = cs.SX.sym('xi', 2)
        p = cs.SX.sym('p', 2)
        f = cs.sin(cs.norm_2(p)) * cs.dot(xi, p) * cs.norm_2(u)
        fun = cs.Function('f', [u, xi, p], [f])

        transpiler = cc.CasadiRustTranspiler(fun, 'xcst_kangaroo')
        transpiler.transpile()
        self.assertTrue(transpiler.compile())

        (u, xi, p) = ([1, 2, 3], [4, 5], [6, 7])
        expected = fun(u, xi, p)
        result = transpiler.call_rust(u, xi, p)
        self.assertAlmostEqual(expected, result[0], 8)

    def test_integration_2(self):
        u = cs.SX.sym('u', 3)
        xi = cs.SX.sym('xi', 2)
        p = cs.SX.sym('p', 2)
        f = cs.sin(cs.norm_2(p)) * cs.dot(xi, p)**2 * cs.norm_2(u)
        f = 1/f
        df = cs.gradient(f, u)
        fun = cs.Function('df', [u, xi, p], [df])

        transpiler = cc.CasadiRustTranspiler(fun, 'xcst_panda')
        transpiler.transpile()
        self.assertTrue(transpiler.compile())

        (u, xi, p) = ([1, 2, 3], [4, 5], [6, 7])
        expected = fun(u, xi, p)
        result = transpiler.call_rust(u, xi, p)

        for i in range(3):
            self.assertAlmostEqual(expected[i], result[i], 8)


if __name__ == '__main__':
    unittest.main()
