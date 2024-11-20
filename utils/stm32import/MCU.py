
import enum

import os
import re
import traceback
import typing
import logging

from .xml import Tag

logger = logging.getLogger(__file__)


Pedantic = True

MEANINGS_OF_TRUE = ['true', 'yes', '1', 'on', 'enable', 'enabled', 'active', 'high', 'set', 'available']
MEANINGS_OF_FALSE = ['false', 'no', '0', 'off', 'disable', 'disabled', 'inactive', 'low', 'unset', 'unavailable']

def parseBool(value: str):
    lowerValue = value.lower()
    if lowerValue in MEANINGS_OF_TRUE:
        return True
    if lowerValue in MEANINGS_OF_FALSE:
        return False
    raise RuntimeError(f"Unknown boolean value: {value}")




class Element:
    def __init__(self, values: dict, props: dict):
        realPropKeys = {k.lower(): k for k in props.keys()}
        realValuesKeys = {k.lower(): k for k in values.keys()}
        extraKeys = set(realValuesKeys.keys()) - set(realPropKeys.keys())
        missingKeys = set(realPropKeys.keys()) - set(realValuesKeys.keys())
        if len(extraKeys) > 0 and Pedantic:
            raise RuntimeError(f"Extra keys: {', '.join(extraKeys)}")
        if len(missingKeys) > 0 and Pedantic:
            logger.debug(f"Missing keys: {', '.join(missingKeys)}")
        for keyLower in realValuesKeys:
            valuesKey = realValuesKeys[keyLower]
            if keyLower in realPropKeys:
                value = values[realValuesKeys[keyLower]]
                propsKey = realPropKeys[keyLower]
                if isinstance(value, props[propsKey]):
                    setattr(self, propsKey, value)
                else:
                    raise RuntimeError(f"For {propsKey} expected type {props[propsKey]}, got {valuesKey} type {type(value)}")
            else:
                raise RuntimeError(f"Unknown key: {valuesKey}")

    def __str__(self):
        values = ', '.join([f"{k}={v}" for k, v in vars(self).items()])
        return f"{self.__class__.__name__}({values})"

    def __repr__(self):
        values = ', '.join([f"{k}={v}" for k, v in vars(self).items()])
        return f"{self.__class__.__name__}({values})"

    @staticmethod
    def fromTag(resType, node: Tag, schema: dict, ignore: list = []):
        ignore = [i.lower() for i in ignore]
        typeName = resType.__name__.lower()
        if node.tagName.lower() != typeName:
            raise RuntimeError(f"Expected {typeName} tag, got {node.tagName}")
        res = {}
        schemaLowerKeys = {k.lower(): k for k in schema.keys()}
        for key, value in node.attrs.items():
            keyLower = key.lower()
            if keyLower in schemaLowerKeys:
                schemaKey = schemaLowerKeys[keyLower]
                res[key] = schema[schemaKey](value)
            else:
                if keyLower in ignore:
                    continue
                if Pedantic:
                    raise RuntimeError(f"Unknown attribute: {key}")

        for child in node.children:
            keyLower = child.tagName.lower()
            if keyLower in schemaLowerKeys:
                schemaKey = schemaLowerKeys[keyLower]
                value = schema[schemaKey](child)
                if value is None:
                    continue
                if schemaKey in res:
                    if isinstance(res[schemaKey], list):
                        res[schemaKey].append(value)
                    else:
                        res[schemaKey] = [res[schemaKey], value]
                else:
                    res[schemaKey] = value
            else:
                if keyLower in ignore:
                    continue
                if Pedantic:
                    raise RuntimeError(f"Unknown tag: {child.tagName}")
        return resType(**res)

    @staticmethod
    def fromDict(resType, values: dict, schema: dict, ignore: list = []):
        res = {}
        schemaLowerKeys = {k.lower(): k for k in schema.keys()}
        for key, value in values.items():
            keyLower = key.lower()
            if keyLower in schemaLowerKeys:
                schemaKey = schemaLowerKeys[keyLower]
                if isinstance(value, list):
                    res[key] = [schema[schemaKey](v) for v in value]
                else:
                    res[key] = schema[schemaKey](value)
            else:
                if keyLower in ignore:
                    continue
                if Pedantic:
                    raise RuntimeError(f"Unknown attribute: {key}")
        return resType(**res)

    @staticmethod
    def fromSomething(resType, something: Tag|dict, schema: dict, ignore: list = []):
        if isinstance(something, Tag):
            return Element.fromTag(resType, something, schema, ignore)
        elif isinstance(something, dict):
            return Element.fromDict(resType, something, schema, ignore)
        else:
            raise RuntimeError(f"Unknown type: {type(something)}")

