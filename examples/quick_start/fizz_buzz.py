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