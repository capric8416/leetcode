# !/usr/bin/env python
# -*- coding: utf-8 -*-


from cli.pull import main as pull
from cli.push import main as push
from cli.account import main as account

from fire import Fire


if __name__ == '__main__':
    Fire()

