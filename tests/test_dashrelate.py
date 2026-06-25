"""Unit tests for OntologyBuilder (no Spark required)."""
import pytest


def test_import():
    import dashrelate
    assert hasattr(dashrelate, "__version__")


def test_launch_importable():
    from dashrelate import launch
    assert callable(launch)


def test_main_class_importable():
    from dashrelate import OntologyBuilder
    assert OntologyBuilder is not None