class Signal(Element):
    class Mode(enum.Enum):
        INPUT = enum.auto()
        LPINPUT = enum.auto()
        OUTPUT = enum.auto()
        LPOUTPUT = enum.auto()
        ANALOG = enum.auto()
        EVENTOUT = enum.auto()
        EXTI = enum.auto()
        EXTI1 = enum.auto()
        EXTI2 = enum.auto()



    def __init__(self, **kwargs):
        super().__init__(kwargs, {
            'name': str,
            'ioModes': (list, Signal.Mode, None)
        })

    @staticmethod
    def fromSomething(node: Tag|dict):
        schema = {
            'name': lambda x: str(x),
            'ioModes': lambda x: [Signal.Mode[mode.upper()] for mode in x.split(',')]
        }
        return Element.fromSomething(Signal, node, schema)



class Condition(Element):
    def __init__(self, **kwargs):
        super().__init__(kwargs, {
            'diagnostic': str,
            'expression': str
        })

    @staticmethod
    def fromSomething(node: Tag|dict):
        schema = {
            'diagnostic': lambda x: str(x),
            'expression': lambda x: str(x)
        }
        return Element.fromSomething(Condition, node, schema)


class Pin(Element):
    class Type(enum.Enum):
        POWER = enum.auto()
        MONOIO = enum.auto()
        IO = enum.auto()
        BOOT = enum.auto()
        RESET = enum.auto()
        NC = enum.auto()

    def __init__(self, **kwargs):
        super().__init__(kwargs, {
            'name': str,
            'position': str,
            'variant': str,
            'requestToSecureIP': bool,
            'type': Pin.Type,
            'signal': (list, Signal),
            'condition': (list, Condition),
        })

    @staticmethod
    def fromSomething(node: Tag|dict):
        schema = {
            'name': lambda x: str(x),
            'position': lambda x: str(x),
            'variant': lambda x: str(x),
            'requestToSecureIP': lambda x: parseBool(x),
            'type': lambda x: Pin.Type[re.sub(r'\W+', '', x.upper())],
            'signal': lambda x: Signal.fromSomething(x),
            'condition': lambda x: Condition.fromSomething(x),
        }
        return Element.fromSomething(Pin, node, schema)

class ContextIp(Element):
    def __init__(self, **kwargs):
        super().__init__(kwargs, {
            'contextName': str,
            'forcedSelection': bool,
            'devalidatedOnSelect': str,
            'initializerForced': bool,
            'defaultSelection': bool,
            'synchronizedContexts': (list, str),
        })

    @staticmethod
    def fromSomething(node: Tag|dict):
        schema = {
            'contextName': lambda x: str(x),
            'forcedSelection': lambda x: parseBool(x),
            'devalidatedOnSelect': lambda x: str(x),
            'initializerForced': lambda x: parseBool(x),
            'defaultSelection': lambda x: parseBool(x),
            'synchronizedContexts': lambda x: [str(v) for v in x.split(',')]
        }
        return Element.fromSomething(ContextIp, node, schema)

class ContextSplit(Element):
    def __init__(self, **kwargs):
        super().__init__(kwargs, {
            'name': str,
            'contextIp': (list, ContextIp),
        })

    @staticmethod
    def fromSomething(node: Tag|dict):
        schema = {
            'name': lambda x: str(x),
            'contextIp': lambda x: ContextIp.fromSomething(x),
        }
        return Element.fromSomething(ContextSplit, node, schema)

class ContextProject(Element):
    def __init__(self, **kwargs):
        super().__init__(kwargs, {
            'attributes': (list, str),
            'comment': str,
            'contexts': (list, str),
            'name': str,
        })

    @staticmethod
    def fromSomething(node: Tag|dict):
        schema = {
            'attributes': lambda x: [str(v) for v in x.split(',')],
            'comment': lambda x: str(x),
            'contexts': lambda x: [str(v) for v in x.split(',')],
            'name': lambda x: str(x),
        }
        return Element.fromSomething(ContextProject, node, schema)

class IP(Element):
    def __init__(self, **kwargs):
        super().__init__(kwargs, {
            'name': str,
            'version': str,
            'configFile': str,
            'instanceName': str,
            'clockEnableMode': str,
            'ipContextCoupling': str,
            'powerDomain': str,
            'contextSplit': (list, ContextSplit),
        })

    @staticmethod
    def fromSomething(node: Tag|dict):
        schema = {
            'name': lambda x: str(x),
            'version': lambda x: str(x),
            'configFile': lambda x: str(x),
            'instanceName': lambda x: str(x),
            'clockEnableMode': lambda x: str(x),
            'ipContextCoupling': lambda x: str(x),
            'powerDomain': lambda x: str(x),
            'contextSplit': lambda x: ContextSplit.fromSomething(x),
        }
        return Element.fromSomething(IP, node, schema)

