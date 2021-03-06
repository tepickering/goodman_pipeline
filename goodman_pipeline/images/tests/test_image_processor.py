from __future__ import absolute_import

from astropy.io import fits
from unittest import TestCase, skip

from ccdproc import CCDData
from ...core import NightDataContainer
from ..image_processor import ImageProcessor
from ..goodman_ccd import get_args

import numpy as np


class ImageProcessorTest(TestCase):

    def setUp(self):
        arguments = ['--saturation', '1']
        args = get_args(arguments=arguments)
        data_container = NightDataContainer(path='/fake',
                                            instrument='Red',
                                            technique='Spectroscopy')
        self.image_processor = ImageProcessor(args=args,
                                              data_container=data_container)

        self.ccd = CCDData(data=np.ones((100, 100)),
                           meta=fits.Header(),
                           unit='adu')
        self.ccd.header.set('INSTCONF', value='Red')
        self.ccd.header.set('GAIN', value=1.48)
        self.ccd.header.set('RDNOISE', value=3.89)

        self.half_full_well = 69257

    def test_file_is_saturated(self):
        self.ccd.data[:10, :10] = self.half_full_well + 1
        self.assertTrue(self.image_processor._is_file_saturated(ccd=self.ccd))

    def test_file_is_not_saturated(self):
        self.ccd.data[:10, :10] = self.half_full_well + 1
        self.ccd.data[0, 0] = 1
        self.assertFalse(self.image_processor._is_file_saturated(ccd=self.ccd))



def test_define_trim_section():
    pass


def test_get_overscan_region():
    pass


def test_create_master_bias():
    pass


def test_create_master_flats():
    pass


def test_name_master_flats():
    pass


def test_process_spectroscopy_science():
    pass


def test_processing_imaging_science():
    pass


def test_combine_data():
    pass
