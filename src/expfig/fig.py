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
from .logging import get_logger


DEFAULT_CONFIG_PATH = os.path.join(os.getcwd(), 'default_config.yaml')


class Config(Namespacify):
    def __init__(self, config=None, keys_for_name=(), name_prefix='', default=DEFAULT_CONFIG_PATH):
        self.default_config = DefaultConfig(self._parse_default(config, default)).with_name_from_keys(*keys_for_name, prefix=name_prefix)

        self.logger = get_logger()
        self.verbosity = 0

        super().__init__(self._parse_config())

        if config is not None:
            self._update_with_config(config)

        self.with_name_from_keys(*keys_for_name, prefix=name_prefix)
        self.verbose(self.verbosity)

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

    def _parse_default(self, config, default):
        candidates = [Path(default), (Path(sys.argv[0]).parent / default)]

        if config is not None and isinstance(config, str):
            candidates.extend([Path(config), (Path(sys.argv[0]).parent / config)])

        for candidate in candidates:
            if candidate.exists():
                return candidate

        candidates_str = '\n\t'.join(str(x.absolute()) for x in candidates)
        err_msg = f'Attempted to resolve default config in the following order:\n\t{candidates_str}.\n' \
                  f'Unable to find a file amongst these candidates.'
        raise ValueError(err_msg)

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

    def _update_with_config(self, config, updatee=None):
        if isinstance(config, str):
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

            config = self._restructure_arguments(config)

        return config

    def _get_arguments(self, key='', d=None):
        if d is None:
            d = self.default_config

        args = {}

        for k, v in d.items():
            new_key = f'{key}.{k}' if key else k
            if isinstance(v, (dict, UserDict)):
                args.update(self._get_arguments(key=new_key, d=v))
            else:
                args[new_key] = self._collect_argument(v)

        return args

    def _collect_argument(self, default_val):
        arg = {
            'default': default_val,
            'type': type(default_val),
        }
        if hasattr(default_val, '__len__') and not isinstance(default_val, str):
            arg["nargs"] = '+'

        return arg

    def _parse_config(self):
        # First we parse any --config arguments and load those
        # Then we can override them with any other passed values.
        base_config = deepcopy(self.default_config)
        config_files, other_args = self._create_config_file_parser().parse_known_args()

        for config_file in config_files.config:
            self._update_with_config(config_file, updatee=base_config)

        parsed_args = self._create_parser(default=base_config).parse_known_args(other_args)

        if len(parsed_args[1]):
            bad_args = [x.replace("--", "") for x in parsed_args[1] if x.startswith("--")]
            valid_args = "\n\t\t".join(sorted(parsed_args[0].__dict__.keys()))
            warn(f'Unrecognized arguments {bad_args}.\n\tValid arguments:\n\t\t{valid_args}')

        args_dict = parsed_args[0].__dict__

        args_dict = self._extract_verbosity(args_dict)
        restructured = self._restructure_arguments(args_dict)

        self._check_restructured(restructured, self.default_config)
        return restructured

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

    def _extract_verbosity(self, config):
        self.verbosity = config['verbose']

        try:
            _ = self.default_config.verbose
        except AttributeError:
            config.pop('verbose')

        return config

    def _restructure_arguments(self, config):
        if isinstance(config, dict):
            keys = [key.split('.') for key in config.keys()]
            keys_series = pd.Series(index=pd.MultiIndex.from_frame(pd.DataFrame(keys)), data=config.values())
        else:
            keys_series = config

        restructured = {}

        for key in keys_series.index.get_level_values(0).unique():
            subset = keys_series[key]
            if subset.index.dropna('all').empty:
                restructured.update({key: subset.item()})
            elif subset.index.dropna().nlevels == 1:
                restructured.update({key: subset.to_dict()})
            else:
                restructured.update({key: self._restructure_arguments(subset)})

        return restructured

    def _check_restructured(self, restructured, default_config, *stack):
        for key, value in default_config.items():
            if key not in restructured:
                raise RuntimeError(f'Missing key {"->".join([*stack, key])} in restructured config.')
            elif isinstance(value, dict):
                self._check_restructured(restructured[key], value, *stack, key)


class DefaultConfig(Namespacify):
    def __init__(self, file_path):
        super().__init__(_config_from_yaml(file_path))


def _config_from_yaml(file_path):
    contents = Path(file_path).open('r')
    loaded_contents = yaml.safe_load(contents)

    if not isinstance(loaded_contents, dict):
        raise ValueError(f'Contents of file "{file_path}" deserialize into object of type '
                         f'{type(loaded_contents).__name__}, should be dict.')

    return loaded_contents