class Voltage(Element):
    def __init__(self, **kwargs):
        super().__init__(kwargs, {
            'min': float,
            'max': float
        })




    @staticmethod
    def fromSomething(node: Tag|dict):
        schema = {
            'min': lambda x: float(x),
            'max': lambda x: float(x)
        }
        return Element.fromSomething(Voltage, node, schema)


class Current(Element):
    def __init__(self, **kwargs):
        super().__init__(kwargs, {
            'lowest': float,
            'run': float
        })

    @staticmethod
    def fromSomething(node: Tag|dict):
        schema = {
            'lowest': lambda x: float(x),
            'run': lambda x: float(x)
        }
        return Element.fromSomething(Current, node, schema)


class Temperature(Element):
    def __init__(self, **kwargs):
        super().__init__(kwargs, {
            'min': float,
            'max': float
        })

    @staticmethod
    def fromSomething(node: Tag|dict):
        schema = {
            'min': lambda x: float(x),
            'max': lambda x: float(x)
        }
        return Element.fromSomething(Temperature, node, schema)


class GentypeFirmware(Element):
    def __init__(self, **kwargs):
        super().__init__(kwargs, {
            'firmwareName': str,
            'genType': str,
        })

    @staticmethod
    def fromSomething(node: Tag|dict):
        schema = {
            'firmwareName': lambda x: str(x),
            'genType': lambda x: str(x)
        }
        return Element.fromSomething(GentypeFirmware, node, schema)

class Context(Element):
    def __init__(self, **kwargs):
        super().__init__(kwargs, {
            'comment': str,
            'genType': str,
            'core': str,
            'groupName': str,
            'groupShortName': str,
            'name': str,
            'shortName': str,
            'longName': str,
            'secure': bool,
            'semaphoreSuffix': str,
            'powerDomain': str,
        })

    @staticmethod
    def fromSomething(node: Tag|dict):
        schema = {
            'comment': lambda x: str(x),
            'genType': lambda x: str(x),
            'core': lambda x: str(x),
            'groupName': lambda x: str(x),
            'groupShortName': lambda x: str(x),
            'name': lambda x: str(x),
            'shortName': lambda x: str(x),
            'longName': lambda x: str(x),
            'secure': lambda x: parseBool(x),
            'semaphoreSuffix': lambda x: str(x),
            'powerDomain': lambda x: str(x),
        }
        return Element.fromSomething(Context, node, schema)




class MCU(Element):
    def __init__(self, **kwargs):
        super().__init__(kwargs, {
            'name': str,
            'fwLibrary': str,
            'clockTree': str,
            'dbVersion': str,
            'family': str,
            'hasPowerPad': bool,
            'ioType': str,
            'line': str,
            'package': str,
            'refName': str,
            'ip': (list, IP),
            'pin': (list, Pin),
            'core': (str, list),
            'frequency': int,
            'ram': (int, list),
            'ccmRam': (int, list),
            'flash': (int, list),
            'e2prom': (int, list),
            'ionb': int,
            'die': str,
            'voltage': Voltage,
            'current': Current,
            'temperature': Temperature,
            'genTypeFirmware': (list, GentypeFirmware),
            'context': (list, Context),
            'contextProject': (list, ContextProject),
            'memoryMap': bool,
            'trustZone': bool,
            'LPBAM': bool,
            'bootPath': bool,
        })


    @staticmethod
    def fromSomething(node: Tag|dict):
        schema = {
            'clockTree': lambda x: str(x),
            'dbVersion': lambda x: str(x),
            'family': lambda x: str(x),
            'hasPowerPad': lambda x: parseBool(x),
            'ioType': lambda x: str(x),
            'line': lambda x: str(x),
            'package': lambda x: str(x),
            'refName': lambda x: str(x),
            'name': lambda x: str(x),
            'fwLibrary': lambda x: str(x),
            'ip': lambda x: IP.fromSomething(x),
            'pin': lambda x: Pin.fromSomething(x),
            'core': lambda x: str(x.text),
            'frequency': lambda x: int(x.text),
            'ram': lambda x: int(x.text),
            'ccmRam': lambda x: int(x.text),
            'flash': lambda x: int(x.text),
            'e2prom': lambda x: int(x.text),
            'ionb': lambda x: int(x.text),
            'die': lambda x: str(x.text),
            'voltage': lambda x: Voltage.fromSomething(x),
            'current': lambda x: Current.fromSomething(x),
            'temperature': lambda x: Temperature.fromSomething(x),
            'genTypeFirmware': lambda x: GentypeFirmware.fromSomething(x),
            'context': lambda x: Context.fromSomething(x),
            'contextProject': lambda x: ContextProject.fromSomething(x),
            'memoryMap': lambda x: parseBool(x.text),
            'trustZone': lambda x: parseBool(x.text),
            'LPBAM': lambda x: parseBool(x.text),
            'bootPath': lambda x: parseBool(x.text),

        }
        return Element.fromSomething(MCU, node, schema, ignore=['xmlns'])
