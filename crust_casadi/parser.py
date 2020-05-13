from pycparser import c_ast, c_generator, parse_file
import re
__all__ = ['Crust']


class Parser:

    def __init__(self, filename):
        # TODO: Change -Iutils/fake - use pkg_resources
        ast = parse_file(filename, use_cpp=True,
                         cpp_args=['-E', r'-Iutils/fake'])
        self.ast = ast

    def get_function_by_name(self, function_name):
        ast_ext = self.ast.ext
        node = []
        for n in ast_ext:
            if isinstance(n, c_ast.FuncDef) and n.decl.name == function_name:
                node = n
        return node


class Crust:

    __CRUST_TYPES = {'double': 'f64',
                     'int': 'i32',
                     'long': 'i64'}
    __CRUST_DEFAULT_INIT = {'double': 0.0, 'int': 0}
    __CRUST_FUNCTION_MAP = {'cos': 'f64::cos',
                            'sin': 'f64::sin',
                            'tan': 'f64::tan',
                            'sqrt': 'f64::sqrt'}

    def __init__(self, file_name, function_name):
        parser = Parser(file_name)
        self.f = parser.get_function_by_name(function_name)
        self.code = None

    @staticmethod
    def __crust_function_mapping(fname):
        p = re.compile('[a-z_]+_[a-z]+_fmax', re.IGNORECASE)
        if p.match(fname) is not None:
            return 'f64::max'
        return Crust.__CRUST_FUNCTION_MAP[fname]

    @staticmethod
    def __declaration_to_rust(dec):
        var_name = dec.name
        var_type = dec.type.type.names[0]
        var_init = Crust.__CRUST_DEFAULT_INIT[var_type] if dec.init is None else dec.init.value
        rust_type = Crust.__CRUST_TYPES[var_type]
        return 'let mut %s: %s = %s;' % (var_name, rust_type, var_init)

    @staticmethod
    def __assignment_to_rust(dec):
        var_name = dec.lvalue.name
        rhs = dec.rvalue
        stmt = var_name + ' = '
        generator = c_generator.CGenerator()
        if isinstance(rhs, c_ast.BinaryOp):
            operator = rhs.op
            op_left = rhs.left.name
            op_right = rhs.right.name
            if operator in ['<=', '>=', '==', '<', '>']:
                stmt += 'if %s %s %s {1.0} else {0.0}' \
                        % (op_left, operator, op_right)
            else:
                stmt += op_left + operator + op_right
        elif isinstance(rhs, c_ast.FuncCall):
            fname = rhs.name.name
            p = re.compile('[a-z_]+_[a-z]+_sq', re.IGNORECASE)
            if p.match(fname) is not None:
                stmt += 'f64::powi(' + rhs.args.exprs[0].name + ', 2)'
            else:
                fname = Crust.__crust_function_mapping(fname)
                args = ",".join([x.name for x in rhs.args.exprs])
                stmt += '%s(%s)' % (fname, args)
        elif isinstance(rhs, c_ast.Constant):
            stmt += generator.visit(rhs)
        elif isinstance(rhs, c_ast.TernaryOp):
            stmt += generator.visit(rhs.iftrue)
        elif isinstance(rhs, c_ast.UnaryOp):
            if rhs.op == '!':
                rhs_var = rhs.expr.name
                stmt += " if f64::abs(%s) < f64::EPSILON { 1.0 } else { 0.0 }" \
                        % rhs_var
        return stmt + ';'

    @staticmethod
    def __ifblock_to_rust(dec):
        generator = c_generator.CGenerator()
        return generator.visit(dec.iftrue) + ';'

    @staticmethod
    def __crust(blocks):
        code = []
        for node in blocks:
            if isinstance(node, c_ast.Decl):
                stmt = Crust.__declaration_to_rust(node)
            elif isinstance(node, c_ast.Assignment):
                stmt = Crust.__assignment_to_rust(node)
            elif isinstance(node, c_ast.If):
                stmt = Crust.__ifblock_to_rust(node)
            elif isinstance(node, c_ast.Return):
                stmt = "return 0;"
            code += [stmt]
        return code

    def parse(self):
        function = self.f
        node_body = function.body
        self.code = Crust.__crust(blocks=node_body.block_items)

    def to_rust_file(self, file_name):
        with open(file_name, "w") as fh:
            fh.write("#[allow(unused_assignments)]\n"
                     "fn casadi(arg: &[&[f64]], res: &mut [&mut [f64]]) -> u16 {\n\t")
            fh.write("\n\t".join(self.code))
            fh.write("\n}\n")
