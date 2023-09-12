import argparse
import sys
import os
import pandas as pd
import yaml

from copy import deepcopy

from collections import UserDict
from pathlib import Path
from warnings import warn

from . import Namespacify, nested_dict_update
from .functions import unflatten
from .functions._parse import str2bool, str2none, ListType, ListAction
from .logging import get_logger


DEFAULT_CONFIG_PATH = os.path.join(os.getcwd(), 'default_config.yaml')


class Config(Namespacify):
    def __init__(self, config=None, default=DEFAULT_CONFIG_PATH):
        self.default_config = DefaultConfig(self._parse_default(config, default))

        self.logger = get_logger()
        self.verbosity = 0

        super().__init__(self._parse_config())

        self.update_with_configs(config)
        self.verbose(self.verbosity)

    def _parse_default(self, config, default):
        if pd.api.types.is_dict_like(default):
            return default

        candidates = [Path(default), (Path(sys.argv[0]).parent / default)]

        if config is not None and isinstance(config, (str, Path)):
            candidates.extend([Path(config), (Path(sys.argv[0]).parent / config)])

        for candidate in candidates:
            if candidate.exists():
                return candidate

        candidates_str = '\n\t'.join(str(x.absolute()) for x in candidates)
        err_msg = f'Attempted to resolve default config in the following order:\n\t{candidates_str}.\n' \
                  f'Unable to find a file amongst these candidates.'
        raise ValueError(err_msg)

    def _parse_config(self):
        # First we parse any --config arguments and load those
        # Then we can override them with any other passed values.
        base_config = deepcopy(self.default_config)

        config_file_args, other_args = self._split_config_file_args()
        config_files = self._create_config_file_parser().parse_args(args=config_file_args)
        self.update_with_configs(config_files.config, base_config)

        parsed_args = self._create_parser(default=base_config).parse_known_args(args=other_args)

        if len(parsed_args[1]):
            valid_args = "\n\t\t".join(sorted(parsed_args[0].__dict__.keys()))
            warn(f'Unrecognized arguments {parsed_args[1]}.\n\tValid arguments:\n\t\t{valid_args}')

        # TODO (ahalev) deprecate, this should be handled by str2None
        args_dict = {k: v if v != 'null' else None for k, v in parsed_args[0].__dict__.items()}

        args_dict = self._extract_verbosity(args_dict)
        restructured = unflatten(args_dict)

        self._check_restructured(restructured, self.default_config)
        return restructured

    def _split_config_file_args(self):
        try:
            config_key_idx = sys.argv.index('--config')
        except ValueError:
            return [], sys.argv[1:]

        config_args = []
        other_args = []

        next_optional_arg = [j for j in range(config_key_idx+1, len(sys.argv)) if '--' in sys.argv[j]][0]

        for j, arg in enumerate(sys.argv[1:], start=1):
            if config_key_idx <= j < next_optional_arg:
                config_args.append(arg)
            else:
                other_args.append(arg)

        assert set(config_args).union(other_args) == set(sys.argv[1:])
        assert not set(config_args).intersection(other_args)

        return config_args, other_args

    def _create_parser(self, default=None):
        parser = argparse.ArgumentParser(prog='GridRL')
        for arg_name, arg_info in self._get_arguments(d=default).items():
            parser.add_argument(f'--{arg_name}', **arg_info)

        if parser.get_default('verbose') is None:
            parser.add_argument('--verbose', default=0, type=int)

        return parser

    def _create_config_file_parser(self):
        parser = argparse.ArgumentParser(prog='GridRLConfig')
        parser.add_argument('--config', default=[], nargs='+')
        return parser

    def update_with_configs(self, configs, updatee=None):
        if configs is None:
            return self
        elif not pd.api.types.is_list_like(configs) or pd.api.types.is_dict_like(configs):
            configs = [configs]

        for config in configs:
            updatee = self._update_with_config(config, updatee=updatee)

        return updatee

    def _update_with_config(self, config, updatee=None):
        if isinstance(config, (str, Path)):
            config = _config_from_yaml(config)

        config = self._restructure_as_necessary(config)

        if updatee:
            return nested_dict_update(updatee, config)
        else:
            return nested_dict_update(self, config)

    def _restructure_as_necessary(self, config):
        if any('.' in k for k in config.keys()):
            if any(isinstance(v, dict) for v in config.values()):
                raise ValueError('Cannot combine nested dict config arguments with "." deliminated arguments.')

            config = unflatten(config)

        return config

    def _extract_verbosity(self, config):
        self.verbosity = config['verbose']

        try:
            _ = self.default_config.verbose
        except AttributeError:
            config.pop('verbose')

        return config

    def _check_restructured(self, restructured, default_config, *stack):
        for key, value in default_config.items():
            if key not in restructured:
                raise RuntimeError(f'Missing key {"->".join([*stack, key])} in restructured config.')
            elif isinstance(value, dict):
                self._check_restructured(restructured[key], value, *stack, key)

    def _get_arguments(self, key='', d=None):
        if d is None:
            d = self.default_config

        args = {}

        for k, v in d.items():
            new_key = f'{key}.{k}' if key else k
            if isinstance(v, (dict, UserDict)) and len(v):
                args.update(self._get_arguments(key=new_key, d=v))
            else:
                if '-' in new_key:
                    raise NameError(f"Invalid character '-' in key '{new_key}'.")

                args[new_key] = self._collect_argument(v)

        return args

    def _collect_argument(self, default_val):
        arg = {}

        if pd.api.types.is_list_like(default_val):
            arg['nargs'] = '+'
            arg['action'] = ListAction
            _type = self._get_list_like_type(default_val)

        elif not default_val and not isinstance(default_val, (float, int, bool)):
            _type = str
        else:
            _type = type(default_val)

        if _type == bool:
            _type = str2bool
        elif _type == str:
            _type = str2none

        arg.update({'default': default_val, 'type': _type})

        return arg

    def _get_list_like_type(self, list_like):
        _types = pd.Series([type(x) for x in list_like])

        try:
            _type = _types.unique().item()
        except ValueError:
            _type = str

            if len(_types):
                warn('Collecting list-like argument with non-unique types in default value or empty default value. '
                     'Collected values will be str.')

        if _type == str:
            _type = str2none

        return ListType(_type)


    def serialize_to_dir(self, log_dir, fname='config.yaml', use_existing_dir=False, with_default=False):
        log_dir = super().serialize_to_dir(log_dir, fname=fname, use_existing_dir=use_existing_dir)

        if with_default:
            path = Path(fname)

            def fname_func(kind): return (path.parent / f'{path.stem}_{kind}').with_suffix(path.suffix)

            self.default_config.serialize_to_dir(log_dir,
                                                 fname=fname_func('default'),
                                                 use_existing_dir=True)

            (self ^ self.default_config).serialize_to_dir(log_dir,
                                                          fname=fname_func('difference'),
                                                          use_existing_dir=True)
        return log_dir

    def verbose(self, level):
        if level >= 2:
            self.logger.info('Trainer config:')
            self.pprint(indent=1, log_func=self.logger.info)
        if level >= 1:
            xor = self ^ self.default_config
            print(f'\n{"-"*10}\n')
            if xor:
                self.logger.info('Custom trainer config (difference from default):')
                xor.pprint(indent=1, log_func=self.logger.info)
            else:
                self.logger.info('No difference from default.')


class DefaultConfig(Namespacify):
    def __init__(self, default):
        if not pd.api.types.is_dict_like(default):
            default = _config_from_yaml(default)

        super().__init__(default)


def _config_from_yaml(file_path):
    contents = Path(file_path).expanduser().open('r')
    loaded_contents = yaml.safe_load(contents)

    if not isinstance(loaded_contents, dict):
        raise ValueError(f'Contents of file "{file_path}" deserialize into object of type '
                         f'{type(loaded_contents).__name__}, should be dict.')

    return loaded_contents


