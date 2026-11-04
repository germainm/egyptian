"""
Decoder of the sequential JPEG images with samples of 12 bits. The expected
values come from libjpeg-turbo 3.1.3, which made the images of these tests:
this project does not depend on it.
"""
import base64
from array import array
import contextlib
import functools
import hashlib
import importlib.util
import time
import io
import unittest
from unittest import mock

from PIL import Image

from django.test import SimpleTestCase

from ..renderers import dicom, jpeg_extended

PYDICOM = importlib.util.find_spec('pydicom') is not None

# A ramp of 24 by 16 pixels from 0 to 4095.
JPEG_12_BITS = base64.b64decode((
    '/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAIBAQEBAQIBAQECAgICAgQDAgICAgUEBAMEBg'
    'UGBgYFBgYGBwkIBgcJBwYGCAsICQoKCgoKBggLDAsKDAkKCgr/wQALDAAQABgBAREA/8QA'
    'FQABAQAAAAAAAAAAAAAAAAAADA3/xAAbEAABBAMAAAAAAAAAAAAAAAALACg3RVRicv/aAA'
    'gBAQAAPwCXjAUwKcMMywKDjVNeQKYFOGGY4FBxqmvAFMCnDDMcCg41QocCmBThhmOBQcap'
    'rwBTApwwzHAoONU15ApgU4YZjgUHGq//2Q=='
))
JPEG_12_BITS_SHA256 = '1548f9360609bfa4045ed251ebd67927afb777a621c9d195e4f60336cb231f77'
# The ramp inverted, for a second frame.
JPEG_12_BITS_INVERTED = base64.b64decode((
    '/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAIBAQEBAQIBAQECAgICAgQDAgICAgUEBAMEBg'
    'UGBgYFBgYGBwkIBgcJBwYGCAsICQoKCgoKBggLDAsKDAkKCgr/wQALDAAQABgBAREA/8QA'
    'FQABAQAAAAAAAAAAAAAAAAAADA3/xAAbEAABBAMAAAAAAAAAAAAAAAALACg3RVRicv/aAA'
    'gBAQAAPwCoanrD1kzvNz7/AL2QoY9Yesmd52ff97IUOesPWTO87Pv+9k14PWHrJnedn3/e'
    'yFDnrD1kzvOz7/vZChj1h6yZ3nZ9/wB7L//Z'
))
JPEG_12_BITS_INVERTED_SHA256 = '974e8fccf4f4bc9be93bd628d8d20e75ff2aba33da5e3539818c3cb77bdbc6c3'
# The ramp in RGB, stored in YCbCr with all the samples.
JPEG_12_BITS_COLOR = base64.b64decode((
    '/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAIBAQEBAQIBAQECAgICAgQDAgICAgUEBAMEBg'
    'UGBgYFBgYGBwkIBgcJBwYGCAsICQoKCgoKBggLDAsKDAkKCgr/2wBDAQICAgICAgUDAwUK'
    'BwYHCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCg'
    'r/wQARDAAQABgDAREAAhEBAxEB/8QAFgABAQEAAAAAAAAAAAAAAAAADAsN/8QAHhAAAAYD'
    'AQEAAAAAAAAAAAAAAAoLN0RUJ2FyARf/xAAWAQEBAQAAAAAAAAAAAAAAAAAMCg3/xAAiEQ'
    'AAAgoDAAAAAAAAAAAAAAAACggJJCYzNkJDUVNhcuL/2gAMAwEAAhEDEQA/AIJSQmcWbD36'
    'nTmc7D8A+stLmlu3VduQcRRfIUwHWxZ8hTOkJnFWwynTmc7Aoc+stLmlu3VduRRkjAQpgO'
    'tiz5CmZITOLNhlOnM52BQ59ZaXNLduq7cijBGAhTAdbFnyMXISEzirYZSpzOdjWZD6y0ua'
    'W7dV25CRZF8hTAdbFnyFMyQmcWbDKdOZzsChz6y0uaW7dV25FGSMBCmA62LPkKZ0hM4q2G'
    'U6cznYFDH1lpc0t26rtyKMEYCFMB1sWfI//9k='
))
JPEG_12_BITS_COLOR_RGB_SHA256 = '20a2df959e7cd757bd7f11601f7f8f61b70edd46d7caf6dbbfe5d20bd5349602'
JPEG_12_BITS_COLOR_SHA256 = '4fb1aa5d8355e405e213b06b81bac8a0a3a52e6856568362a74c76b6f733f59f'
# The same with half of the chroma samples: the luma is compared.
JPEG_12_BITS_SUBSAMPLED = base64.b64decode((
    '/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAIBAQEBAQIBAQECAgICAgQDAgICAgUEBAMEBg'
    'UGBgYFBgYGBwkIBgcJBwYGCAsICQoKCgoKBggLDAsKDAkKCgr/2wBDAQICAgICAgUDAwUK'
    'BwYHCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCg'
    'r/wQARDAAQABgDASIAAhEBAxEB/8QAFgABAQEAAAAAAAAAAAAAAAAADAAL/8QAHhAAAAYD'
    'AQEAAAAAAAAAAAAAAAoLN0RUJ2FyARf/xAAXAQADAQAAAAAAAAAAAAAAAAAJCgsN/8QAKx'
    'EAAAEHCwUAAAAAAAAAAAAAAAoLJSdDUmEBAwQGCAkpNDdEYlRjcXKk/9oADAMBAAIRAxEA'
    'PwDBKSEzizYe/U6cznYUzpCZxVsMp05nOwAuSEzirYZSpzOdhTMkJnFmwynTmc7Fr4/WFS'
    '2qSc6xp7xA5rr8wp5JVruz8cA/RSEzizYZTpzOdiGUqkJnFWwynTmc7EMjYLdCpfHhrunH'
    'mnfnYh8SzeYU1Y0ZVvxwk4D/2Q=='
))
# Made by libjpeg-turbo 3.1.3, with the SHA-256 of the samples it reads from them.
JPEG_12_BITS_SAMPLINGS = {
    '2h1v': (
        (
            '/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAMCAgMCAgMDAwMEAwMEBQgFBQQEBQoH'
            'BwYIDAoMDAsKCwsNDhIQDQ4RDgsLEBYQERMUFRUVDA8XGBYUGBIUFRT/2wBDAQME'
            'BAUEBQkFBQkUDQsNFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQU'
            'FBQUFBQUFBQUFBQUFBT/wQARDAAQABgDASEAAhEBAxEB/8QAFQABAQAAAAAAAAAA'
            'AAAAAAAACwD/xAAwEAAAAQoEBAUFAAAAAAAAAAAGAwQFBwgJFRYXGAETFBkKERIa'
            'AAILGyUmQ0Vndf/EABgBAAIDAAAAAAAAAAAAAAAAAAsMBgkK/8QAJxEAAAQFBAMA'
            'AwEAAAAAAAAAAgMEBQEGBxQVEhMWFwgJEQoYGSX/2gAMAwEAAhEDEQA/ABaOF0cW'
            'OMGd+FJaqdJuk2t13NQeklr4WwjFivgX8S10GdGLYzOTVxudBMsHAECA4WDSISZ6'
            'gDpLBpms2KnBuqkSEvKSHgixxTBDA3LFkCnm7cds3J9uVvFIq1LbGlTsEaQk9fu4'
            'wqUKSXI5MYl2NSuy9rorSHLqCJeuGaYtL1EP4xNa6nLJoapgmZASRPRrm4r1qEAo'
            'RSkz24M4GyoTKWOB5gYtjFTIJMxNRsFhpZzwMRBTs8GwwQcQvqr8KKxr5zKmicJb'
            'Tp6knPDw5uDaXEMURFSnVgAz1Tl4oyCkwEWeW6PBTzWynwXnFHv5g05L4/nwjLYE'
            '8+F0UM/PZ34rZqp7Y6TYfUi1B6tovhU6MV0+BcOrXSpqYscs5Mom5qEyIcHoIEZY'
            'SohGHqfOkSGmazksbm61hIV8pUeCLDFDkMTcsRQN4ZLfD2WPTvU2h0oK/Pasj/Kr'
            'mgbG9BLJTYnPNA4yIjSlkyc9LIly27wA5uzKFOrcChmITC1AxBG0tooRSgI1yz6b'
            '/QhWGSpSW+zetszyU8NrO1tknksyNSeW601QIy08gzCviTKD7At4e5fClXOhAzW0'
            '0pUYMBjG0ChFGWK24hUrcnLz4rt19l233LVp7YrTyW93HU8iF0FJJXQ8xQWaItFK'
            'RCfLtj64ybwrODyMDiB21bBL3xW+Jup5f25n7DuLcv7VJ6dzX+mdJat+LhP02qSf'
            'i9TzZYGXebZHa22/ku7qv8b8dexN+4M19l6up729Nv8AYxuYevmABHfUx66MfjpU'
            '5pldjS18u3NeTxPx67Vubo3c7f1dH5HIH5O2xOemHTxgCMLiFw9cnLznXf8A9l23'
            '3LWX7nVPkt7uOp5F7X6tzQh5igs0QmF1dE+XbH0QY3hWSHrw0S+tzzX6soA1pP0J'
            '7tyHxwvMTfcTvQhP671cYebbg+rBWW4gtLbZw7XptQFpfF2mPS1OUiH+W/7E5T/U'
            'v8DkuEZGEFPVWvhr/adca+NY7dbLG02MCzabIv8A/9k='
        ), '6844a168eab8477291fc8891c91cabbbd7d84d788426228222195a6b66ee67a6'
    ),
    '2h2v': (
        (
            '/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAMCAgMCAgMDAwMEAwMEBQgFBQQEBQoH'
            'BwYIDAoMDAsKCwsNDhIQDQ4RDgsLEBYQERMUFRUVDA8XGBYUGBIUFRT/2wBDAQME'
            'BAUEBQkFBQkUDQsNFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQU'
            'FBQUFBQUFBQUFBQUFBT/wQARDAAQABgDASIAAhEBAxEB/8QAFwAAAwEAAAAAAAAA'
            'AAAAAAAAAAoLCf/EADAQAAABCgQEBQUAAAAAAAAAAAYDBAUHCAkVFhcYARMUGQoR'
            'EhoAAgsbJSZDRWd1/8QAFwEAAwEAAAAAAAAAAAAAAAAACQoLDP/EAB8RAAIDAQAC'
            'AwEAAAAAAAAAAAMEAgUGAQAHCAkKEv/aAAwDAQACEQMRAD8Ai0cLo4scYM78KS1U'
            '6TdJtbruag9JLXwthGLFfAv4lroM6MWxmcmrjc6CZYOAIEBwsGkQkz1AHSWDTNZs'
            'VODdVIkJeUkPBFjimCGBuWLIGnm7cds3J9uVvFIq1LbGlTsEaQk9fu4wqUKSXI5M'
            'Yl2NSuy9rorSHLqCJeuGaYtL2JziFStycvPiu3X2XbfctWntitPJb3cdTyIXQUkl'
            'dDzFBZoi0UpEJ8u2PrjJvCs4PUYHEDtq2CXvit8TdTy/tzP2HcW5f2qT07mv9M6S'
            '1b8XCfptUr8wPyttCWlK004zJ+TJizmVtMr/AF8qcQ2JjWIecqz3h6v+V7+/XjzN'
            'aPNchlstCGwgQngqfqi+h66LdKOOVzkrOTjZiEM0gazlZmQivasMWoI8pmdGzTci'
            'rp9OrHmR1mR4PF4sY94MpfGROF0UM/PZ34rZqp7Y6TYfUi1B6tovhU6MV0+BcOrX'
            'SpqYscs5Mom5qEyIcHoIEZYSohGHqfOkSGmazksbm61hIV8pUeCLDFDkMTcsRQJ4'
            'YdcQuHrk5ec67/8Asu2+5ay/c6p8lvdx1PIva/VuaEPMUFmiEwurony7Y+iDG8Ky'
            'Q8eNNT8DfkB6auPQ+env0Mg0USy4le3uM3uhKNAYYRSDWmzJYAq6MQORhUUFxyWl'
            'pU+DRvpzsBl75UI9N/nk9AX2Boye0MXhHTBTVCn3S+uvZupMKsEGEK9eoPjzDXps'
            '4BfkIUWYvuS12eQ4Ku0xJ2gjS7//2Q=='
        ), '90124df20c09eca0a61cb2bfe93b1b10325667d03bd0af0d4aa9ce368fce862c'
    ),
    '1h2v': (
        (
            '/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAMCAgMCAgMDAwMEAwMEBQgFBQQEBQoH'
            'BwYIDAoMDAsKCwsNDhIQDQ4RDgsLEBYQERMUFRUVDA8XGBYUGBIUFRT/2wBDAQME'
            'BAUEBQkFBQkUDQsNFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQU'
            'FBQUFBQUFBQUFBQUFBT/wQARDAAQABgDARIAAhEBAxEB/8QAFgABAQEAAAAAAAAA'
            'AAAAAAAACgkL/8QALxAAAAIIBAUDBQEAAAAAAAAABAYDBQcICRUWGAETFxkKERIU'
            'GgILGyUmQ0Vndf/EABUBAQEAAAAAAAAAAAAAAAAAAAoL/8QAIxEAAQMDAwUBAAAA'
            'AAAAAAAABQMEBgECBxITFQgJFBYXEf/aAAwDAQACEQMRAD8AxaOF0gWQMHd+FJeq'
            'hJwk3t23PQe0lt4awrGixgY8TV1GKAvjO5PXBxRTTFwhEguJi0qFmNUApbFp2sMl'
            'EB2UmRF6UR8MWOK4QYB0yZQtCgQsVuTp6MV46+y7b7ls0+MV08pvdx7nkgug0kpd'
            'T1FJaom000iM+XbH1zkPKs4vSbO2r1ayh5k6OyaQESas6RR0MXr8sHITtFrWi9L0'
            'wuQhltuMgQytqjyioqRI3mFk1SySF1FTALSR/pq7E8zf5jj0wlDQwtklu3qmNIky'
            '4ArkpBlW1zRRKPZTD2W4ejYetij+i4WVt1D66SxxFtfRc/G62WxhuQ2bk/HK3ilV'
            'altjUp4COkKPv93GVUhpJcjkzinZ1S7r3fTXSHL1BMvXLO2TU8q+BBDatgp76Vvi'
            'bqeX+Op/A7m3L/a0n07qv+M9pat+rlP23W97UXVN4Xsfrrja5HV7Lx9eN8/Vv7/0'
            'TldX0vXuPfN+T7Hn7pjjfzmgGhinRV2FOP8Ad/VBGxyu77dxdnE8nr8ryfqvNUu+'
            'v7m6Q5H4f43J757idPsMY0JE4XRg0c93fitnqotkJNx9iL0Hu2jeGTqxnUYGA61d'
            'ahQLnLuTqIcKU0JcPpIMaYyqhWDV+KVJadrEpg4dqxkS+lKfDFhip0GIdMhUKHYE'
            'MB65OnoOu/8A7LtvuW0v5OqvKb3ce55J7X9W6oU9RSWqJTK9XTPl2x9EmDyrJL1b'
            '3tq9S8XeYxjsZkFBisFRW1sWT8WYIQRF1Wq9b1AuPRl1uTQROtyjyqpWRLXh1lFS'
            'yqFtEjALSxXpq7AMMf4cj0PlEdDrY2buKqDR5MEfK41Qe1uc1UVj2LA91uYY2Yre'
            'q/qsalbhQAuqscWb2UQPxuln/9k='
        ), '600a6b2cceddd297658fb75483ec1435b1b2bb7d0527258ffdfd80fe6b31cdd5'
    ),
    '4h1v': (
        (
            '/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAMCAgMCAgMDAwMEAwMEBQgFBQQEBQoH'
            'BwYIDAoMDAsKCwsNDhIQDQ4RDgsLEBYQERMUFRUVDA8XGBYUGBIUFRT/2wBDAQME'
            'BAUEBQkFBQkUDQsNFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQU'
            'FBQUFBQUFBQUFBQUFBT/wQARDAAQACADAUEAAhEBAxEB/8QAFQABAQAAAAAAAAAA'
            'AAAAAAAACgv/xAAwEAAAAggFAwMDBQAAAAAAAAAEBgMFBwgJFRYYARITFxkKFBoC'
            'CxsRIyUmQkVndf/EABYBAQEBAAAAAAAAAAAAAAAAAAkICv/EACQRAAECBQUBAAMA'
            'AAAAAAAAAAIEBQEDBhMUChESFRYIByQl/9oADAMBAAIRAxEAPwCGf068GCBg7v0p'
            'L2MJOEm92256D2ktvDWFa0WMDHiaupBQF8Z3J64OKKacuEIjlxMWlQsxqgFLYtO1'
            'hkwgOykyIvSiPhjxxXCDAOmTKGgW584bcn46PMUrrUuMalPAQ2h9Hf8ALjKqQ2ku'
            'R0ZxTs6pd17vprtDp7gmXPLO2TU9QM6dZnMc93fqt3sYtkJNyNiL0Hu2jeGTq1nU'
            'YGA61dahQLnLuTqIcKU0JcPpIMaYyqhVjV+KVJadrEpg4dqxkS+lKfDHhip0GIdM'
            'hUKVOnWgvwMHd+lJexhJwk3u23PQe0lt4awrWixgY8LVlIKAvjO5PXBxRTTFwhEc'
            'uJi0qFmNUApbFp2sMmEB2UmRF6UR8MeOK4QYB0yZQ2/oZPyjU850phwc5IA+mpmz'
            '58gYwtA+qEYJahRDG4UIpkNMwBxSneITWRiAq1h/owHPTQ/IlZT3lodHhply6lNY'
            'pUqEw7WZdSqkAo6pbwK4UIo22joS3VEcJ5hMXlGWC5ef80YL0IMkXJyWMV47XC7b'
            '7kZp8Yrt7TfLj3P2LoNpKXU9RSWqJtNNojPp2x55yHlWsXm8wg3DbYJL+O5xOVPJ'
            '+yp/A7m/0/2tp9u6r/pntLVv4uU/ptvMIOCjcnJYOvkB8LtvuRpfydVeU3y49z9E'
            '9r+7dUKeopLVEple7pn07Y8kmDyrRLzeYQZIuTkkYrx2uF233IzT4xXbym+XHufs'
            'XQbSUup6iktUTaabRGfTtjzzkPKtYvFVoXa3s+Ubu8yOFlP2XPfIxuKr0Vy4W/pt'
            '/J37x5FvGzFu2BDc5pmPiTH6Jp7bL4W0vb8t8nE2W+ru3S5ew38PkZB5NrEz3Hbq'
            'x//Z'
        ), '0c03b0db6044def95984f913f465495d847214450130d29cd9008962f3cbcc14'
    ),
    '2h2v odd size': (
        (
            '/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAMCAgMCAgMDAwMEAwMEBQgFBQQEBQoH'
            'BwYIDAoMDAsKCwsNDhIQDQ4RDgsLEBYQERMUFRUVDA8XGBYUGBIUFRT/2wBDAQME'
            'BAUEBQkFBQkUDQsNFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQU'
            'FBQUFBQUFBQUFBQUFBT/wQARDAANABEDASIAAhEBAxEB/8QAFgABAQEAAAAAAAAA'
            'AAAAAAAACgsA/8QAMBAAAAIGCQMCBwAAAAAAAAAABAUDBgcICRYBAgoUFRcYGRoA'
            'CxMREhxaW5WX19j/xAAWAQEBAQAAAAAAAAAAAAAAAAAICgv/xAAjEQABBQAABgMB'
            'AAAAAAAAAAADAQIEBQYABwgJChlVl9TV/9oADAMBAAIRAxEAPwCUlYurOJAwd3sp'
            'LzsJOEm9g256DtJbeGsFbRYwMeFqxEKAvjO5PXBxSpplcUJSFcTK0UGY0gFGytO1'
            'hkwgOylZEVVEvix00nCCgOmTENqaBFBw1J8b3eKI9KW2NKXAQyiRX/dxwqT8pNSP'
            'hxiXcald16/YrlD48wVl9+GXZNLwprF0/wDQ/owdlIed7gY7RCTYjDls0UKlrBW5'
            '09BYrWUUE1dzl/lpBuKVMtAtsXgQBISxUKh+WiW0qEPQ1TNmx8L8rFVc9hohrVgK'
            'UltTQInEGfQXON7qjRbmPN9lLZezeQ0VOLpPcnyzpuxCk1vEo55M8uMmZX+uRqte'
            'DD/cAwM/eDD1dbYGozlbZJPS7ZZz45mGkRSWiXcanHLvhSJompXF0os2rDaq4AxM'
            '/d45R0GcCHUsedX/ANjXxnQxtnEqLaFIboh3FvEkMkS68t0mjh0DJ2nDKsAtSpPr'
            'wZJRyNrfRhty+iwKizGTBH2jCSVTTuTd88+S1gj/AJcVf+k+t0074ddtX31ZmNz9'
            'ia9+/ut1vY+zjt2/P8nvr/mr+/isv0edlv5zp6+r+dH9Pj//2Q=='
        ), '80ab223ff579767b5896fe02779027af1fcfb992ed8f315ebcdcd4c355555427'
    ),
    '2h1v narrow': (
        (
            '/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAMCAgMCAgMDAwMEAwMEBQgFBQQEBQoH'
            'BwYIDAoMDAsKCwsNDhIQDQ4RDgsLEBYQERMUFRUVDA8XGBYUGBIUFRT/2wBDAQME'
            'BAUEBQkFBQkUDQsNFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQU'
            'FBQUFBQUFBQUFBQUFBT/wQARDAAIAAMDASEAAhEBAxEB/8QAFQABAQAAAAAAAAAA'
            'AAAAAAAAAAb/xAAgEAAABAYDAAAAAAAAAAAAAAAACQoLAQMEBio3R1Ro/8QAFQEB'
            'AQAAAAAAAAAAAAAAAAAACgz/xAAnEQAAAwIPAAAAAAAAAAAAAAAEBgoAKAEDBQgJ'
            'FRkzN0RFUlZmZ//aAAwDAQACEQMRAD8AkEkrDmxhxTcl/wCWwdxrWn4OufsT/NQC'
            'l5oElEKnOyMmiu7E3Dgj6gE4zJfe2S4X0dKxipwbhpAuovNgdkHpDf/Z'
        ), '2a52ed064fd605b97a4e1f83dbbe44b168c110dc92c5a2cf984761527d93b4e8'
    ),
    '2h2v narrow': (
        (
            '/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAMCAgMCAgMDAwMEAwMEBQgFBQQEBQoH'
            'BwYIDAoMDAsKCwsNDhIQDQ4RDgsLEBYQERMUFRUVDA8XGBYUGBIUFRT/2wBDAQME'
            'BAUEBQkFBQkUDQsNFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQU'
            'FBQUFBQUFBQUFBQUFBT/wQARDAAIAAIDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAA'
            'AAAAAAAAAAb/xAAgEAABAgUFAAAAAAAAAAAAAAAABgkECAsMGSo3R1Zo/8QAFQEB'
            'AQAAAAAAAAAAAAAAAAAACwz/xAAoEQAAAAoLAAAAAAAAAAAAAAAAAQQFBgcICUVm'
            'AgMLFBknKDI2UVX/2gAMAwEAAhEDEQA/AJRlG316GJhqkM1Zr3GwaC4MVHXYHzSA'
            'Cr9dVmVtDD/Z/wBY6y+HIxFDD4hDLgP4ltlUuer1W59Le3Uo8h3Y5DD/2Q=='
        ), '11763d6b1e5e8225c39b8f34ce33f7baa34fe53703869312746ceca25ac6b671'
    ),
}
JPEG_12_BITS_SUBSAMPLED_LUMA_SHA256 = 'a22d8e31eda8d5f564a44f9c27a48fca80d7b6c05be274ebaf5360da83f83910'
# The pixels of JPGExtended.dcm, a sample file of pydicom.
SAMPLE_FILE_SHA256 = 'd30242775a414c01d616447854ebe3f2b20259822894bcd6891f879bcdcbf313'


