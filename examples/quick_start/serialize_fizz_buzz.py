from fizz_buzz import Solution

# Serialize the underlying dict
with open('simple_serialization.yaml', 'w') as f:
    Solution().config.serialize(f)

# Serialize the underlying dict. Makes sure it does not overwrite any existing `fizz_buzz_config` directory
# by appending an integer on the end if one exists.
Solution().config.serialize_to_dir('fizz_buzz_configs')

# Same as the above, but also serializes the default config and the difference.
Solution().config.serialize_to_dir('fizz_buzz_configs_with_default', with_default=True)
