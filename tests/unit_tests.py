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
        self.assertAlmostEqual(expected, result[0], 12)

    def __test_vector_function(self, function, filename):
        u = cs.SX.sym('u', 3)
        xi = cs.SX.sym('xi', 2)
        p = cs.SX.sym('p', 4)
        f = cs.norm_2(p) * cs.norm_1(xi) * function(u)
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
        self.assertAlmostEqual(expected, result[0], 12)

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

    def test_inv(self):
        self.__test_simple_function(cs.inv, 'inv')
        self.__test_simple_function(lambda x: 1/x, 'inv2')

    @staticmethod
    def __minus(x):
        return -x

    def test_minus(self):
        self.__test_simple_function(CrustUnitTest.__minus, 'minus')
        self.__test_simple_function(lambda x: -x, 'minus2')

    @staticmethod
    def __power(x, a):
        return x**a

    def test_power(self):
        for a in [-1, 2, 3, 4]:
            self.__test_simple_function(lambda x: CrustUnitTest.__power(x, a), 'pow')

    def test_if_else(self):
        self.__test_simple_function(lambda x: cs.if_else(x < 1, 2 * x, 3 * x), 'ifelse1')
        self.__test_simple_function(lambda x: cs.if_else(x < 0.4, -2 * x, -x), 'ifelse2')

    def test_norm_2(self):
        self.__test_vector_function(cs.norm_2, 'my_norm2')

    def test_norm_1(self):
        self.__test_vector_function(cs.norm_1, 'my_norm1')

    def test_norm_inf(self):
        self.__test_vector_function(cs.norm_inf, 'my_norm_inf')


if __name__ == '__main__':
    unittest.main()
