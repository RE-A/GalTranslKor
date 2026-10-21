"""Shared pytest setup.

This fork shows backend messages in Korean by default. Upstream tests assert the
original Chinese messages, so the test process pins GT_LANG to zh-cn before any
GalTransl module is imported. The Korean default is covered separately.
"""
import os

os.environ.setdefault("GT_LANG", "zh-cn")
