"""Four-state logic with a compatible boolean projection and complete, unpruned trace."""
from decimal import Decimal

LOGIC_VERSION = 'four-state-1'

def number(v): return type(v) in (int, float, Decimal)

def compare(actual, op, expected):
    if isinstance(expected, bool):
        if not isinstance(actual, bool): return None
    elif number(expected):
        if not number(actual): return None
        actual, expected = Decimal(str(actual)), Decimal(str(expected))
        if not actual.is_finite() or not expected.is_finite(): return None
    elif type(actual) != type(expected): return None
    operations = {'==': lambda: actual == expected, '!=': lambda: actual != expected,
                  '>=': lambda: actual >= expected, '>': lambda: actual > expected,
                  '<=': lambda: actual <= expected, '<': lambda: actual < expected}
    if op not in operations: raise ValueError('UNSUPPORTED_OPERATOR')
    return operations[op]()

def combine(operator, states):
    if not states: raise ValueError('EMPTY_LOGIC')
    if operator not in ('all_of', 'any_of'): raise ValueError('UNSUPPORTED_LOGIC_OPERATOR')
    decisive = 'FALSE' if operator == 'all_of' else 'TRUE'
    if decisive in states: return decisive
    if 'INVALID' in states: return 'INVALID'
    if 'UNKNOWN' in states: return 'UNKNOWN'
    return 'TRUE' if operator == 'all_of' else 'FALSE'

def tree(node, values, invalid=None, path='root'):
    invalid = invalid or {}
    operators = [o for o in ('all_of', 'any_of') if o in node]
    if len(operators)>1: raise ValueError('AMBIGUOUS_LOGIC_NODE')
    if operators:
        operator = operators[0]
        children = [tree(n, values, invalid, f'{path}/{i}') for i,n in enumerate(node[operator])]
        truth = combine(operator, [n['truth_state'] for n in children])
        return {'operator':operator,'state':{'TRUE':True,'FALSE':False}.get(truth),
                'truth_state':truth,'path':path,'logic_version':LOGIC_VERSION,'children':children,
                'decisive_children':[n['path'] for n in children if n['truth_state']==truth]}
    field = node.get('field', node.get('derived_field'))
    if not field: raise ValueError('UNSUPPORTED_LOGIC_NODE')
    value = values.get(field)
    reasons = invalid.get(field, [])
    result = None if value is None or reasons else compare(value,node['op'],node['value'])
    truth = 'INVALID' if reasons or (value is not None and result is None) else 'UNKNOWN' if value is None else 'TRUE' if result else 'FALSE'
    return {'field':field,'operator':node['op'],'expected':node['value'],'actual':value,
            'state':result,'truth_state':truth,'path':path,'logic_version':LOGIC_VERSION,
            'reasons':reasons or (['TYPE_OR_NONFINITE_INVALID'] if truth=='INVALID' else ['NOT_AVAILABLE'] if truth=='UNKNOWN' else [])}

def fields(node, state=None):
    """Legacy projection: all indeterminate leaves, NOT diagnostic requirements."""
    if 'children' in node: return sorted({f for child in node['children'] for f in fields(child,state)})
    return [node['field']] if node.get('state') is state else []

def requirements(node):
    """Mark unresolved paths; OR candidates are alternatives, not individually mandatory.

    A determined ancestor suppresses unknown descendants for THIS decision only.
    Missing data in false AND branches are nonblocking too, not proof of normality.
    """
    required=set(); optional=set(); invalid_required=set(); invalid_all=set()
    def walk(n, active=True, blocked_by=None):
        truth=n.get('truth_state', 'TRUE' if n['state'] is True else 'FALSE' if n['state'] is False else 'UNKNOWN')
        n['truth_state']=truth
        if 'children' in n:
            needed=active and truth in ('UNKNOWN','INVALID')
            n['required_for_resolution']=needed
            for child in n['children']:
                walk(child,needed,blocked_by or (n.get('path','root') if not needed else None))
        else:
            n['required_for_resolution']=active and truth in ('UNKNOWN','INVALID')
            n['nonblocking_ancestor']=blocked_by
            if truth=='UNKNOWN': (required if active else optional).add(n['field'])
            if truth=='INVALID':
                invalid_all.add(n['field'])
                if active: invalid_required.add(n['field'])
    walk(node)
    return {'missing_required':sorted(required),'optional_not_measured':sorted(optional-required),
            'invalid_required':sorted(invalid_required),'invalid_fields':sorted(invalid_all),
            'missing_requirement_semantics':'UNRESOLVED_CANDIDATES_RESPECT_AND_OR_NOT_ALL_MANDATORY',
            'data_requirement_version':LOGIC_VERSION}

def has_positive(node):
    return any(has_positive(c) for c in node['children']) if 'children' in node else node['state'] is True

def leaf(field,value=True,op='=='): return {'field':field,'op':op,'value':value}