def sha256(array):
    return hashlib.sha256(array.astype('<u2').tobytes()).hexdigest()


def make_jpeg(mode='L', **kwargs):
    """An 8-bit JPEG file made by Pillow, with what it decodes to."""
    import numpy

    generator = numpy.random.default_rng(seed=3)
    size = (37, 53) if mode == 'L' else (37, 53, 3)
    image = Image.fromarray(generator.integers(0, 256, size, dtype='uint8'))
    buffer = io.BytesIO()
    image.save(buffer, 'JPEG', quality=90, **kwargs)
    return buffer.getvalue()


class DecoderTestCase(SimpleTestCase):
    def test_12_bits(self):
        samples, precision = jpeg_extended.decode_jpeg(data=JPEG_12_BITS)
        self.assertEqual(precision, 12)
        self.assertEqual(samples.shape, (16, 24, 1))
        self.assertEqual(sha256(samples[:, :, 0]), JPEG_12_BITS_SHA256)

    def test_12_bits_whole_range(self):
        samples, precision = jpeg_extended.decode_jpeg(data=JPEG_12_BITS)
        self.assertEqual((samples.min(), samples.max()), (0, 4095))

    def test_12_bits_color(self):
        samples, precision = jpeg_extended.decode_jpeg(data=JPEG_12_BITS_COLOR)
        self.assertEqual(samples.shape, (16, 24, 3))
        self.assertEqual(sha256(samples), JPEG_12_BITS_COLOR_SHA256)

    def test_12_bits_subsampled(self):
        samples, precision = jpeg_extended.decode_jpeg(
            data=JPEG_12_BITS_SUBSAMPLED
        )
        self.assertEqual(samples.shape, (16, 24, 3))
        self.assertEqual(
            sha256(samples[:, :, 0]), JPEG_12_BITS_SUBSAMPLED_LUMA_SHA256
        )

    def test_components_enlarged_as_libjpeg_turbo(self):
        for name, (data, expected) in JPEG_12_BITS_SAMPLINGS.items():
            with self.subTest(name=name):
                samples, precision = jpeg_extended.decode_jpeg(
                    data=base64.b64decode(data)
                )
                self.assertEqual(sha256(samples), expected)

    def test_filter_of_two_samples_for_one(self):
        import numpy

        samples = numpy.array([[0, 100, 200]], dtype=numpy.uint16)
        self.assertEqual(
            jpeg_extended._enlarge(
                samples=samples, factor_horizontal=2, factor_vertical=1
            ).tolist(), [[0, 25, 75, 125, 175, 200]]
        )
        self.assertEqual(
            jpeg_extended._enlarge(
                samples=samples.T, factor_horizontal=1, factor_vertical=2
            ).T.tolist(), [[0, 25, 75, 125, 175, 200]]
        )

    def test_narrow_or_other_factors_repeated(self):
        import numpy

        samples = numpy.array([[0, 100]], dtype=numpy.uint16)
        self.assertEqual(
            jpeg_extended._enlarge(
                samples=samples, factor_horizontal=2, factor_vertical=1
            ).tolist(), [[0, 0, 100, 100]]
        )
        self.assertEqual(
            jpeg_extended._enlarge(
                samples=samples, factor_horizontal=4, factor_vertical=1
            ).tolist(), [[0, 0, 0, 0, 100, 100, 100, 100]]
        )

    def test_8_bits_as_pillow(self):
        for kwargs in (
            {}, {'restart_marker_blocks': 1}, {'restart_marker_blocks': 7},
            {'restart_marker_rows': 1}
        ):
            with self.subTest(kwargs=kwargs):
                data = make_jpeg(**kwargs)
                samples, precision = jpeg_extended.decode_jpeg(data=data)
                self.assertEqual(precision, 8)
                self.assertEqual(
                    samples[:, :, 0].astype('uint8').tobytes(),
                    Image.open(io.BytesIO(data)).tobytes()
                )

    def test_truncated_file_gives_what_it_holds(self):
        import numpy

        generator = numpy.random.default_rng(seed=5)
        buffer = io.BytesIO()
        Image.fromarray(
            generator.integers(0, 256, (256, 256), dtype='uint8')
        ).save(buffer, 'JPEG', quality=90)
        data = buffer.getvalue()
        complete, precision = jpeg_extended.decode_jpeg(data=data)
        with self.assertLogs(jpeg_extended.logger, level='WARNING'):
            partial, precision = jpeg_extended.decode_jpeg(
                data=data[:len(data) * 3 // 4]
            )
        self.assertEqual(partial.shape, complete.shape)
        self.assertEqual(partial[:32].tobytes(), complete[:32].tobytes())
        self.assertEqual(int(partial[-1, -1, 0]), 128)

    def test_files_refused(self):
        progressive = make_jpeg(progressive=True)
        no_frame = JPEG_12_BITS[:JPEG_12_BITS.index(b'\xff\xc1')] + b'\xff\xd9'
        for name, data in {
            'not a JPEG file': b'not a JPEG file',
            'empty': b'',
            'start of image alone': b'\xff\xd8',
            'no frame': no_frame,
            'progressive': progressive,
            'no scan': JPEG_12_BITS[:JPEG_12_BITS.index(b'\xff\xda')],
            'scan without component': JPEG_12_BITS[
                :JPEG_12_BITS.index(b'\xff\xda')
            ] + b'\xff\xda\x00\x03\x00'
        }.items():
            with self.subTest(name=name):
                with self.assertRaises(jpeg_extended.JPEGDecodeError):
                    jpeg_extended.decode_jpeg(data=data)

    def test_declared_size_limits(self):
        position = JPEG_12_BITS.index(b'\xff\xc1') + 5
        for size, message in ((4000, 'too short'), (9000, 'larger than')):
            data = (
                JPEG_12_BITS[:position] + size.to_bytes(2, 'big') * 2 +
                JPEG_12_BITS[position + 4:]
            )
            with self.subTest(size=size):
                with self.assertRaisesMessage(
                    jpeg_extended.JPEGDecodeError, message
                ):
                    jpeg_extended.decode_jpeg(data=data)

    def test_time_limit(self):
        with mock.patch.object(jpeg_extended, 'TIME_MAXIMUM', -1):
            with self.assertRaisesMessage(
                jpeg_extended.JPEGDecodeError, 'not decoded'
            ):
                jpeg_extended.decode_jpeg(data=JPEG_12_BITS)


def make_sequential_jpeg(
    blocks, rows, columns, dc_sizes=16, precision=12, restart_interval=0,
    trailing=b''
):
    """
    A sequential JPEG file of one component from its blocks of coefficients,
    each one a DC difference and (zeros before, value) pairs, for what the
    fixtures are too small to show. Its files give the samples of libjpeg-turbo
    as long as the values stay within what 12-bit samples can give.
    """
    # Codes of many lengths, as in a real file: the shortest for what is common.
    symbols_ac = [0x00, 0xF0] + [
        (run << 4) | size for size in range(1, 16) for run in range(16)
    ]
    lengths_ac = (
        0, 1, 2, 2, 2, 3, 3, 4, 6, 10, 16, 24, 30, 40, 48, 51
    )
    symbols_dc = list(range(dc_sizes))
    lengths_dc = (0, 0, 0, 0, dc_sizes) + (0,) * 11

    def get_codes(lengths, symbols):
        codes = {}
        code = 0
        index = 0
        for length, count in enumerate(lengths, start=1):
            for _ in range(count):
                codes[symbols[index]] = (code, length)
                code += 1
                index += 1
            code <<= 1
        return codes

    codes_ac = get_codes(lengths=lengths_ac, symbols=symbols_ac)
    codes_dc = get_codes(lengths=lengths_dc, symbols=symbols_dc)

    def segment(marker, content):
        return (
            b'\xff' + bytes((marker,)) + (len(content) + 2).to_bytes(2, 'big') +
            content
        )

    output = bytearray(b'\xff\xd8')
    output += segment(0xDB, b'\x00' + bytes([1] * 64))
    output += segment(
        0xC1, bytes((precision,)) + rows.to_bytes(2, 'big') +
        columns.to_bytes(2, 'big') + b'\x01\x01\x11\x00'
    )
    output += segment(0xC4, b'\x00' + bytes(lengths_dc) + bytes(symbols_dc))
    output += segment(0xC4, b'\x10' + bytes(lengths_ac) + bytes(symbols_ac))
    if restart_interval:
        output += segment(0xDD, restart_interval.to_bytes(2, 'big'))
    output += segment(0xDA, b'\x01\x01\x00\x00\x3f\x00')

    accumulator = 0
    bits = 0

    def write(value, size):
        nonlocal accumulator, bits
        accumulator = (accumulator << size) | value
        bits += size
        while bits >= 8:
            byte = (accumulator >> (bits - 8)) & 255
            output.append(byte)
            if byte == 255:
                output.append(0)
            bits -= 8
        accumulator &= (1 << bits) - 1

    def write_value(value):
        size = abs(value).bit_length()
        if size:
            write(value if value > 0 else value + (1 << size) - 1, size)
        return size

    for index, (difference, pairs) in enumerate(blocks):
        if restart_interval and index and not index % restart_interval:
            if bits:
                write((1 << (8 - bits)) - 1, 8 - bits)
            output += bytes((0xFF, 0xD0 + (index // restart_interval - 1) % 8))

        size = abs(difference).bit_length()
        write(*codes_dc[size])
        write_value(difference)

        coefficient = 1
        for zeros, value in pairs:
            while zeros > 15:
                write(*codes_ac[0xF0])
                zeros -= 16
                coefficient += 16
            size = abs(value).bit_length()
            write(*codes_ac[(zeros << 4) | size])
            write_value(value)
            coefficient += zeros + 1
        if coefficient < 64:
            write(*codes_ac[0x00])

    if bits:
        write((1 << (8 - bits)) - 1, 8 - bits)
    return bytes(output) + trailing + b'\xff\xd9'


@functools.lru_cache(maxsize=4)
def make_blocks(count, seed=5):
    """Blocks of a real image: flat parts, with few or many coefficients."""
    import random

    generator = random.Random(seed)
    blocks = []
    for index in range(count):
        # Each sixth of the image holds another kind of block.
        kind = index * 6 // count
        pairs = []
        coefficient = 1
        length = {0: 0, 1: 2, 2: 8, 3: 0, 4: 30, 5: 5}[kind]
        for _ in range(length):
            zeros = generator.randrange(0, 4 if kind != 5 else 24)
            if coefficient + zeros > 63:
                break
            size = generator.randrange(1, 15 if kind == 4 else 7)
            value = generator.randrange(1 << (size - 1), 1 << size)
            pairs.append((zeros, value if generator.random() < .5 else -value))
            coefficient += zeros + 1
        blocks.append(
            (generator.randrange(-40, 41) if kind else 0, pairs)
        )
    return blocks


@functools.lru_cache(maxsize=4)
def make_file(blocks_wide=64, blocks_high=64, **kwargs):
    return make_sequential_jpeg(
        blocks=make_blocks(count=blocks_wide * blocks_high),
        columns=blocks_wide * 8, rows=blocks_high * 8, **kwargs
    )


@contextlib.contextmanager
def readers_results():
    """The results of the arrays of readers, each one for a segment."""
    original = jpeg_extended._read_segment_with_readers
    results = []

    def wrapper(**kwargs):
        results.append(original(**kwargs))
        return results[-1]

    with mock.patch.object(
        jpeg_extended, '_read_segment_with_readers', wrapper
    ), mock.patch.object(jpeg_extended, 'READERS_BYTES_MINIMUM', new=1024):
        yield results


class ReadersTestCase(SimpleTestCase):
    """
    The arrays of readers against the Python loop, which defines the behavior.
    """
    def assert_same(self, first, second):
        # Not assertEqual: on lists this long, its message takes minutes.
        import numpy

        self.assertTrue(numpy.array_equal(first, second), 'Different samples.')

    def decode_both(self, data):
        with mock.patch.object(
            jpeg_extended, 'READERS_BYTES_MINIMUM', new=1 << 40
        ):
            expected = jpeg_extended.decode_jpeg(data=data)
        with readers_results() as results:
            samples, precision = jpeg_extended.decode_jpeg(data=data)
        self.assert_same(samples, expected[0])
        self.assertEqual(precision, expected[1])
        return samples, results

    def test_readers_are_used(self):
        samples, results = self.decode_both(data=make_file())
        self.assertEqual(results, [True])

    def test_8_bits(self):
        samples, results = self.decode_both(data=make_file(precision=8))
        self.assertEqual(results, [True])

    def test_restart_intervals(self):
        samples, results = self.decode_both(
            data=make_file(blocks_high=128, restart_interval=64 * 64)
        )
        self.assertEqual(results, [True, True])

    def test_small_segments_read_by_the_loop(self):
        samples, results = self.decode_both(data=make_file(restart_interval=8))
        self.assertEqual(results, [])

    def test_fixtures_of_libjpeg_turbo(self):
        # Too small for the readers to succeed each time: the result must not
        # depend on it.
        with mock.patch.multiple(
            jpeg_extended, READERS_BYTES_MINIMUM=1,
            READERS_SETTINGS=((float('inf'), 16, 14, 64),)
        ):
            samples, precision = jpeg_extended.decode_jpeg(data=JPEG_12_BITS)
        self.assertEqual(sha256(samples[:, :, 0]), JPEG_12_BITS_SHA256)

    def test_scans_of_one_component_of_several(self):
        # Interleaved: for the Python loop, even when it is large.
        source = Image.new('RGB', (512, 512))
        source.putdata(
            [
                (index % 251, index % 241, index % 239)
                for index in range(512 * 512)
            ]
        )
        buffer = io.BytesIO()
        source.save(buffer, 'JPEG', quality=95, subsampling=0)
        samples, results = self.decode_both(data=buffer.getvalue())
        self.assertEqual(results, [])

    def test_truncated_streams(self):
        data = make_file()
        start = data.index(b'\xff\xda') + 10
        for share in (50, 90, 99, 100):
            with self.subTest(share=share):
                self.decode_both(
                    data=data[:start + (len(data) - 2 - start) * share // 100]
                )
        # The last block cut in two.
        for missing in range(1, 8):
            with self.subTest(missing=missing):
                self.decode_both(data=data[:-2 - missing])

    def test_invalid_codes(self):
        data = make_file()
        start = data.index(b'\xff\xda') + 10
        for position in (start + 1, (start + len(data)) // 2, len(data) - 20):
            with self.subTest(position=position):
                damaged = bytearray(data)
                # Sixteen bits of ones: the tables have no such code.
                damaged[position:position + 6] = b'\xff\x00\xff\x00\xff\x00'
                samples, results = self.decode_both(data=bytes(damaged))
                self.assertEqual(results, [False])

    def test_invalid_code_with_enough_data_after_it(self):
        # The count of blocks does not reveal the damage: more data comes.
        data = make_file()
        start = data.index(b'\xff\xda') + 10
        scan = bytearray(data[start:-2])
        scan[len(scan) // 2:len(scan) // 2 + 6] = b'\xff\x00\xff\x00\xff\x00'
        samples, results = self.decode_both(
            data=data[:start] + bytes(scan) + data[start:-2] + data[-2:]
        )
        self.assertEqual(results, [False])

    def test_value_after_the_last_coefficient(self):
        # 63 zeros, then a value: the loop stops there.
        blocks = list(make_blocks(count=64 * 64))
        blocks[len(blocks) // 2] = (0, [(63, 1)])
        samples, results = self.decode_both(
            data=make_sequential_jpeg(blocks=blocks, columns=512, rows=512)
        )
        self.assertEqual(results, [False])

    def test_block_filled_to_its_last_coefficient(self):
        blocks = list(make_blocks(count=64 * 64))
        blocks[100] = (1, [(0, 3)] * 63)
        blocks[200] = (1, [(62, 3)])
        blocks[300] = (1, [(32, 1), (20, 1)])
        samples, results = self.decode_both(
            data=make_sequential_jpeg(blocks=blocks, columns=512, rows=512)
        )
        self.assertEqual(results, [True])

    def test_data_after_the_image(self):
        samples, results = self.decode_both(data=make_file(trailing=bytes(1000)))
        self.assertEqual(results, [True])

    def test_reader_that_does_not_resynchronize_in_time(self):
        # Too few symbols: a part is taken over by the reader before it, up to
        # one that fell on the right codes.
        with mock.patch.multiple(
            jpeg_extended, READERS_FAILURES_DIVISOR=1,
            READERS_ROUNDS_MAXIMUM=256,
            READERS_SETTINGS=((float('inf'), 2, 14, 512),)
        ):
            samples, results = self.decode_both(data=make_file())
        self.assertEqual(results, [True])

    def test_too_many_readers_that_do_not_resynchronize(self):
        with mock.patch.multiple(
            jpeg_extended, READERS_FAILURES_DIVISOR=64,
            READERS_SETTINGS=((float('inf'), 2, 14, 512),)
        ):
            samples, results = self.decode_both(data=make_file())
        self.assertEqual(results, [False])

    def test_readers_at_the_end_of_the_stream(self):
        # So many readers that some leave the data while they synchronize.
        with mock.patch.multiple(
            jpeg_extended, READERS_SETTINGS=((float('inf'), 2000, 30, 8),)
        ):
            samples, results = self.decode_both(data=make_file())
        self.assertEqual(results, [True])

    def test_dc_beyond_the_range_of_the_array(self):
        # The loop stops at the block where the array refuses the value.
        data = make_sequential_jpeg(
            blocks=[
                (65535, pairs) for difference, pairs in make_blocks(
                    count=182 * 182
                )
            ], columns=182 * 8, dc_sizes=17, rows=182 * 8
        )
        # The readers must go as far as the values: the flat parts of this
        # image are periodic, where they do not resynchronize.
        with mock.patch.multiple(
            jpeg_extended, READERS_FAILURES_DIVISOR=1,
            READERS_ROUNDS_MAXIMUM=1024
        ), self.assertLogs(jpeg_extended.logger, level='WARNING'):
            samples, results = self.decode_both(data=data)
        self.assertEqual(results, [False])

    def test_settings_according_to_the_bits_per_block(self):
        import numpy

        tables = jpeg_extended.ScanTables(
            table_ac=[0] * 65536, table_dc=[0] * 65536
        )
        words = jpeg_extended.get_words(data=bytes(4096))
        for count, spacing in ((32768, 8), (1000, 16), (10, 1024)):
            with self.subTest(count=count), mock.patch.object(
                jpeg_extended, 'READERS_SETTINGS', new=(
                    (5, 0, 12, 1), (100, 0, 11, 1), (float('inf'), 0, 11, 1024)
                )
            ):
                starts = jpeg_extended._get_reader_starts(
                    count=count, size_bits=32768, tables=tables, words=words
                )
                # After the first one: the others moved by one invalid code.
                self.assertEqual(int(numpy.diff(starts)[1]), spacing)

    def test_dc_size_beyond_the_limit(self):
        blocks = list(make_blocks(count=64 * 64))
        blocks[len(blocks) // 2] = (70000, [])
        samples, results = self.decode_both(
            data=make_sequential_jpeg(
                blocks=blocks, columns=512, dc_sizes=18, rows=512
            )
        )
        self.assertEqual(results, [False])

    def test_fewer_blocks_in_a_row_of_the_scan_than_of_the_component(self):
        # A scan of one component of several: its rows stop at the last block
        # that the image needs, those of the MCU of the frame go further.
        import numpy

        data = make_file()
        start = data.index(b'\xff\xda') + 10
        tables = {}
        position = 2
        while position < start - 10:
            size = int.from_bytes(data[position + 2:position + 4], 'big')
            if data[position + 1] == 0xC4:
                jpeg_extended.read_huffman_tables(
                    data[position + 4:position + 2 + size], tables
                )
            position += 2 + size

        def read(minimum):
            component = jpeg_extended.Component(
                horizontal=1, identifier=1, quantization=0, vertical=1
            )
            component.blocks_wide = 66
            component.blocks_high = 64
            component.coefficients = array('i', bytes(4 * 64 * 66 * 64))
            with mock.patch.object(
                jpeg_extended, 'READERS_BYTES_MINIMUM', new=minimum
            ):
                jpeg_extended._decode_scan(
                    deadline=time.monotonic() + 60, mcus_high=64, mcus_wide=64,
                    plan=[
                        (
                            component, tables[0], tables[16], 1, 1, ((0, 0),)
                        )
                    ], restart_interval=0, segments=(data[start:-2],)
                )
            return numpy.frombuffer(component.coefficients, dtype=numpy.intc)

        self.assert_same(read(minimum=1024), read(minimum=1 << 40))

    def test_blocks_of_a_scan_of_one_component_of_several(self):
        # Not interleaved: fewer blocks in a row than in the array.
        import numpy

        columns = 8 * 64 + 1
        data = make_sequential_jpeg(
            blocks=make_blocks(count=65 * 64), columns=columns, rows=512
        )
        samples, results = self.decode_both(data=data)
        self.assertEqual(results, [True])
        self.assertEqual(samples.shape, (512, columns, 1))
        self.assertEqual(numpy.asarray(samples).dtype, numpy.uint16)


def make_dicom(
    frames=(JPEG_12_BITS,), photometric='MONOCHROME2', rows=16, columns=24,
    samples=1, signed=0, bits=12, transfer_syntax=None
):
    from pydicom.dataset import Dataset, FileMetaDataset
    from pydicom.encaps import encapsulate
    from pydicom.uid import (
        JPEGExtended12Bit, SecondaryCaptureImageStorage, generate_uid
    )

    meta = FileMetaDataset()
    meta.MediaStorageSOPClassUID = SecondaryCaptureImageStorage
    meta.MediaStorageSOPInstanceUID = generate_uid()
    meta.TransferSyntaxUID = transfer_syntax or JPEGExtended12Bit
    dataset = Dataset()
    dataset.file_meta = meta
    dataset.SOPClassUID = SecondaryCaptureImageStorage
    dataset.SOPInstanceUID = meta.MediaStorageSOPInstanceUID
    dataset.Modality = 'OT'
    dataset.Rows, dataset.Columns = rows, columns
    dataset.SamplesPerPixel = samples
    if samples > 1:
        dataset.PlanarConfiguration = 0
    dataset.PhotometricInterpretation = photometric
    dataset.BitsAllocated = 16 if bits > 8 else 8
    dataset.BitsStored, dataset.HighBit = bits, bits - 1
    dataset.PixelRepresentation = signed
    dataset.NumberOfFrames = len(frames)
    dataset.PixelData = encapsulate(list(frames))
    dataset['PixelData'].is_undefined_length = True
    dataset['PixelData'].VR = 'OB'
    buffer = io.BytesIO()
    dataset.save_as(buffer, enforce_file_format=True)
    buffer.seek(0)
    return buffer


@unittest.skipUnless(PYDICOM, 'pydicom not installed')
class DICOMTestCase(SimpleTestCase):
    def test_sample_file_of_pydicom(self):
        from pydicom.data import get_testdata_file
        from pydicom.pixels import pixel_array

        path = get_testdata_file('JPGExtended.dcm', download=False)
        if not path:
            self.skipTest('sample file of pydicom not installed')

        array = pixel_array(
            path, decoding_plugin=jpeg_extended.register_decoder()
        )
        self.assertEqual(sha256(array), SAMPLE_FILE_SHA256)

        with open(path, mode='rb') as file_object:
            self.assertEqual(
                dicom.get_dicom_page_count(file_object=file_object), 1
            )
            image = dicom.render_dicom_page(
                file_object=file_object, page_number=0
            )
        # The image itself, not a page of attributes with the reason.
        self.assertEqual(image.size, (256, 1024))

    def test_no_decoder_refusal_logged(self):
        # Pillow is not asked for the samples of 12 bits.
        with self.assertNoLogs('pydicom', level='ERROR'):
            dicom.render_dicom_page(file_object=make_dicom(), page_number=0)

    def test_values(self):
        from pydicom.pixels import pixel_array

        array = pixel_array(
            make_dicom(), decoding_plugin=jpeg_extended.register_decoder(),
            index=0
        )
        self.assertEqual(sha256(array), JPEG_12_BITS_SHA256)

    def test_each_frame_on_its_page(self):
        from pydicom.pixels import pixel_array

        file_object = make_dicom(frames=(JPEG_12_BITS, JPEG_12_BITS_INVERTED))
        self.assertEqual(dicom.get_dicom_page_count(file_object=file_object), 2)
        first = dicom.render_dicom_page(file_object=file_object, page_number=0)
        second = dicom.render_dicom_page(file_object=file_object, page_number=1)
        self.assertEqual(first.size, (528, 352))
        self.assertEqual(second.size, (528, 352))
        self.assertLess(first.getpixel((0, 0)), second.getpixel((0, 0)))

        for index, expected in enumerate(
            (JPEG_12_BITS_SHA256, JPEG_12_BITS_INVERTED_SHA256)
        ):
            file_object.seek(0)
            self.assertEqual(
                sha256(
                    pixel_array(
                        file_object, index=index,
                        decoding_plugin=jpeg_extended.register_decoder()
                    )
                ), expected
            )

    def test_8_bits_samples(self):
        from pydicom.pixels import pixel_array

        data = make_jpeg()
        array = pixel_array(
            make_dicom(
                bits=8, columns=53, frames=(data,), rows=37
            ), decoding_plugin=jpeg_extended.register_decoder(), index=0
        )
        self.assertEqual(array.dtype, 'uint8')
        self.assertEqual(array.tobytes(), Image.open(io.BytesIO(data)).tobytes())

    def test_signed_samples(self):
        from pydicom.pixels import pixel_array

        array = pixel_array(
            make_dicom(signed=1),
            decoding_plugin=jpeg_extended.register_decoder(), index=0
        )
        self.assertEqual((array.min(), array.max()), (-2048, 2047))

    def test_color_values(self):
        from pydicom.pixels import pixel_array

        array = pixel_array(
            make_dicom(
                frames=(JPEG_12_BITS_COLOR,), photometric='YBR_FULL', samples=3
            ), decoding_plugin=jpeg_extended.register_decoder(), index=0
        )
        self.assertEqual(sha256(array), JPEG_12_BITS_COLOR_RGB_SHA256)

    def test_color_samples_kept_when_not_ybr(self):
        from pydicom.pixels import pixel_array

        # Without its JFIF marker: pydicom reads the file as YCbCr with it.
        size = int.from_bytes(JPEG_12_BITS_COLOR[4:6], 'big')
        data = JPEG_12_BITS_COLOR[:2] + JPEG_12_BITS_COLOR[4 + size:]
        array = pixel_array(
            make_dicom(frames=(data,), photometric='RGB', samples=3),
            decoding_plugin=jpeg_extended.register_decoder(), index=0
        )
        self.assertEqual(sha256(array), JPEG_12_BITS_COLOR_SHA256)

    def test_color_pages(self):
        for photometric, data in (
            ('YBR_FULL', JPEG_12_BITS_COLOR),
            ('YBR_FULL_422', JPEG_12_BITS_SUBSAMPLED)
        ):
            with self.subTest(photometric=photometric):
                image = dicom.render_dicom_page(
                    file_object=make_dicom(
                        frames=(data,), photometric=photometric, samples=3
                    ), page_number=0
                )
                # The image itself, not a page of attributes with the reason:
                # the ramp goes from blue to red, the third channel inverted.
                self.assertEqual(image.size, (528, 352))
                red, green, blue = image.getpixel((0, 0))
                self.assertLess(red, 30)
                self.assertGreater(blue, 225)
                red, green, blue = image.getpixel((527, 351))
                self.assertGreater(red, 225)
                self.assertLess(blue, 30)

    def test_size_other_than_the_declared_one(self):
        image = dicom.render_dicom_page(
            file_object=make_dicom(rows=20), page_number=0
        )
        # A page of attributes with the reason.
        self.assertEqual(image.size, (dicom.PAGE_WIDTH, dicom.PAGE_HEIGHT))

    def test_damaged_frame_gives_a_page_with_the_reason(self):
        image = dicom.render_dicom_page(
            file_object=make_dicom(frames=(b'not a JPEG file!',)), page_number=0
        )
        self.assertEqual(image.size, (dicom.PAGE_WIDTH, dicom.PAGE_HEIGHT))
