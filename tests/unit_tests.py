import unittest
import crust_casadi as cc
import casadi.casadi as cs


class CrustUnitTest(unittest.TestCase):

    def __test_simple_function(self, function, filename):
        u = cs.SX.sym('u', 3)
        xi = cs.SX.sym('xi', 2)
        p = cs.SX.sym('p', 4)
        f = cs.sum1(p) * cs.sum1(xi) * function(cs.sum1(u))
        fun = cs.Function('f', [u, xi, p], [f])

        transpiler = cc.CasadiRustTranspiler(casadi_function=fun,
                                             function_alias=filename,
                                             rust_dir='tests/rust',
                                             c_dir='tests/c')
        transpiler.transpile()
        self.assertTrue(transpiler.compile())

        (u, xi, p) = ([0.1, 0.2, 0.3], [4, 5], [6, 7, 8, 9])
        expected = fun(u, xi, p)
        result = transpiler.call_rust(u, xi, p)
        self.assertAlmostEqual(expected, result[0], 8)

    def test_sin(self):
        self.__test_simple_function(cs.sin, 'sin')

    def test_cos(self):
        self.__test_simple_function(cs.cos, 'cos')

    def test_tan(self):
        self.__test_simple_function(cs.tan, 'tan')

    def test_exp(self):
        self.__test_simple_function(cs.exp, 'exp')

    def test_sqrt(self):
        self.__test_simple_function(cs.sqrt, 'sqrt')

    def test_signum(self):
        self.__test_simple_function(cs.sign, 'signum')

    def test_acos(self):
        self.__test_simple_function(cs.acos, 'acos')

    def test_asin(self):
        self.__test_simple_function(cs.asin, 'asin')

    def test_atan(self):
        self.__test_simple_function(cs.atan, 'atan')

    def test_abs(self):
        self.__test_simple_function(cs.fabs, 'abs')


if __name__ == '__main__':
    unittest.main()
