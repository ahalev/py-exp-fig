import argparse
import sys
import os
import yaml

from copy import deepcopy

from collections import UserDict
from pathlib import Path
from warnings import warn

from . import Namespacify, nested_dict_update
from .core import unflatten, get_similar_args_str_fmt
from .core._parse import ListType, ListAction, parse_arg_type, get_type
from .logging import get_logger
from .utils import api


DEFAULT_CONFIG_PATH = os.path.join(os.getcwd(), 'default_config.yaml')


class Config(Namespacify):
    """
    Serializable config object.

    Parameters
    ----------
    config : str, Path, dict, None or list of str, dict, or Path, default None
        Dictionaries of configuration values or str/Path pointing to YAML file(s) containing configuration values.
        * If str or Path, the value is treated as a YAML file which is then loaded to a dictionary, and then:
        * If dictionary, `Config` object will be updated to contain values in the dictionary. These values can be either
          nested or '.'-delimited, the latter of which will be nested before updating `Config` object.
        * If list of the above, `Config` object will be updated in corresponding order. In the case of duplicate keys,
          the value from the **last** entry will be utilized.
    default : str, dict or Path, default `os.path.join(os.getcwd(), 'default_config.yaml')`.
        Dict or path-like object from which to load default config.
        The corresponding nested dictionary defines the arguments in argparse. For example:
         >>> default = {'truck': {'wheels': 4, 'brand': 'toyota'}}
         will result in argparse arguments `truck.wheels` of type `int` and `truck.brand` of type str, with defaults
         of 4 and 'toyota', respectively.
    yaml_type_handling: {'ignore', 'warn', 'error'}, default 'warn'
        Handling method for values loaded from config files (either via `--config <filename>` or passed via `config`
        parameter) that cannot be cast to the type of the value in the default config.
        * 'ignore': silently allow mistyped values.
        * 'warn': allow mistyped values and raise a warning if encountered.
        * 'error': raise `TypeError`s on mistyped values.
    Attributes
    ----------

    """
    def __init__(self, config=None, default=DEFAULT_CONFIG_PATH, yaml_type_handling='warn'):
        assert yaml_type_handling in ('ignore', 'warn', 'error'), \
            "yaml_type_handling must be one of 'ignore', 'warn', error'"

        self.yaml_type_handling = yaml_type_handling

        self.default_config = DefaultConfig(self._parse_default(config, default))
        self.logger = get_logger()
        self.verbosity = 0

        super().__init__(self._parse_config())

        self.update_with_configs(config)
        self.verbose(self.verbosity)

    def _parse_default(self, config, default):
        if api.is_dict_like(default):
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
            valid_option_keys = sorted(parsed_args[0].__dict__.keys())
            warn_msg = get_similar_args_str_fmt(parsed_args[1], valid_option_keys)
            warn(warn_msg)

        args_dict = self._extract_verbosity(parsed_args[0].__dict__)
        restructured = unflatten(args_dict)

        self._check_restructured(restructured, self.default_config)
        return restructured

    def _split_config_file_args(self):
        config_arg_loc = [x.startswith('--config') for x in sys.argv]

        if sum(config_arg_loc) > 1:
            msg = "Multiple --config arguments encountered. Pass multiple configs with a single --config prefix, e.g. " \
                  "'python script.py --config config_1.yaml config_2.yaml'"
            raise TypeError(msg)

        try:
            config_key_idx = sys.argv.index('--config')
        except ValueError:
            try:
                # single string starting with '--config'
                assert sum(config_arg_loc) == 1
            except AssertionError:
                return [], sys.argv[1:]
            else:
                config_arg_loc = config_arg_loc.index(True)
                config_arg = sys.argv[config_arg_loc]

                other_args = sys.argv[1:].copy()
                other_args.pop(config_arg_loc-1)

                return [config_arg], other_args

            return [], sys.argv[1:]

        config_args = []
        other_args = []
        try:
            next_optional_arg = [j for j in range(config_key_idx+1, len(sys.argv)) if '--' in sys.argv[j]][0]
        except IndexError:
            # no optional args following config arguments
            next_optional_arg = float('inf')

        for j, arg in enumerate(sys.argv[1:], start=1):
            if config_key_idx <= j < next_optional_arg:
                config_args.append(arg)
            else:
                other_args.append(arg)

        assert set(config_args).union(other_args) == set(sys.argv[1:])
        assert not set(config_args).intersection(other_args)

        return config_args, other_args

    def _create_parser(self, default=None):
        parser = argparse.ArgumentParser()
        for arg_name, arg_info in self._get_arguments(d=default).items():
            parser.add_argument(f'--{arg_name}', **arg_info)

        if parser.get_default('verbose') is None:
            parser.add_argument('--verbose', default=0, type=int)

        return parser

    def _create_config_file_parser(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--config', default=[], nargs='+', type=ListType(str), action=ListAction)
        return parser

    def update_with_configs(self, configs, updatee=None):
        """
        Update `self` with one or multiple dict-like objects.

        Parameters
        ----------
        configs : str, Path, dict or None
            One of:
            * Path-like pointing to a yaml-file to load a dict from
            * dict
            * list of the above
            * None, in which case no update occurs
        updatee : dict-like or None, default None
            Object to update. If None, updates self.

        Returns
        -------
        updatee: dict-like
            Updated object.

        """
        if configs is None:
            return self
        elif not api.is_list_like(configs) or api.is_dict_like(configs):
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

                base_default = self.default_config.get(tuple(new_key.split('.')), v)
                args[new_key] = self._collect_argument(v, base_default, new_key)

        return args

    def _collect_argument(self, default_val, base_default, arg_name):
        arg = {}

        _type, additional_args = parse_arg_type(arg_name, base_default)

        arg.update(additional_args)

        try:
            default = _type(default_val)
        except Exception as e:
            msg = f"Value '{default_val}' read from yaml file cannot be case to type '{get_type(_type)}' "\
                  f"of base config value."
            if self.yaml_type_handling == 'error':
                raise TypeError(msg) from e
            elif self.yaml_type_handling == 'warn':
                self.logger.warning(msg)

            default = default_val

        arg.update({'default': default, 'type': _type})

        return arg


    def serialize_to_dir(self, log_dir, fname='config.yaml', use_existing_dir=False, with_default=False):
        """
        Save the config as a yaml file in a directory.

        Parameters
        ----------
        log_dir : str or Path
            directory to serialize into.

        fname : str, default 'config.yaml`
            Name of the file.

        use_existing_dir : bool, default False
            Whether to serialize to a directory that already exists. If False and `log_dir` exists,
            config will be serialized to `{log_dir}_{k}`, where k is the smallest positive integer such that
            `{log_dir}_{k}` does not currently exist.

        with_default : bool, default False
            Whether to serialize default config as well. If true, default config is serialized as `config_default.yaml`
            in the same `log_dir` as the config. The symmetric difference is also serialized as
            `config_difference.yaml`.

        Returns
        -------
        log_dir : str
            Path of the log dir the config was serialized to.

        """
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
        if not api.is_dict_like(default):
            default = _config_from_yaml(default)

        super().__init__(default)


def _config_from_yaml(file_path):
    contents = Path(file_path).expanduser().open('r')
    loaded_contents = yaml.safe_load(contents)

    if not isinstance(loaded_contents, dict):
        raise ValueError(f'Contents of file "{file_path}" deserialize into object of type '
                         f'{type(loaded_contents).__name__}, should be dict.')

    return loaded_contents
