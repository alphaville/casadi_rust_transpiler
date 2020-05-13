from pycparser import c_ast, c_generator, parse_file


class Parser:

    def __init__(self, fname):
        ast = parse_file(fname, use_cpp=True, cpp_path='clang',
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

    def __init__(self):
        pass
