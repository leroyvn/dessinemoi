import attr
import pytest as pytest

import dessinemoi
from dessinemoi import Factory


@pytest.fixture
def factory():
    yield Factory()


def test_factory_create(factory):
    # A Factory instance can be created
    assert isinstance(factory, Factory)


def test_factory_register(factory):
    class Sheep:
        _TYPE_ID = "sheep"

    # Register class based on its built-in ID
    factory.register(Sheep)
    assert "sheep" in factory.registry
    assert factory.registry["sheep"] == Sheep

    # Registering class again fails if aliases are not allowed
    with pytest.raises(ValueError):
        factory.register(Sheep, type_id="mouton")
    factory.register(Sheep, type_id="mouton", allow_aliases=True)
    assert factory.registry["mouton"] == Sheep

    # Overwriting existing ID fails if not explicitly allowed
    with pytest.raises(ValueError):
        factory.register(int, type_id="sheep")
    factory.register(int, type_id="sheep", allow_id_overwrite=True)

    # A new class can also be registered with a decorator
    # Decorator uses can also be chained
    @factory.register(type_id="agneau", allow_aliases=True)  # Full function call form
    @factory.register  # Optionless form
    class Lamb(Sheep):
        _TYPE_ID = "lamb"

    assert "lamb" in factory.registry
    assert "agneau" in factory.registry
    assert factory.registry["lamb"] is Lamb
    assert factory.registry["agneau"] is Lamb


def test_factory_new(factory):
    @factory.register
    @attr.s(frozen=True)
    class Sheep:
        _TYPE_ID = "sheep"
        age = attr.ib()
        name = attr.ib()

    @factory.register
    @attr.s(frozen=True)
    class Ram(Sheep):
        _TYPE_ID = "ram"
        name = attr.ib(default="Gorki")

    # We can use the factory to instantiate new objects with positional arguments only
    assert factory.new("sheep", args=(5, "Dolly")) == Sheep(5, "Dolly")

    # Keyword arguments are supported as well
    assert factory.new("ram", args=(7,)) == Ram(7, name="Gorki")
    assert factory.new("ram", args=(7,), kwargs=dict(name="Romuald")) == Ram(
        7, name="Romuald"
    )

    # Unregistered type IDs raise
    with pytest.raises(ValueError):
        factory.new("mouton")

    # We can restrict accepted types to a certain type
    assert factory.new("ram", args=(7,), allowed_cls=Ram) == Ram(7, name="Gorki")
    with pytest.raises(TypeError):
        factory.new("sheep", args=(5, "Dolly"), allowed_cls=Ram)


def test_convert(factory):
    @factory.register
    @attr.s(frozen=True)
    class Sheep:
        _TYPE_ID = "sheep"
        wool = attr.ib(default="some")

    @factory.register
    @attr.s(frozen=True)
    class Lamb(Sheep):
        _TYPE_ID = "lamb"

    # We can construct keyword-only classes from a dictionary using a converter
    merino = factory.convert({"type": "sheep", "wool": "a_lot"})
    assert merino == Sheep(wool="a_lot")

    # Objects other than dictionaries are not modified
    assert factory.convert(merino) is merino

    # Conversion can be restricted to a specific type
    with pytest.raises(TypeError):
        assert factory.convert({"type": "sheep"}, allowed_cls=Lamb)
    assert factory.convert({"type": "lamb"}, allowed_cls=Lamb) == Lamb()

    # The convert method can be turned into a converter (in the sense of attrs)
    converter = factory.convert(allowed_cls=Lamb)
    with pytest.raises(TypeError):
        assert converter({"type": "sheep"})
    assert converter({"type": "lamb"}) == Lamb()


def test_module_api():
    # Module has a default Factory instance
    assert isinstance(dessinemoi.factory, Factory)

    # Module allows direct access to factory instance API
    @dessinemoi.register
    @attr.s(frozen=True)
    class Sheep:
        _TYPE_ID = "sheep"
        wool = attr.ib(default="some")

    assert dessinemoi.new("sheep") == Sheep()
    assert dessinemoi.convert({"type": "sheep"}) == Sheep()