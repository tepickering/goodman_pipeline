from __future__ import absolute_import

from unittest import TestCase, skip
from ccdproc import CCDData
from astropy.io import fits
import numpy as np

# import all classes in core.py
from ..core import (NightDataContainer,
                    NoMatchFound,
                    NotEnoughLinesDetected,
                    NoTargetException,
                    SpectroscopicMode)

from ..core import models

# import of functions in core.py
from ..core import (add_wcs_keys,
                    call_cosmic_rejection,
                    classify_spectroscopic_data,
                    convert_time,
                    dcr_cosmicray_rejection,
                    extraction,
                    extract_fractional_pixel,
                    extract_optimal,
                    fractional_sum,
                    get_best_flat,
                    get_central_wavelength,
                    get_slit_trim_section,
                    get_twilight_time,
                    identify_targets,
                    image_overscan,
                    image_trim,
                    lacosmic_cosmicray_rejection,
                    normalize_master_flat,
                    ra_dec_to_deg,
                    read_fits,
                    search_comp_group,
                    trace,
                    trace_targets,
                    write_fits)

# class ExceptionHandling(TestCase):
#
#     def test_critical_error(self):
#         self.assertRaises(CriticalError)
#
#
#     def test_night_data_container(self):
#         pass
#
#
#     def test_no_match_found(self):
#         pass
#
#
#     def test_not_enough_lines_detected(self):
#         pass
#
#
#     def test_no_target_exception(self):
#         pass


def test_spectroscopic_mode():
    pass


class WcsKeywords(TestCase):

    def test_add_wcs_keys(self):
        wcs_keys = ['BANDID1',
                    'APNUM1',
                    'WCSDIM',
                    'CTYPE1',
                    'CRVAL1',
                    'CRPIX1',
                    'CDELT1',
                    'CD1_1',
                    'LTM1_1',
                    'WAT0_001',
                    'WAT1_001',
                    'DC-FLAG',
                    'DCLOG1']

        test_ccd = CCDData(data=np.ones((100, 100)),
                           meta=fits.Header(),
                           unit='adu')

        test_ccd = add_wcs_keys(ccd=test_ccd)
        for key in wcs_keys:
            self.assertIn(key, test_ccd.header)


def test_call_cosmic_rejection():
    pass


def test_classify_spectroscopic_data():
    pass


def test_convert_time():
    pass


def test_dcr_cosmicray_rejection():
    pass


def test_extract():
    pass


def test_extract_optimal():
    pass


class FractionalExtraction(TestCase):

    def test_fractional_extraction(self):

        # Create fake image
        fake_image = CCDData(data=np.ones((100, 100)),
                             meta=fits.Header(),
                             unit='adu')

        fake_image.header['OBSTYPE'] = 'COMP'
        fake_image.header['GSP_FNAM'] = 'fake-image.fits'
        print(fake_image.header)

        # Create model aligned with pixels - represents the trace
        model = models.Linear1D(slope=0, intercept=50.3)

        # Calculate the STDDEV
        stddev = 8.4

        # Calculate how many STDDEV will be extracted - N_STDDEV
        n_stddev = 2

        # Calculate how far the background is from the the center.
        distance = 1

        # Perform extraction
        extracted_array, background = extract_fractional_pixel(ccd=fake_image,
                                                   target_trace=model,
                                                   target_stddev=stddev,
                                                   extraction_width=n_stddev,
                                                   background_spacing=distance)
        # assert isinstance(fake_image, CCDData)
        assert isinstance(extracted_array, CCDData)

        reference = np.ones(100) * stddev * n_stddev
        np.testing.assert_array_almost_equal(extracted_array, reference)

    def test_fractional_sum(self):

        fake_image = np.ones((100, 100))
        low_limit = 50 + np.random.random()
        high_limit = 60 + np.random.random()

        sum = fractional_sum(fake_image, 50, low_limit, high_limit)
        self.assertEqual(sum, high_limit - low_limit)


# class BackgroundValue(TestCase):


def test_get_best_flat():
    pass


def test_get_central_wavelength():
    pass


class SlitTrim(TestCase):

    def test_get_slit_trim_section(self):

        # Create fake image
        fake_image = CCDData(data=np.ones((100, 100)),
                             meta=fits.Header(),
                             unit='adu')

        # define
        slit_low_limit = 5
        slit_high_limit = 95

        reference_slit_trim = '[1:100,{:d}:{:d}]'.format(slit_low_limit + 10,
                                                         slit_high_limit - 10)

        # make a flat-like structure
        fake_image.data[slit_low_limit:slit_high_limit, :] = 100
        slit_trim = get_slit_trim_section(master_flat=fake_image)
        # print(fake_image.data[:,5])
        # print(slit_trim)
        self.assertEqual(slit_trim, reference_slit_trim)


def test_get_twilight_time():
    pass


def test_identify_targets():
    pass


def test_image_overscan():
    pass


def test_image_trim():
    pass


def test_lacosmic_cosmicray_rejection():
    pass


def test_normalize_master_flat():
    pass


# def test_print_default_args():
#     pass
#
#
# def test_print_progress():
#     pass
#
#
# def test_print_spacers():
#     pass


def test_ra_dec_to_deg():
    pass


def test_read_fits():
    pass


def test_search_comp_group():
    pass


def test_spectroscopic_extraction():
    pass


def test_trace():
    pass


def test_trace_targets():
    pass


def test_write_fits():
    pass
