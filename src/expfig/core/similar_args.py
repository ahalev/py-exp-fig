from difflib import get_close_matches

nlt = '\n\t'

best_matches = dict()


def get_similar_args(unrecognized_args, known_args):
    unrecognized_options = [opt.partition('=')[0].lstrip('-') for opt in unrecognized_args if opt.startswith('--')]

    for bad_opt in unrecognized_options:
        best_matches[f'--{bad_opt}'] = [f'--{s}' for s in get_close_matches(bad_opt, known_args)]

    return best_matches


def get_similar_args_str_fmt(unrecognized_args, known_args):
    similar_args = get_similar_args(unrecognized_args, known_args)

    string = [f"Unrecognized arguments '{unrecognized_args}'"]

    for unrecognized, matches in similar_args.items():
        if matches:
            s = f"'{unrecognized}' is not a recognized argument.\n\nThe most similar arguments are{nlt}{nlt.join(matches)}"
            string.append(s)

    if len(string) == 1:
        string.append('There are no similar arguments.')

    return '\n\n'.join(string)
