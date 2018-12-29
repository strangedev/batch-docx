class SyntaxNode():

    def __init__(self, name,  data):
        self.name = name
        self.data = data


def intersperse(iterable, delimiter):
    it = iter(iterable)
    yield next(it)
    for x in it:
        yield delimiter
        yield x


def takeWhile(iter, c):
    for x in iter:
        if c(x): yield x
        else: break


def parse_word(stream):
    return SyntaxNode("word", "".join(intersperse(stream, " ")).replace("$_", " ").replace("$.", ""))


def parse_operator(stream):
    if len(stream) != 1:
        return None

    op = stream[0]

    if op in ["!=", "=="]:
        return SyntaxNode("operator", op)

    return None


def parse_statement(stream):
    if len(stream) != 3:
        return None

    wordl = parse_word([stream[0]])
    wordr = parse_word([stream[2]])
    op = parse_operator([stream[1]])

    if not op:
        return False

    return SyntaxNode("statement", (wordl, op, wordr))


def parse_ifclause(stream):
    if len(stream) < 6:
        return None

    if stream.pop(0) != "$if":
        return None

    statement_stream = list(takeWhile(stream, lambda x: x != ":"))
    stream = stream[len(statement_stream):]

    if stream.pop(0) != ":":
        return None

    expression_true_stream = list(takeWhile(stream, lambda x: x != "$else:"))
    stream = stream[len(expression_true_stream):]

    if stream.pop(0) != "$else:":
        return None

    statement = parse_statement(statement_stream)
    expression_true = parse_expression(expression_true_stream)
    expression_false = parse_expression(stream)

    if not all([statement, expression_true, expression_false]):
        return None

    return SyntaxNode("ifclause", (statement, expression_true, expression_false))


def parse_expression(stream):

    ifclause = parse_ifclause(stream)
    return ifclause if ifclause else parse_word(stream)


def parse_template_lang(astring):
    stream = astring.split()
    return parse_expression(stream)


def eval_ifclause(node, bindings):

    operandl = bindings[node.data[0].data[0].data]
    operandr = node.data[0].data[2].data
    operator = node.data[0].data[1].data

    nodel = node.data[1]
    noder = node.data[2]

    if operator == "==":
        return nodel if operandl == operandr else noder

    return nodel if operandl != operandr else noder


def eval_template_lang(astring, bindings):

    root = parse_template_lang(astring)

    if not root:
        return "Syntaxfehler in Zuweisung!"

    current_node = None
    next_node = root

    while next_node:
        current_node = next_node
        next_node = None

        if current_node.name == "ifclause":
            next_node = eval_ifclause(current_node, bindings)

    return current_node.data