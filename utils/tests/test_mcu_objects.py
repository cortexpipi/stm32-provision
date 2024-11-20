import unittest
import stm32import.MCU as MCU



class TestMCUObject(unittest.TestCase):
    def test_truth_parser(self):
        true_values = ['true', 'True', 'TRUE', '1', 'yes', 'Yes', 'YES', 'Available']
        false_values = ['false', 'False', 'FALSE', '0', 'no', 'No', 'NO', 'Unavailable']
        for value in true_values:
            self.assertTrue(MCU.parseBool(value))
        for value in false_values:
            self.assertFalse(MCU.parseBool(value))

    def test_mcu_pin(self):
        inputData = {
            'name': 'PA0',
            'type': MCU.Pin.Type.IO,
            'position': '100',
            'variant': 'reset',
            'requestToSecureIP': True,
            'signal': [
                MCU.Signal(**{'name': 'ADC1_IN0', 'ioModes': MCU.Signal.Mode.ANALOG}),
            ],
        }
        pin = MCU.Pin(**inputData)
        for key in inputData:
            self.assertEqual(getattr(pin, key), inputData[key])
        inputData['signal'] = MCU.Signal(**{'name': 'ADC1_IN0', 'ioModes': MCU.Signal.Mode.ANALOG})

    def test_mcu_object(self):
        inputData = {
            'refName': 'STM32F103C8',
            'family': 'STM32F1',
            'line': 'STM32F103',
            'package': 'LQFP48',
            'ram': 20,
            'flash': 64,
            'pin': [
                MCU.Pin(**{'name': 'PA0', 'type': MCU.Pin.Type.IO}),
            ]

        }
        mcu = MCU.MCU(**inputData)
        for key in inputData:
            self.assertEqual(getattr(mcu, key), inputData[key])


if __name__ == '__main__':
    unittest.main()
