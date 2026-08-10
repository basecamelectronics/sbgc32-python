# Как добавить команду
Пример для CMD_BOARD_INFO_3

В commands.py добавляем команду и описание 
```CMD_BOARD_INFO_3            = 2     # Request additional board information```

в `native/sbgc_python.h` добавляем структуру для функции и ее прототип
```c
typedef struct 
{
    uint8_t device_id[9];
    ...
    uint8_t adjustable_variables_total;
    
} sbgc_py_board_info_3_t;

SBGC_PY_API sbgc_py_status_t sbgc_py_get_board_info_3 (
							sbgc_py_device_t *device, 
							sbgc_py_board_info_3_t *board_info);

```

в `native/sbgc_python.c` реализуем саму функцию

в ней объявляем структуру из `native/sbgc_python.h` и `sbgcCommandStatus_t`

ставим защиту
```c
if (device == NULL || angles == NULL)
        return SBGC_PY_INVALID_ARGUMENT;
    if (!device->connected)
        return SBGC_PY_NOT_CONNECTED;
    if (current_device != device)
        return SBGC_PY_ERROR;
```
		
инициализуем нулями `device->last_tx_size` и `device->last_rx_size`

дальше вызов оригинальной функции из библиотеки и заполнение полей структуры 
```c
status = SBGC32_ReadBoardInfo3(&device->serial_api, &native_board_info);
...
board_info->script_slot_1_size = native_board_info.scriptSlot1_Size;
...
```

в `src/sbgc32/native.py` добавляем структуру, она же является классом для фасада
Не нужно передавать структуры Serial API прямо в Python, они зависят от настроек
библиотеки, упаковки полей и её версии
```python
class NativeBoardInfo3(ctypes.Structure):
    _fields_ = [
        ("device_id", ctypes.c_uint8 * 9),
        ("mcu_id", ctypes.c_uint8 * 12),
        ("eeprom_size", ctypes.c_uint32),
	...
	]
```

ниже class NativeLibrary, в нем `def __init__` добавляем состояние fallback:

```python
self._raw_board_info_3_devices: set[int] = set()
```

в `def _configure_functions()` добавляем `argtypes` и `restype` с указанием класса `NativeBoardInfo3`

```python
lib.sbgc_py_get_board_info_3.argtypes = [
    ctypes.c_void_p,
    ctypes.POINTER(NativeBoardInfo3),
]
lib.sbgc_py_get_board_info_3.restype = ctypes.c_int
```

и ниже реализуем функцию, которую будет вызывать пользователь 
```python
def get_board_info_3(self, device: int) -> NativeBoardInfo3:
```
а также подфункцию
```python
def _get_board_info_3_raw(self, device: int) -> NativeBoardInfo3 | None:
```

в `src/sbgc32/types.py` реализуем класс BoardInfo3 с указанием типов:

```python
@dataclass(frozen=True, slots=True)
class BoardInfo3:
    device_id: bytes
    mcu_id: bytes
    eeprom_size: int
    script_slot_sizes: tuple[int, ...]
    profile_set_slots: int
    ...
```

теперь в `src/sbgc32/device.py` можно импортировать наш класс и реализовать 
```python
from .types import Angles, Axis3, BoardInfo, BoardInfo3
```

дальше функцию можно запустить в main:

```python
def main() -> None:
    print("Opening COM port...", flush=True)
    with SimpleBGC(port="COM4", baudrate=115200) as gimbal:
		info = gimbal.get_board_info_3()

		print(info.device_id.hex())
		print(info.mcu_id.hex())
		print(info.eeprom_size)
```

Эта схема сохраняет границы слоёв. Python не работает с внутренними структурами
Serial API, а вызывает маленький стабильный C-фасад. Для каждой новой команды
добавляются только нужные данные.


## Шаблон Python

```python
# src/sbgc32/native.py
class NativeExample(ctypes.Structure):
    _fields_ = [("value", ctypes.c_uint32)]

lib.sbgc_py_get_example.argtypes = [
    ctypes.c_void_p,
    ctypes.POINTER(NativeExample),
]
lib.sbgc_py_get_example.restype = ctypes.c_int

# src/sbgc32/types.py
@dataclass(frozen=True, slots=True)
class Example:
    value: int

# src/sbgc32/device.py
def get_example(self) -> Example:
    value = self._native.get_example(self._handle)
    return Example(value=value.value)
```

COM-порт открывается внутри DLL через Windows API. Поэтому при добавлении
команды Python не должен работать с портом напрямую. Весь обмен остаётся в
`native/sbgc_python.c`, а Python получает только готовую структуру результата

## Сборка DLL

В PowerShell из корня проекта

```powershell
cmake -S native -B build/native -A x64
cmake --build build/native --config Release
```

DLL появится здесь:

`src/sbgc32/_native/sbgc_python.dll`.

Перед пересборкой нужно остановить Python-скрипты и отладку в PyCharm. Windows не
позволяет заменить DLL, которая уже загружена запущенным процессом.
