from .chain import Chain
from .text import Text

def get_model_dict(thing):
    if isinstance(thing, Chain):
        return thing.model
    if isinstance(thing, Text):
        return thing.chain.model
    if isinstance(thing, list):
        return dict(thing)
    if isinstance(thing, dict):
        return thing

def combine(models, weights=None):
    if weights == None:
        weights = [ 1 for _ in range(len(models)) ]

    try:
        assert(len(models) == len(weights))
    except:
        raise ValueError("`models` and `weights` lengths must be equal.")

    model_dicts = list(map(get_model_dict, models))
    state_sizes = [ len(list(md.keys())[0])
        for md in model_dicts ]

    try:
        assert(len(set(state_sizes)) == 1)
    except:
        raise ValueError("All `models` must have the same state size.")

    try:
        assert(len(set(map(type, models))) == 1)
    except:
        raise ValueError("All `models` must be of the same type.")

    c = {}

    for m, w in zip(model_dicts, weights):
        for state, options in m.items():
            current = c.get(state, {})
            for subseq_k, subseq_v in options.items():
                subseq_prev = current.get(subseq_k, 0)
                current[subseq_k] = subseq_prev + (subseq_v * w)
            c[state] = current

    ret_inst = models[0]

    if isinstance(ret_inst, Chain):
        return Chain.from_json(c)
    if isinstance(ret_inst, Text):
        combined_text = "\n".join(m.input_text for m in models)
        return Text.from_chain(c, corpus=combined_text)
    if isinstance(ret_inst, list):
        return list(c.items())
    if isinstance(ret_inst, dict):
        return c

    raise ValueError("`models` should be instances of list, dict, markovify.Chain, or markovify.Text")
