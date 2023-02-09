import argparse
import os
import pandas as pd
import yaml


from pathlib import Path
from collections import UserDict
from warnings import warn

from . import Namespacify, nested_dict_update


DEFAULT_CONFIG_PATH = os.path.join(os.getcwd(), 'default_config.yaml')


class Config(Namespacify):
    def __init__(self, config=None, keys_for_name=('algo', 'type'), name_prefix='', default=DEFAULT_CONFIG_PATH):
        self.default_config = DefaultConfig(self._parse_default(config, default)).with_name_from_keys(*keys_for_name, prefix=name_prefix)

        super().__init__(self._parse_config())

        if config is not None:
            self._update_with_config(config)

        self.with_name_from_keys(*keys_for_name, prefix=name_prefix)
        self._verbose()

    def _parse_default(self, config, default):
        if os.path.exists(default):
            return default
        elif config is not None and os.path.exists(config):
            return config
        else:
            raise ValueError(f'Default config path {default} does not point to a file and {config} does not either.')

    def _verbose(self, level='from_config'):
        if level == 'from_config':
            try:
                level = self.context.verbose
            except AttributeError:
                level = 0

        if level >= 2:
            print('Trainer config:')
            self.pprint(indent=1)
        elif level >= 1:
            print('Custom trainer config:')
            (self ^ self.default_config).pprint(indent=1)

    def _update_with_config(self, config, updatee=None):
        if isinstance(config, str):
            config = _config_from_yaml(config)

        if updatee:
            nested_dict_update(updatee, config)
        else:
            nested_dict_update(self, config)

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
        parsed_args = self._create_parser().parse_known_args()

        if len(parsed_args[1]):
            bad_args = [x.replace("--", "") for x in parsed_args[1] if x.startswith("--")]
            valid_args = "\n\t\t".join(sorted(parsed_args[0].__dict__.keys()))
            warn(f'Unrecognized arguments {bad_args}.\n\tValid arguments:\n\t\t{valid_args}')

        config_files = parsed_args[0].__dict__.pop('config')
        restructured = self._restructure_arguments(parsed_args[0].__dict__)

        if config_files is not None:
            for config_file in config_files:
                self._update_with_config(config_file, updatee=restructured)

        self._check_restructured(restructured, self.default_config)
        return restructured

    def _create_parser(self):
        parser = argparse.ArgumentParser(prog='GridRL')
        for arg_name, arg_info in self._get_arguments().items():
            parser.add_argument(f'--{arg_name}', **arg_info)

        parser.add_argument('--config', default=None, nargs='+')

        return parser

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
