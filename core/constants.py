import types
from collections import namedtuple
from dataclasses import dataclass
from typing import List, TypeVar, Type, Any, TYPE_CHECKING, ClassVar, Dict, Optional, Final

from dotenv.main import load_dotenv

load_dotenv()


def _create_value_cls(name, comparable):
    cls = namedtuple('_EnumValue_' + name, 'name value')
    cls.__repr__ = lambda self: f'<{name}.{self.name}: {self.value!r}>'
    cls.__str__ = lambda self: f'{name}.{self.name}'
    if comparable:
        cls.__le__ = lambda self, other: isinstance(other, self.__class__) and self.value <= other.value
        cls.__ge__ = lambda self, other: isinstance(other, self.__class__) and self.value >= other.value
        cls.__lt__ = lambda self, other: isinstance(other, self.__class__) and self.value < other.value
        cls.__gt__ = lambda self, other: isinstance(other, self.__class__) and self.value > other.value
    return cls


def _is_descriptor(obj):
    return hasattr(obj, '__get__') or hasattr(obj, '__set__') or hasattr(obj, '__delete__')


class EnumMeta(type):
    if TYPE_CHECKING:
        __name__: ClassVar[str]
        _enum_member_names_: ClassVar[List[str]]
        _enum_member_map_: ClassVar[Dict[str, Any]]
        _enum_value_map_: ClassVar[Dict[Any, Any]]

    def __new__(mcs, name, bases, attrs, *, comparable: bool = False):
        value_mapping = {}
        member_mapping = {}
        member_names = []

        value_cls = _create_value_cls(name, comparable)
        for key, value in list(attrs.items()):
            is_descriptor = _is_descriptor(value)
            if key[0] == '_' and not is_descriptor:
                continue

            # Special case classmethod to just pass through
            if isinstance(value, classmethod):
                continue

            if is_descriptor:
                setattr(value_cls, key, value)
                del attrs[key]
                continue

            try:
                new_value = value_mapping[value]
            except KeyError:
                new_value = value_cls(name=key, value=value)  # type: ignore
                value_mapping[value] = new_value
                member_names.append(key)

            member_mapping[key] = new_value
            attrs[key] = new_value

        attrs['_enum_value_map_'] = value_mapping
        attrs['_enum_member_map_'] = member_mapping
        attrs['_enum_member_names_'] = member_names
        attrs['_enum_value_cls_'] = value_cls
        actual_cls = super().__new__(mcs, name, bases, attrs)
        value_cls._actual_enum_cls_ = actual_cls  # type: ignore
        return actual_cls

    def __iter__(cls):
        return (cls._enum_member_map_[name] for name in cls._enum_member_names_)

    def __reversed__(cls):
        return (cls._enum_member_map_[name] for name in reversed(cls._enum_member_names_))

    def __len__(cls):
        return len(cls._enum_member_names_)

    def __repr__(cls):
        return f'<enum {cls.__name__}>'

    @property
    def __members__(cls):
        return types.MappingProxyType(cls._enum_member_map_)

    def __call__(cls, value):
        try:
            return cls._enum_value_map_[value]
        except (KeyError, TypeError):
            raise ValueError(f"{value!r} is not a valid {cls.__name__}")

    def __getitem__(cls, key):
        return cls._enum_member_map_[key]

    def __setattr__(cls, name, value):
        raise TypeError('Enums are immutable.')

    def __delattr__(cls, attr):
        raise TypeError('Enums are immutable')

    def __instancecheck__(self, instance):
        # isinstance(x, Y)
        # -> __instancecheck__(Y, x)
        try:
            # noinspection PyProtectedMember
            return instance._actual_enum_cls_ is self
        except AttributeError:
            return False


if TYPE_CHECKING:
    # noinspection PyUnresolvedReferences
    from enum import Enum
else:

    class Enum(metaclass=EnumMeta):
        @classmethod
        def try_value(cls, value):
            try:
                return cls._enum_value_map_[value]
            except (KeyError, TypeError):
                return value

        @property
        def name(self):
            """The name of the Enum member."""
            return self.name

        @property
        def value(self):
            """The value of the Enum member."""
            return self.value

STAFF_CHANNELS: List[int] = [
    805206391877926912, 821089373214605412, 827474353036853258, 827474644318552104,
    874644809338458143, 808097124742594590, 823668719610888253, 827472306007048232,
    827473681767858176
]
LOUNGE_CHANNELS: List[int] = [
    805206377302982707, 805206379329093632, 805206382160773120, 809686110753652756,
    838961597988732958, 805930501457182746
]
COMMAND_CHANNELS: List[int] = [
    805206382659502121, 805206384794533898, 874644809338458143, 808097124742594590,
    823668719610888253, 827472306007048232, 874644809338458143, 825391611764539462,
    824958184882962452, 827473681767858176, 806823195755282443, 824989904798220358,
    837271163813101608, 838961597988732958
]


@dataclass(frozen=True)
class ROLE:
    """Guilds_ids access with dot notation"""
    OWNER: Final[int] = 805206226769674290
    MANAGER: Final[int] = 818009049911525406
    ADMIN: Final[int] = 820251239429963806
    SR_MOD: Final[int] = 818009056081084417
    MOD: Final[int] = 818009061844844625
    STAFF: Final[int] = 805206229596635187
    HELPER: Final[int] = 819175030453043240
    chat_mod: Final[int] = 821687313150509078


@dataclass(frozen=True)
class GUILD:
    """Guilds_ids access with dot notation"""
    MAIN: int = 512369682636865556
    TESTING: int = 821723190044000317


@dataclass(frozen=True)
class CHANNEL:
    """channel_ids access with dot notation"""
    LOUNGE1: int = 805206377302982707
    DEV: int = 874644809338458143


@dataclass(frozen=True)
class EMOJI:
    """emojis access with dot notation"""
    CROWN: Final[str] = "<a:crown:844861855414747148>"
    TICK: Final[str] = "<a:check:896366284239962143>"
    CROSS: Final[str] = "<a:crossmark:881496170122342470>"
    DOT: Final[str] = "<:small_dot:890514856636190762>"
    SPARKLE2: Final[str] = "<a:sparkles2:831678838610198559>"
    SPARKLE: Final[str] = "<a:sparklestars:831911200073580635>"
    alert: Final[str] = "<a:alert:834006242522693644>"
    PINK_F: Final[str] = "<a:pink_flame:906831372809814026>"
    YELLOW_F: Final[str] = "<a:yellow_flame:832412962865414155>"
    loading: Final[str] = "<a:Loading:876360209340170290>"
    VERIFY: Final[str] = "<a:pinkverified:863685577047408660>"
    coisinha: Final[str] = "<a:coisinha:925262779332575242>"
    arrow: Final[str] = "<a:arrow:925262779550679080>"


T = TypeVar('T')


def try_enum(cls: Type[T], val: Any) -> Optional[T]:
    """A function that tries to turn the value into enum ``cls``.

    If it fails it returns a proxy invalid value instead.
    """

    try:
        return cls._enum_value_map_[val]
    except (KeyError, TypeError, AttributeError):
        return None
