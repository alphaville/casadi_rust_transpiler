from pycparser import c_ast, c_generator, parse_file
import re
import pkg_resources
import jinja2
import subprocess
import shutil
import json
import os

__all__ = ['CasadiRustTranspiler']


def make_dir_if_not_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


class Parser:

    def __init__(self, filename):
        fake_lib_path = pkg_resources.resource_filename('crust_casadi', 'utils/fake')
        ast = parse_file(filename, use_cpp=True,
                         cpp_args=['-E', '-I'+fake_lib_path])
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
    __CRUST_DEFAULT_INIT = {'double': 0.0, 'int': 0, 'long': 0}
    __CRUST_FUNCTION_MAP = {'cos': 'f64::cos',
                            'sin': 'f64::sin',
                            'tan': 'f64::tan',
                            'exp': 'f64::exp',
                            'acos': 'f64::acos',
                            'asin': 'f64::asin',
                            'atan': 'f64::atan',
                            'fabs': 'f64::abs',
                            'sqrt': 'f64::sqrt'}

    def __init__(self, file_name, casadi_function, function_name='casadi'):
        parser = Parser(file_name)
        self.f = parser.get_function_by_name(function_name)
        self.code = None
        self.file_name = file_name
        self.function_name = function_name
        self.casadi_function = casadi_function

    @staticmethod
    def __crust_function_mapping(fname):
        p = re.compile('[a-z_]+_fmax', re.IGNORECASE)
        if p.match(fname) is not None:
            return 'f64::max'
        p = re.compile('[a-z_]+_fmin', re.IGNORECASE)
        if p.match(fname) is not None:
            return 'f64::min'
        p = re.compile('[a-z_]+_sign', re.IGNORECASE)
        if p.match(fname) is not None:
            return 'f64::signum'
        return Crust.__CRUST_FUNCTION_MAP[fname]

    @staticmethod
    def __declaration_to_rust(dec):
        var_name = dec.name
        var_type = dec.type.type.names[0]
        var_init = Crust.__CRUST_DEFAULT_INIT[var_type] if dec.init is None else dec.init.value
        rust_type = Crust.__CRUST_TYPES[var_type]
        return 'let mut %s: %s = %s;' % (var_name, rust_type, var_init)


    @staticmethod
    def __unwrap(node):
        if isinstance(node, c_ast.ID):
            return node.name
        elif isinstance(node, c_ast.Constant):
            return node.value
        else:
            raise Exception("Unknown node type")

    @staticmethod
    def __assignment_to_rust(dec):
        var_name = dec.lvalue.name
        rhs = dec.rvalue
        stmt = var_name + ' = '
        generator = c_generator.CGenerator()
        if isinstance(rhs, c_ast.BinaryOp):
            operator = rhs.op
            op_left = Crust.__unwrap(rhs.left)
            op_right = Crust.__unwrap(rhs.right)
            if operator in ['<=', '>=', '==', '<', '>']:
                stmt += 'if %s %s %s {1.0} else {0.0}' \
                        % (op_left, operator, op_right)
            else:
                stmt += op_left + operator + op_right
        elif isinstance(rhs, c_ast.FuncCall):
            fname = rhs.name.name
            p = re.compile('[a-z_]+_[a-z]+_sq', re.IGNORECASE)
            if p.match(fname) is not None:
                stmt += 'f64::powi(' + Crust.__unwrap(rhs.args.exprs[0]) + ', 2)'
            else:
                fname = Crust.__crust_function_mapping(fname)
                args = ",".join([Crust.__unwrap(x) for x in rhs.args.exprs])
                stmt += '%s(%s)' % (fname, args)
        elif isinstance(rhs, c_ast.Constant):
            stmt += generator.visit(rhs)
        elif isinstance(rhs, c_ast.TernaryOp):
            stmt += generator.visit(rhs.iftrue)
        elif isinstance(rhs, c_ast.UnaryOp):
            rhs_var = Crust.__unwrap(rhs.expr)
            if rhs.op == '!':
                stmt += " if f64::abs(%s) < f64::EPSILON { 1.0 } else { 0.0 }" \
                        % rhs_var
            else:
                stmt += rhs.op + rhs_var
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

    @staticmethod
    def __get_template(name):
        fake_lib_path = pkg_resources.resource_filename('crust_casadi', 'templates')
        file_loader = jinja2.FileSystemLoader(fake_lib_path)
        env = jinja2.Environment(loader=file_loader, autoescape=True)
        return env.get_template(name)

    def parse(self):
        function = self.f
        node_body = function.body
        self.code = Crust.__crust(blocks=node_body.block_items)

    def to_rust_file(self, file_name=None, casadi_function_name='casadi'):
        tmpl_supplement = Crust.__get_template("supplement.rs")
        sizes = {'results': self.casadi_function.sz_res(),
                 'args': self.casadi_function.sz_arg(),
                 'wspace': self.casadi_function.sz_w(),
                 'iwspace': self.casadi_function.sz_iw(),
                 'result_dim': self.casadi_function.size_out(0),
                 'args_dims': [self.casadi_function.size_in(i) for i in range(3)],
                 }
        tmpl_supplement_out = tmpl_supplement.render(sz=sizes,
                                                     casadi_function_name=casadi_function_name,
                                                     file_name=file_name)

        with open(file_name, "w") as fh:
            fh.write("#[allow(unused_assignments)]\n"
                     "fn %s(\n\targ: &[&[f64]],\n\tres: &mut [&mut [f64]],\n\t"
                     "_real_workspace: &mut [f64],\n\t_int_workspace: &mut [i64],\n) -> u16 {\n\t"
                     % casadi_function_name)
            fh.write("\n\t".join(self.code))
            fh.write("\n}\n\n")
            fh.write(tmpl_supplement_out)


class CasadiRustTranspiler:

    def __init__(self,
                 casadi_function,
                 function_alias,
                 rust_dir='rust',
                 c_dir='c'):
        self.casadi_function = casadi_function
        self.function_alias = function_alias
        self.rust_dir = rust_dir
        self.c_dir = c_dir
        make_dir_if_not_exists(c_dir)
        make_dir_if_not_exists(rust_dir)

    def transpile(self, rust_function_name=None):
        # 1. Generate C file and move to c/
        c_file_name = '%s.c' % self.function_alias
        c_file_path = '%s/%s' % (self.c_dir, c_file_name)
        self.casadi_function.generate(c_file_name)
        shutil.move(c_file_name, c_file_path)

        function_name = '%s_f0' % self.function_alias
        crust = Crust(c_file_path, self.casadi_function, function_name)
        crust.parse()
        the_rust_function_name = self.function_alias if rust_function_name is None else rust_function_name
        crust.to_rust_file("%s/%s.rs" % (self.rust_dir, self.function_alias),
                           the_rust_function_name)

    def compile(self):
        command = ["rustc", "%s.rs" % self.function_alias]
        p = subprocess.Popen(command, cwd=self.rust_dir, stdout=subprocess.PIPE)
        p.communicate()
        rc = p.returncode
        return rc == 0

    def call_rust(self, *args):
        command = ["./%s" % self.function_alias, *[str(x) for x in args]]
        p = subprocess.Popen(command, cwd=self.rust_dir, stdout=subprocess.PIPE)
        p.wait()
        line = p.stdout.readline()
        result = json.loads(line.rstrip().decode('utf-8'))
        p.stdout.close()
        return result
