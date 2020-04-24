
# 
# Grammar
#
# (1) S -> AA
# (2) A -> aA
# (3) A -> b
# 
# Should recognize the regexp '^a*ba*b$'
# 
# State Table
#
# ╔═════════╤═══════════════════════════╤══════════════════╗
# ║  state  │           Action          │      Go To       ║
# ║         │    a        b       EOF   │    S        A    ║
# ╟─────────┼───────────────────────────┼──────────────────╢
# ║    0    │    S3       S4            │    1        2    ║
# ║    1    │                    accept │                  ║
# ║    2    │    S3       S4            │             5    ║
# ║    3    │    S3       S4            │             6    ║
# ║    4    │    R3       R3       R3   │                  ║
# ║    5    │    R1       R1       R1   │                  ║
# ║    6    │    R2       R2       R2   │                  ║
# ╚═════════╧═══════════════════════════╧══════════════════╝ 
# 
# I0 closure(S` -> .S)
# S` -> .S
# S -> .AA
# A -> .aA
# A -> .b
# 
# I1 (I0 | S) = closure(S` -> S.)
# S` -> S.
# 
# I2 (I0 | A) = closure(S -> A.A)
# S -> A.A
# A -> .aA
# A -> .b
# 
# I3 (I0 | a) = closure(A -> a.A)
# A -> a.A
# A -> .aA
# A -> .b
# 
# I4 (I0 | b) = closure(A -> b.)
# A -> b.
# 
# I5 (I2 | A) = closure(S -> AA.)
# S -> AA.
# 
# (I2 | a) = closure(A -> a.A) = I3
# (I2 | b) = closure(A -> b.)  = I4
# 
# I6 (I3 | A) = closure(A -> aA.)
# A -> aA.
# 
# (I3 | a) = closure(A -> a.A) = I3
# (I3 | b) = closure(A -> b.)  = I4
# 
# No other items have anything following the marker so we are done.
# 
# The part that says things like (I0 | A) is what gives the actions and gotos.
# A non=terminal means a goto, a terminal means a shift.
# Any items that have no symbols after the marker are reduce operations. 
# 
# 
# 
# When pushing to the state stack, check for a reduction rule in the state you are pushing on
# if there it is a reduction state, change the look ahead to look onto the stack instead of the
# next character.
#  


import json
import copy

# Grammar 0
#grammar = [
#    ('S`', 'S'),
#    ('S', 'A', 'A'),
#    ('A', '<a>', 'A'),
#    ('A', '<b>')
#]

# Grammar 1
grammar = [
    ('S`', 'Expr'),
    ('Expr', '<(>', 'Expr', '<)>'),
    ('Expr', 'Binary'),
    ('Expr', '<num>'),
    ('Binary', 'Expr', 'Op', 'Expr'),
    ('Op', '<+>'),
    ('Op', '<->'),
    ('Op', '<*>'),
    ('Op', '</>'),
]

# Grammar 2
#grammar = [
#    ('S`', 'Expr'),
#    ('Expr', '<(>', 'Expr', '<)>'),
#    ('Expr', 'Binary'),
#    ('Expr', 'Num'),
#    ('Binary', 'Expr', 'Op', 'Expr'),
#    ('Op', '<+>'),
#    ('Op', '<->'),
#    ('Op', '<*>'),
#    ('Op', '</>'),
#    ('Num', '<num>'),
#    ('Num', '<->', '<num>')
#]

# Item = [
#   production, 
#   marker, 
#   [
#       [production, marker],
#       [production, marker],
#       [production, marker],
#       [production, marker]
#   ]
# ]

def to_string(production):
    out = production[0] + ' ->'
    for part in production[1:]:
        out += ' ' + part
    return out

# All terminal symbols are surrounded by '<' and '>'
def is_non_terminal(part):
    if part[0] == '<' and part[-1] == '>':
        return False
    return True

# Returns the symbol directly following the marker if it exists.
# If the marker is at the end of the production it returns None
def get_symbol_after_marker(aug):
    if aug['marker'] < len(aug['production']):
        return aug['production'][aug['marker']]
    return None

# Augments the grammar by placing markers at the beginning of the RHS of each production
def augment_grammar(grammar):
    aug_grammar = []
    for production in grammar:
        aug_grammar.append({'production':production, 'marker':1})
    return aug_grammar

