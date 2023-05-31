## Installation

Install with pip:

```shell script
pip install experiment-config
```

## Usage

`expfig.Config` allows for straightforward hyperparameter selection and logging.


It reads hyperparameters from YAML files, the command line, and user inputs and makes them 
available as both attributes and keys. 
It can be embedded in both a script or a class.

## Quick Start

We will build a simple version of [FizzBuzz](https://leetcode.com/problems/fizz-buzz/) 
that allows custom replacement of the words *Fizz* and *Buzz*.

A simple solution of FizzBuzz looks like this:

```python
# examples/quick_start/fizz_buzz.py

class Solution:
    n = 15

    def fizzBuzz(self):
        out = []

        for j in range(1, self.n+1):
            val = ''
            if j % 3 == 0:
                val = 'Fizz'
            if j % 5 == 0:
                val += 'Buzz'
            elif not val:
                val = str(j)
            out.append(val)
        
        print(out)
        return out


Solution().fizzBuzz()
```
Calling `python examples/quick_start/fizz_buzz.py` at the command line will print 
```shell script
['1', '2', 'Fizz', '4', 'Buzz', 'Fizz', '7', '8', 'Fizz', 'Buzz', '11', 'Fizz', '13', '14', 'FizzBuzz']
```
We can use expfig.Config to quickly replace `'Fizz'`, `'Buzz'`, and the integer `n` at the command line.

Let's define a file `fizz_buzz_default_config.yaml`:

```yaml
n: 15
words:
  buzz: Buzz
  fizz: Fizz
```

and replace the values of `'Fizz'`, `'Buzz'`, and `n` in our script with the corresponding
values in the config. We will also add a pretty-print of our config, just to keep track of what is going on:

```python
# examples/quick_start/fizz_buzz.py
from expfig import Config


class Solution:
    config = Config(default='fizz_buzz_default_config.yaml')
    
    def fizzBuzz(self):
        self.config.pprint()
        out = []

        for j in range(1, self.config.n+1):
            val = ''
            if j % 3 == 0:
                val = self.config.words.fizz
            if j % 5 == 0:
                val += self.config.words.buzz
            elif not val:
                val = str(j)
            out.append(val)
        
        print(out)
        return out


Solution().fizzBuzz()
```
Calling `python examples/quick_start/fizz_buzz.py` at the command line will now print 
```shell script
config:
    n: 15
    words:
        buzz: Buzz
        fizz: Fizz
['1', '2', 'Fizz', '4', 'Buzz', 'Fizz', '7', '8', 'Fizz', 'Buzz', '11', 'Fizz', '13', '14', 'FizzBuzz']
```
which is, as expected, our config followed by the solution.

We can now easily modify any combination of our values:

```shell script
$ python examples/quick_start/fizz_buzz.py --n 10 --words.buzz Buzzword

config:
    n: 10
    words:
        buzz: Buzzword
        fizz: Fizz
['1', '2', 'Fizz', '4', 'Buzzword', 'Fizz', '7', '8', 'Fizz', 'Buzzword'].
```

This example can be viewed in the `examples/quick_start` directory.

#### `verbose`

`--verbose` is a special key that `expfig.Config` will read. It accepts positive integer values and will print
the config is increasing verbosity depending on its value.

* `--verbose 0`: nothing is printed (this is the default).
* `--verbose 1`: the symmetric difference between the config and the default config is printed.
* `--verbose 2`: the entire config is printed.

For example:

```shell script
$ python examples/quick_start/fizz_buzz.py --n 10 --words.buzz Buzzword --verbose 1

 config:
     n: 10
     words:
         buzz: Buzzword
config:
    n: 10
    words:
        buzz: Buzzword
        fizz: Fizz
['1', '2', 'Fizz', '4', 'Buzzword', 'Fizz', '7', '8', 'Fizz', 'Buzzword']

```

The first block is the difference between the config and the default config, while the second is the pretty-print of
the entire config.

## Saving a `Config`

`expfig.Config` takes advantage of YAML-serialization (and de-serialization) for 
reproducibility.

You can use both `expfig.Config.serialize` and `expfig.Config.serialize_to_dir` for serialization.

`expfig.Config.serialize` performs a simple YAML-dump of the underlying dictionary:

```python
# python examples/quick_start/serialize_fizz_buzz.py

from fizz_buzz import Solution

with open('simple_serialization.yaml', 'w') as f:
    Solution().config.serialize(f)
```
`expfig.Config.serialize_to_dir` will ensure that you are not overwriting any existing directories
(if desired), and can also handle serializing the default config and the difference:
```python
# python examples/quick_start/serialize_fizz_buzz.py


from fizz_buzz import Solution

# Serialize the underlying dict. Makes sure it does not overwrite any existing `fizz_buzz_config` directory
# by appending an integer on the end if one exists.
Solution().config.serialize_to_dir('fizz_buzz_configs')

# Same as the above, but also serialize the default config and the difference.
Solution().config.serialize_to_dir('fizz_buzz_configs_with_default', with_default=True)
```

You can then use `expfig.Config.deserialize` to load your saved serialization and reproduce your settings, for example:

```python
from expfig import Config

with open('simple_serialization.yaml', 'r') as f:
    config = Config.deserialize(f)
```

Note that doing so effectively treats `simple_serialization.yaml` as a default config;
you can use command-line arguments to update it upon loading.

## Additional methods of inputting custom hyperparameters

There are three other ways to define custom settings/hyperparameters:

  1. You can pass the `--config path_to_a_config.yaml` argument at the command line. 
  
     `path_to_a_config.yaml` may
     contain any combination of values as defined in your default config file; they must be in the same format. 
     You may pass any number of config files this way:

     ```shell script
     --config path_to_a_config.yaml path_to_another_config.yaml
     ```

     If you pass multiple config files with conflicting values, the value from the ***last*** config file
     will be used.
     
     Note that any values passed this way will be overridden by explicit arguments or arguments passed by the below
     two methods.

  2. You can pass a path to a `yaml` file containing settings to `expfig.Config`. You may pass any combination
     of values as defined in `config/default_config.yaml`; they must be in the same format. This is equivalent to
     the above except it is done within a script and not at the command line:
     ```python
     from expfig import Config
     
     config = Config(config='path_to_a_config.yaml')
     ```
  3. You can pass a nested dictionary defining configuration settings to `expfig.Config`.
     For example:
     ```python
     from expfig import Config
     
     config_dict = {
         'microgrid': {'config': {'scenario': 1}},
         'algo': {'sampler': {'type': 'local', 'n_workers': 4}},
         'context': {'verbose': True}
     }
     config = Config(config_dict)
     ```

## Hyperparameter Resolution Order

You may encounter the situation where you pass the same key in different ways, with different values. For example, you may have a key in both your default config, a config passed via `--config path_to_a_config.yaml`, 
and by direct argument at the command line: `--key value`.

For any key set in your default config, the resolution order is as follows:

1. Values passed directly to `expfig.Config` upon object initialization. This includes values
   defined within a config file passed to `expfig.Config`: `expfig.Config(config='path_to_a_config.yaml)`.

2. Values passed explicitly at the command line.

3. Values within a config file passed at the command line. If multiple config files are passed and the 
   key is contained in more than one of said files, the value from the *last* file will be used.

4. Values within your default config.


## Variations between different methods of setting parameters

### 1. Type casting
Values passed at the command line are casted to the type of the default value as defined by the yaml-load of the default
value. For example, a default config containing `value: 1` will result in the expectation that `value` is an `int`. 
This is not true with values passed in python code or in separate config files. 

There are two exceptions to this: 

1. Values where the default value is `None` parse command line arguments to string.

2. The string `null` passed at the command line results in the value `None`. 


## Additional Examples

An example of using `expfig.Config` to set hyperparameters for a machine learning problem
is available in `examples/knn`. This example demonstrates a simple class to run a classification problem using `scikit-learn`'s
[`KNeighborsClassifier`](https://scikit-learn.org/stable/modules/generated/sklearn.neighbors.KNeighborsClassifier.html).
