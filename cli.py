# !/usr/bin/env python
# -*- coding: utf-8 -*-


from fire import Fire

from cli import account, pull, push

if __name__ == '__main__':
    _, _, _ = account, pull, push
    Fire()