# Builds one closure over an augmented production for a given augmented grammar
def build_item(aug, prev, grammar):
    to_check = [aug]
    productions = [aug]
    added_symbols = []

    # Generate the list of productions in this item
    while len(to_check) > 0:
        # Get and remove the next item from the list of to be checked productions
        next = to_check.pop(0)
        # Get the symbol after the marker
        sym = get_symbol_after_marker(next)
        # If the symbol exists (not at the end) and it is a non-terminal
        if sym and is_non_terminal(sym) and sym not in added_symbols:
            # Add the symbol to the added symbols so we don't check it again in another production
            added_symbols.append(sym)
            # Add all the productions with that non-terminal to the productions and to_check list
            for prod in grammar:
                if prod['production'][0] == sym:
                    productions.append(prod)
                    to_check.append(prod)
    # Returns the single item state
    return {
        'closure':aug, # Represents closure(prod) ex: closure(S` -> .AA)
        'from':prev, # Represents how we got here
        'productions':productions
    }

# Returns a step as a dictionary for ease of readability and printing
def step(state, action, to, look_ahead):
    return {
        'state': state, 
        'action': action, 
        'to': to, 
        'look_ahead': look_ahead
    }

def get_look_ahead():
    pass

# Builds all the item states from a given augmented grammar
def build_item_set(grammar):
    items = [build_item(grammar[0], None, grammar)]
    closures = [items[0]['closure']]
    steps = []
    
    i = 0
    for item in items:
        productions = item['productions']
        for production in productions:
            sym = get_symbol_after_marker(production)
            if sym:
                # This is used for the 'from' part of subsequent items
                # Its read 'from item state number x given symbol y' where x and y are (x, y)
                prev = (i, sym)
                # Increment the marker (but it can't change the origional marker!)
                next = copy.copy(production)
                next['marker'] += 1
                # Don't build an item whos closure is already covered
                if next not in closures:
                    # Build the next item and add it to the list
                    items.append(build_item(next, prev, grammar))
                    # Add the closure so we don't do it again
                    closures.append(next)
                    # Check if its not a shift step
                    if next['marker'] >= len(next['production']):
                        if next['production'] == grammar[0]['production']:
                            # Add accept step
                            steps.append(step(len(items) - 1, '<EOF>', 'accept', None))
                        else:
                            # Add reduction step
                            steps.append(step(len(items) - 1, '<ALL>', 'reduce {}'.format(to_string(next['production'])), None))
                    # Add shift step associated with an item
                    steps.append(step(i, sym, len(items) - 1, None))
                else:
                    # Add a shift step that would have created a redundant item
                    steps.append(step(i, sym, closures.index(next), None))
                
                # Add look ahead to non-terminal steps
                if steps[-1]['action'] == sym and is_non_terminal(sym):
                    steps[-1]['look_ahead'] = None
        # Increment iterator for prev
        i += 1

    print(json.dumps(steps, indent=4))
    return (closures, len(items), steps)

def gen_table(num_states, steps, actions, gotos):
    table = []

    # Setup label row
    table.append(['state'])
    for action in actions:
        table[0].append(action)
    for goto in gotos:
        table[0].append(goto)

    # Fill table so we can just access by index
    for i in range(num_states):
        table.append([])
        table[i + 1].append(i)
        for action in actions:
            table[i + 1].append('')
        for goto in gotos:
            table[i + 1].append('')

    # Add step data
    for step in steps:
        if is_non_terminal(step['action']):
            # Non-Terminals go in the GoTo section
            index = 1 + len(actions) + gotos.index(step['action'])
        else:
            # Terminals go in the Action section
            index = 1 + actions.index(step['action'])
        # If data is present at a location, append it with a /
        data = str(step['to'])
        if table[step['state'] + 1][index] != '':
            data = table[step['state'] + 1][index] + '/' + data
        # Put the data in the table at the right indicies
        table[step['state'] + 1][index] = data
    return table

def pretty_print_table(matrix):
    s = [[str(e) for e in row] for row in matrix]
    lens = [max(map(len, col)) for col in zip(*s)]
    fmt = '\t'.join('{{:{}}}'.format(x) for x in lens)
    table = [fmt.format(*row) for row in s]
    print('\n'.join(table))

def collect_actions_and_gotos(grammar):
    actions = ['<EOF>', '<ALL>']
    gotos = []

    for production in grammar:
        for part in production:
            if part != 'S`':
                if is_non_terminal(part):
                    if part not in gotos:
                        gotos.append(part)
                else:
                    if part not in actions:
                        actions.append(part)
    return (actions, gotos)

if __name__ == '__main__':
    aug_grammar = augment_grammar(grammar)
    (closures, num_states, steps) = build_item_set(aug_grammar)
    (actions, gotos) = collect_actions_and_gotos(grammar)
    table = gen_table(num_states, steps, actions, gotos)
    pretty_print_table(table)
