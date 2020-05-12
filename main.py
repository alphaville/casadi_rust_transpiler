from __future__ import print_function
import re
import sys

from pycparser import c_parser, c_ast, c_generator, parse_file


def get_function_from_ast(ast, function_name):
    ast_ext = ast.ext
    node = []
    for n in ast_ext:
        if isinstance(n, c_ast.FuncDef) and n.decl.name == function_name:
            node = n
    return node


crust_types = {'double': 'f64'}
crust_default_init = {'double': 0.0, 'int': 0}
crust_function_map = {'cos': 'f64::cos',
                      'sin': 'f64::sin',
                      'sqrt': 'f64::sqrt'}


def crust_function_mapping(fname):
    p = re.compile('phi_[a-z]+_fmax', re.IGNORECASE)
    if p.match(fname) is not None:
        return 'f64::max'
    return crust_function_map[fname]


def declaration_to_rust(dec):
    assert(isinstance(dec, c_ast.Decl))
    var_name = dec.name
    var_type = dec.type.type.names[0]
    var_init = crust_default_init[var_type] if dec.init is None else dec.init.value
    rust_type = crust_types[var_type]
    return 'let mut %s: %s = %s;' % (var_name, rust_type, var_init)


def assignment_to_rust(dec):
    assert (isinstance(dec, c_ast.Assignment))
    var_name = dec.lvalue.name
    rhs = dec.rvalue
    stmt = var_name + ' = '
    generator = c_generator.CGenerator()
    if isinstance(rhs, c_ast.BinaryOp):
        operator = rhs.op
        op_left = rhs.left.name
        op_right = rhs.right.name
        stmt += op_left + operator + op_right
    elif isinstance(rhs, c_ast.FuncCall):
        fname = rhs.name.name
        p = re.compile('phi_[a-z]+_sq', re.IGNORECASE)
        if p.match(fname) is not None:
            stmt += 'f64::powi(' + rhs.args.exprs[0].name + ', 2)'
        else:
            fname = crust_function_mapping(fname)
            args = ",".join([x.name for x in rhs.args.exprs])
            stmt += '%s(%s)' %(fname, args)
    elif isinstance(rhs, c_ast.Constant):
        stmt += generator.visit(rhs)
    elif isinstance(rhs, c_ast.TernaryOp):
        stmt += generator.visit(rhs.iftrue)
    return stmt + ';'


def crust(blocks):
    for node in blocks:
        if isinstance(node, c_ast.Decl):
            stmt = declaration_to_rust(node)
        elif isinstance(node, c_ast.Assignment):
            stmt = assignment_to_rust(node)
        print(stmt)


ast = parse_file('c/xcst_belfast.c', use_cpp=True, cpp_path='clang',
                 cpp_args=['-E', r'-Iutils/fake'])


f0 = get_function_from_ast(ast, 'phi_ZPljYgYgKSBLjmbdpTRb_f0')

node_body = f0.body
f_block_items = node_body.block_items


d0 = node_body.block_items[0]
declaration_to_rust(d0)

# 36: fmax
# 37: sq
# 41: division
d0 = node_body.block_items[28]
print(d0)
assignment_to_rust(d0)

crust(blocks=node_body.block_items)