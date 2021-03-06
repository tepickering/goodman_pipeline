from __future__ import absolute_import

from unittest import TestCase, skip
from ccdproc import CCDData
from astropy.io import fits
from astropy.modeling import Model
from astropy.modeling import (models,
                              fitting)
import astropy.units as u
import collections
import numpy as np
import os
import pandas
import re
import logging

logging.disable(logging.CRITICAL)

# import all classes in core.py
from ..core import (GenerateDcrParFile,
                    NightDataContainer,
                    NoMatchFound,
                    NotEnoughLinesDetected,
                    NoTargetException,
                    ReferenceData,
                    SaturationValues,
                    SpectroscopicMode)


# import of functions in core.py
from ..core import (astroscrappy_lacosmic,
                    add_wcs_keys,
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
                    interpolate,
                    normalize_master_flat,
                    ra_dec_to_deg,
                    read_fits,
                    record_trace_information,
                    save_extracted,
                    search_comp_group,
                    setup_logging,
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


def test_search_comp_group():
    pass


def test_lacosmic_cosmicray_rejection():
    pass


def test_classify_spectroscopic_data():
    pass


class InterpolationTest(TestCase):

    def test_interpolate(self):
        initial_array = np.sin(np.arange(0, 3 * np.pi))
        initial_length = len(initial_array)

        new_x_axis, new_array = interpolate(spectrum=initial_array,
                                            interpolation_size=100)

        self.assertEqual(len(new_x_axis), len(new_array))
        self.assertEqual(len(new_array), initial_length * 100)


class GenerateDcrFile(TestCase):

    def setUp(self):
        self.create = GenerateDcrParFile()
        self.ccd = CCDData(data=np.ones((100, 100)),
                           meta=fits.Header(),
                           unit='adu')
        self.ccd.header.set('INSTCONF', value='Red')
        self.ccd.header.set('CCDSUM', value='1 1')

    def test_generate_dcr_par_file(self):
        serial, parallel = self.ccd.header['CCDSUM'].split()
        instrument = self.ccd.header['INSTCONF']

        self.assertEqual(serial, '1')
        self.assertEqual(instrument, 'Red')
        self.assertEqual(self.create._file_name, 'dcr.par')
        self.assertIsInstance(self.create._df, pandas.DataFrame)

        self.assertFalse(os.path.isfile(self.create._file_name))
        self.create()
        self.assertTrue(os.path.isfile(self.create._file_name))

        self.assertRaises(AssertionError, self.create, 'Green')

    def tearDown(self):
        if os.path.isfile(self.create._file_name):
            os.remove(self.create._file_name)


class MasterFlatTest(TestCase):

    def setUp(self):
        # create a master flat
        self.master_flat = CCDData(data=np.ones((100, 100)),
                                   meta=fits.Header(),
                                   unit='adu')
        self.master_flat.header.set('GRATING', value='RALC_1200-BLUE')
        self.master_flat.header.set('SLIT', value='0.84" long slit')
        self.master_flat.header.set('FILTER2', value='<NO FILTER>')
        self.master_flat.header.set('WAVMODE', value='1200 m2')
        self.master_flat_name = 'master_flat_1200m2.fits'
        # expected master flat to be retrieved by get_best_flat
        self.reference_flat_name = 'master_flat_1200m2_0.84_dome.fits'
        # location of sample flats
        self.flat_path = 'goodman_pipeline/data/test_data/master_flat'
        slit = re.sub('[A-Za-z" ]',
                      '',
                      self.master_flat.header['SLIT'])
        self.flat_name_base = re.sub('.fits',
                                     '_' + slit + '*.fits',
                                     self.master_flat_name)

        # save a master flat with some random structure.

        self.master_flat_name_norm = 'flat_to_normalize.fits'
        # add a bias level
        self.master_flat.data += 300.
        # add noise
        self.master_flat.data += np.random.random_sample(
            self.master_flat.data.shape)

        self.master_flat.write(os.path.join(self.flat_path,
                                            self.master_flat_name_norm),
                               overwrite=False)

    def tearDown(self):
        full_path = os.path.join(self.flat_path,
                                 self.master_flat_name_norm)

        self.assertTrue(os.path.isfile(full_path))
        if os.path.isfile(full_path):
            os.unlink(full_path)
        self.assertFalse(os.path.isfile(full_path))

        # remove normalized flat
        norm_flat = re.sub('flat_to_', 'norm_flat_to_', full_path)
        if os.path.isfile(norm_flat):
            os.unlink(norm_flat)
        self.assertFalse(os.path.isfile(norm_flat))

    def test_get_best_flat(self):
        # print(self.flat_name_base)

        master_flat, master_flat_name = get_best_flat(
            flat_name=self.flat_name_base,
            path=self.flat_path)
        self.assertIsInstance(master_flat, CCDData)
        self.assertEqual(os.path.basename(master_flat_name),
                         self.reference_flat_name)

    def test_get_best_flat_fail(self):
        # Introduce an error that will never produce a result.
        wrong_flat_name = re.sub('1200m2', '1300m2', self.flat_name_base)
        master_flat, master_flat_name = get_best_flat(
            flat_name=wrong_flat_name,
            path=self.flat_path)
        self.assertIsNone(master_flat)
        self.assertIsNone(master_flat_name)

    def test_normalize_master_flat(self):
        methods = ['mean', 'simple', 'full']
        for method in methods:
            self.assertNotAlmostEqual(self.master_flat.data.mean(), 1.)
            normalized_flat, normalized_flat_name = normalize_master_flat(
                master=self.master_flat,
                name=os.path.join(self.flat_path,
                                  self.master_flat_name_norm),
                method=method)

            self.assertAlmostEqual(normalized_flat.data.mean(), 1.,
                                   delta=0.001)
            self.assertEqual(normalized_flat.header['GSP_NORM'], method)
            self.assertIn('norm_', normalized_flat_name)


class CentralWavelength(TestCase):

    def setUp(self):
        # 400m2
        self.grating = '400'
        self.grating_angle = 7.5
        self.camera_angle = 16.1
        self.reference_central_wavelength = 7001.54 * u.angstrom

    def test_get_central_wavelength(self):
        central_wavelength = get_central_wavelength(grating=self.grating,
                                                    grt_ang=self.grating_angle,
                                                    cam_ang=self.camera_angle)
        self.assertAlmostEqual(central_wavelength.value,
                               self.reference_central_wavelength.value,
                               places=2)


class AddWCSKeywordsTest(TestCase):

    def setUp(self):
        self.test_ccd = CCDData(data=np.ones((100, 100)),
                                meta=fits.Header(),
                                unit='adu')

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



        self.test_ccd = add_wcs_keys(ccd=self.test_ccd)
        for key in wcs_keys:
            self.assertIn(key, self.test_ccd.header)

    @skip
    def test_add_wcs_keys_error(self):
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


class CosmicRayRejectionTest(TestCase):

    def setUp(self):
        self.ccd = CCDData(data=np.ones((100, 100)),
                           meta=fits.Header(),
                           unit='adu')
        self.file_name = 'cr_test.fits'

        self.ccd.header.set('CCDSUM', value='1 1')
        self.ccd.header.set('OBSTYPE', value='OBJECT')
        self.ccd.header.set('INSTCONF', value='Red')
        self.ccd.header.set('GSP_FNAM', value=self.file_name)
        self.ccd.header.set('GSP_COSM', value='none')

        self.red_path = os.getcwd()
        self.out_prefix = 'prefix'

    @skip
    def test_dcr_cosmicray_rejection(self):
        pass

    def test_call_cosmic_rejection_default_1x1(self):
        prefix = 'new_'
        initial_value = self.ccd.data[50, 50]
        self.ccd.data[50, 50] = 50000

        ccd, out_prefix = call_cosmic_rejection(ccd=self.ccd,
                                                image_name=self.file_name,
                                                out_prefix=self.out_prefix,
                                                red_path=self.red_path,
                                                dcr_par=os.getcwd(),
                                                keep_files=True,
                                                prefix=prefix,
                                                method='default',
                                                save=True)
        self.assertAlmostEqual(initial_value, ccd.data[50, 50])
        self.assertEqual(out_prefix, prefix + self.out_prefix)
        self.assertEqual(ccd.header['GSP_FNAM'],
                         prefix + self.out_prefix + self.file_name)
        self.assertEqual(ccd.header['GSP_COSM'], 'DCR')

        self.assertTrue(os.path.isfile('dcr.par'))
        self.assertTrue(os.path.isfile('new_prefixcr_test.fits'))

    def test_call_cosmic_rejection_default_2x2(self):
        self.ccd.header.set('CCDSUM', value='2 2')
        prefix = 'new_'
        initial_value = self.ccd.data[50, 50]
        self.ccd.data[50, 50] = 50000

        ccd, out_prefix = call_cosmic_rejection(ccd=self.ccd,
                                                image_name=self.file_name,
                                                out_prefix=self.out_prefix,
                                                red_path=self.red_path,
                                                dcr_par=os.getcwd(),
                                                keep_files=True,
                                                prefix=prefix,
                                                method='default',
                                                save=True)
        self.assertAlmostEqual(initial_value, ccd.data[50, 50])
        self.assertEqual(out_prefix, prefix + self.out_prefix)
        self.assertEqual(ccd.header['GSP_FNAM'],
                         prefix + self.out_prefix + self.file_name)
        self.assertEqual(ccd.header['GSP_COSM'], 'LACosmic')
        self.assertTrue(os.path.isfile('new_prefixcr_test.fits'))

    def test_call_cosmic_rejection_default_3x3(self):
        self.ccd.header.set('CCDSUM', value='3 3')
        prefix = 'new_'
        initial_value = self.ccd.data[50, 50]
        self.ccd.data[50, 50] = 50000

        ccd, out_prefix = call_cosmic_rejection(ccd=self.ccd,
                                                image_name=self.file_name,
                                                out_prefix=self.out_prefix,
                                                red_path=self.red_path,
                                                dcr_par=os.getcwd(),
                                                keep_files=True,
                                                prefix=prefix,
                                                method='default',
                                                save=True)
        self.assertAlmostEqual(initial_value, ccd.data[50, 50])
        self.assertEqual(out_prefix, prefix + self.out_prefix)
        self.assertEqual(ccd.header['GSP_FNAM'],
                         prefix + self.out_prefix + self.file_name)
        self.assertEqual(ccd.header['GSP_COSM'], 'LACosmic')

        self.assertTrue(os.path.isfile('new_prefixcr_test.fits'))

    def test_call_cosmic_rejection_none(self):
        prefix = 'new_'
        ccd, out_prefix = call_cosmic_rejection(ccd=self.ccd,
                                                image_name=self.file_name,
                                                out_prefix=self.out_prefix,
                                                red_path=self.red_path,
                                                dcr_par=os.getcwd(),
                                                keep_files=True,
                                                prefix=prefix,
                                                method='none',
                                                save=True)
        self.assertEqual(out_prefix, self.out_prefix)
        self.assertEqual(ccd.header['GSP_FNAM'],
                         self.out_prefix + self.file_name)
        self.assertEqual(ccd.header['GSP_COSM'], 'none')
        self.assertTrue(os.path.isfile('prefixcr_test.fits'))

    def test_call_cosmic_rejection_comp_lamp(self):
        self.ccd.header.set('OBSTYPE', value='COMP')
        prefix = 'new_'
        ccd, out_prefix = call_cosmic_rejection(ccd=self.ccd,
                                                image_name=self.file_name,
                                                out_prefix=self.out_prefix,
                                                red_path=self.red_path,
                                                dcr_par=os.getcwd(),
                                                keep_files=True,
                                                prefix=prefix,
                                                method='lacosmic',
                                                save=True)
        self.assertEqual(out_prefix, prefix + self.out_prefix)
        self.assertEqual(ccd.header['GSP_FNAM'],
                         prefix + self.out_prefix + self.file_name)
        self.assertEqual(ccd.header['GSP_COSM'], 'none')

    def test_call_cosmic_rejection_not_implemented_error(self):
        prefix = 'new_'
        self.assertRaises(NotImplementedError,
                          call_cosmic_rejection,
                          self.ccd,
                          self.file_name,
                          self.out_prefix,
                          self.red_path,
                          os.getcwd(),
                          True,
                          prefix,
                          'not_implemented_method',
                          True)

    def tearDown(self):
        files_to_delete = ['dcr.par',
                           'goodman_log.txt',
                           'cosmic_test.fits',
                           'new_prefixcr_test.fits',
                           'prefixcr_test.fits',
                           'crmask_cr_test.fits']

        for _file in files_to_delete:
            if os.path.isfile(_file):
                os.unlink(_file)


class TimeConversionTest(TestCase):

    def setUp(self):
        self.test_time_str = '2018-01-17T12:05:44.250'
        self.test_time_sec = 1516190744.0

    def test_convert_time(self):
        self.assertEqual(convert_time(self.test_time_str), self.test_time_sec)

    def test_get_twilight_time(self):
        expected_evening_twilight = '2018-01-17T01:21:26.113'
        expected_morning_twilight = '2018-01-17T08:24:38.919'
        expected_sun_set_time = '2018-01-17T23:43:46.782'
        expected_sun_rise_time = '2018-01-17T10:02:04.508'
        evening_twilight, morning_twilight, sun_set, sun_rise\
            = get_twilight_time([self.test_time_str])

        self.assertEqual(evening_twilight, expected_evening_twilight)
        self.assertEqual(morning_twilight, expected_morning_twilight)
        self.assertEqual(sun_set, expected_sun_set_time)
        self.assertEqual(sun_rise, expected_sun_rise_time)


class ExtractionTest(TestCase):

    def setUp(self):
        self.fake_image = CCDData(data=np.ones((100, 100)),
                                  meta=fits.Header(),
                                  unit='adu')
        self.fake_image.header.set('NAXIS', value=2)
        self.fake_image.header.set('NAXIS1', value=100)
        self.fake_image.header.set('NAXIS2', value=100)
        self.fake_image.header.set('OBSTYPE', value='COMP')
        self.fake_image.header['GSP_FNAM'] = 'fake-image.fits'

        # Create model aligned with pixels - represents the trace
        self.target_trace = models.Linear1D(slope=0, intercept=50.3)

        # Calculate the STDDEV
        self.stddev = 8.4

        # Calculate how many STDDEV will be extracted - N_STDDEV
        self.n_stddev = 2

        # Calculate how far the background is from the the center.
        self.distance = 1

        self.target_profile = models.Gaussian1D(amplitude=1,
                                                mean=50.3,
                                                stddev=self.stddev)

        self.reference_result = np.ones(100) * self.stddev * self.n_stddev

    def test_fractional_extraction(self):
        # Perform extraction
        extracted_array, background, info = extract_fractional_pixel(
            ccd=self.fake_image,
            target_trace=self.target_trace,
            target_stddev=self.stddev,
            extraction_width=self.n_stddev,
            background_spacing=self.distance)
        # assert isinstance(fake_image, CCDData)
        self.assertIsInstance(extracted_array, CCDData)

        np.testing.assert_array_almost_equal(extracted_array,
                                             self.reference_result)

    def test_fractional_extraction_obstype_object(self):
        self.fake_image.header.set('OBSTYPE', value='OBJECT')
        # Perform extraction
        extracted_array, background, info = extract_fractional_pixel(
            ccd=self.fake_image,
            target_trace=self.target_trace,
            target_stddev=self.stddev,
            extraction_width=self.n_stddev,
            background_spacing=self.distance)
        # assert isinstance(fake_image, CCDData)
        self.assertIsInstance(extracted_array, CCDData)

        np.testing.assert_array_almost_equal(extracted_array,
                                             np.zeros(extracted_array.shape))

    def test_fractional_sum(self):

        fake_image = np.ones((100, 100))
        low_limit = 50 + np.random.random()
        high_limit = 60 + np.random.random()

        frac_sum = fractional_sum(fake_image, 50, low_limit, high_limit)
        self.assertEqual(frac_sum, high_limit - low_limit)

    def test_extract_optimal(self):
        self.assertRaises(NotImplementedError, extract_optimal)

    def test_extract__optimal_not_implemented(self):
        self.assertRaises(NotImplementedError,
                          extraction,
                          self.fake_image,
                          self.target_trace,
                          self.target_profile,
                          'optimal')

    def test_extraction(self):
        extracted = extraction(ccd=self.fake_image,
                               target_trace=self.target_trace,
                               spatial_profile=self.target_profile,
                               extraction_name='fractional')
        self.assertIsInstance(extracted, CCDData)
        np.testing.assert_array_almost_equal(extracted, self.reference_result)

    def test_extraction_exception(self):
        self.assertRaises(NotImplementedError, extraction, ccd=self.fake_image,
                          target_trace=self.target_trace,
                          spatial_profile=self.target_profile,
                          extraction_name='optimal')


class SlitTrimTest(TestCase):
    # TODO (simon): discuss with Bruno

    def setUp(self):
        # Create fake image
        self.fake_image = CCDData(data=np.ones((100, 100)),
                                  meta=fits.Header(),
                                  unit='adu')

        # define
        self.slit_low_limit = 5
        self.slit_high_limit = 95

        self.reference_slit_trim = '[1:100,{:d}:{:d}]'.format(
            self.slit_low_limit + 10 + 1,
            self.slit_high_limit - 10)

        # make a flat-like structure
        self.fake_image.data[self.slit_low_limit:self.slit_high_limit, :] = 100

    def test_get_slit_trim_section(self):

        slit_trim = get_slit_trim_section(master_flat=self.fake_image)
        # print(fake_image.data[:,5])
        # print(slit_trim)
        self.assertEqual(slit_trim, self.reference_slit_trim)

    def test_image_trim_slit(self):
        # # define
        # slit_low_limit = 5
        # slit_high_limit = 95
        #
        # slit_trim = '[1:100,{:d}:{:d}]'.format(slit_low_limit + 10 + 1,
        #                                        slit_high_limit - 10)
        self.fake_image = image_trim(ccd=self.fake_image,
                                     trim_section=self.reference_slit_trim,
                                     trim_type='slit')
        self.assertIsInstance(self.fake_image, CCDData)
        reference_size = (self.slit_high_limit - 10) - \
                         (self.slit_low_limit + 10)
        self.assertEqual(self.fake_image.data.shape, (reference_size, 100))

        self.assertEqual(self.fake_image.header['GSP_SLIT'],
                         self.reference_slit_trim)


class RaDecConversion(TestCase):

    def setUp(self):
        self.ra = '19:09:55.026'
        self.dec = '-68:18:01.901'
        self.reference_ra = 287.479275
        self.reference_dec = -68.3005281

    def test_ra_dec_to_deg(self):
        radeg, decdeg = ra_dec_to_deg(right_ascension=self.ra,
                                      declination=self.dec)
        self.assertAlmostEqual(radeg, self.reference_ra)
        self.assertAlmostEqual(decdeg, self.reference_dec)


class ReferenceDataTest(TestCase):

    def setUp(self):
        self.rd = ReferenceData(
            reference_dir=os.path.join(os.getcwd(),
                                       'goodman_pipeline/data/ref_comp'))
        self.ccd = CCDData(data=np.ones((800, 2000)),
                           meta=fits.Header(),
                           unit='adu')

        self.columns = ['object', 'grating', 'grt_targ', 'cam_targ']

        self.data_exist = [['HgArNe', 'SYZY_400', 7.5, 16.1],
                           ['HgAr', 'SYZY_400', 7.5, 16.1]]

        self.data_does_not_exist = [['HgArNe', 'SYZY_800', 7.5, 16.1],
                                    ['HgAr', 'SYZY_800', 7.5, 16.1]]

    def test_get_reference_lamp_exist(self):
        self.ccd.header.set('OBJECT', value='HgArNe')
        self.ccd.header.set('WAVMODE', value='400 m2')

        ref_lamp = self.rd.get_reference_lamp(header=self.ccd.header)

        self.assertIsInstance(ref_lamp, CCDData)
        self.assertEqual(ref_lamp.header['OBJECT'], self.ccd.header['OBJECT'])
        self.assertEqual(ref_lamp.header['WAVMODE'], self.ccd.header['WAVMODE'])

    def test_get_reference_lamp_does_not_exist(self):
        self.ccd.header.set('OBJECT', value='HgArCu')
        self.ccd.header.set('WAVMODE', value='400 m5')

        self.assertRaises(NotImplementedError,
                          self.rd.get_reference_lamp,
                          self.ccd.header)

    def test_lamp_exist(self):
        self.assertTrue(self.rd.lamp_exists(object_name='HgArNe',
                                            grating='SYZY_400',
                                            grt_targ=7.5,
                                            cam_targ=16.1))

        self.assertFalse(self.rd.lamp_exists(object_name='HgArCu',
                                             grating='SYZY_400',
                                             grt_targ=7.5,
                                             cam_targ=16.1))

    def test_check_comp_group__lamp_exists(self):
        comp_group = pandas.DataFrame(self.data_exist,
                                      columns=self.columns)

        new_group = self.rd.check_comp_group(comp_group=comp_group)

        self.assertIsInstance(new_group, pandas.DataFrame)
        self.assertFalse(comp_group.equals(new_group))
        self.assertEqual(len(new_group), 1)

    def test_check_comp_group__lamp_does_not_exist(self):
        comp_group = pandas.DataFrame(self.data_does_not_exist,
                                      columns=self.columns)

        new_group = self.rd.check_comp_group(comp_group=comp_group)

        self.assertIsInstance(new_group, pandas.DataFrame)
        self.assertTrue(comp_group.equals(new_group))


class RecordTraceInformationTest(TestCase):

    def setUp(self):
        self.ccd = CCDData(data=np.ones((800, 2000)),
                           meta=fits.Header(),
                           unit='adu')

        self.all_keywords = ['GSP_TMOD',
                             'GSP_TORD',
                             'GSP_TC00',
                             'GSP_TC01',
                             'GSP_TC02',
                             'GSP_TERR']

        self.trace_info = collections.OrderedDict()

        self.trace_info['GSP_TMOD'] = ['Polinomial1D',
                                       'Model name used to fit trace']

        self.trace_info['GSP_TORD'] = [2, 'Degree of the model used to fit '
                                          'target trace']

        self.trace_info['GSP_TC00'] = [500, 'Parameter c0']
        self.trace_info['GSP_TC01'] = [1, 'Parameter c1']
        self.trace_info['GSP_TC02'] = [2, 'Parameter c2']
        self.trace_info['GSP_TERR'] = [0.5, 'RMS error of target trace']

    def test_record_trace_information(self):
        ccd = record_trace_information(ccd=self.ccd, trace_info=self.trace_info)
        new_keys = [key for key in ccd.header.keys()]

        self.assertTrue(all([key in new_keys for key in self.all_keywords]))
        self.assertEqual(ccd.header['GSP_TMOD'], 'Polinomial1D')
        self.assertEqual(ccd.header['GSP_TORD'], 2)


class SpectroscopicModeTest(TestCase):

    def setUp(self):
        self.sm = SpectroscopicMode()
        self.ccd = CCDData(data=np.ones((800, 2000)),
                           meta=fits.Header(),
                           unit='adu')
        self.ccd.header.set('GRATING', value='SYZY_400')
        self.ccd.header.set('CAM_TARG', value='16.1')
        self.ccd.header.set('GRT_TARG', value='7.5')
        self.ccd.header.set('FILTER2', value='GG455')

    def test__call__(self):
        self.assertRaises(SyntaxError, self.sm)

        mode_m2_header = self.sm(header=self.ccd.header)

        self.assertEqual(mode_m2_header, 'm2')

        mode_m2_keywords = self.sm(grating=self.ccd.header['GRATING'],
                                   camera_targ=self.ccd.header['CAM_TARG'],
                                   grating_targ=self.ccd.header['GRT_TARG'],
                                   blocking_filter=self.ccd.header['FILTER2'])

        self.assertEqual(mode_m2_keywords, 'm2')

    def test_get_mode(self):
        mode_m2 = self.sm.get_mode(grating='400',
                                   camera_targ='16.1',
                                   grating_targ='7.5',
                                   blocking_filter='GG455')
        self.assertEqual(mode_m2, 'm2')

        mode_custom_400 = self.sm.get_mode(grating='400',
                                           camera_targ='16.1',
                                           grating_targ='6.6',
                                           blocking_filter='GG455')

        self.assertEqual(mode_custom_400, 'Custom_7000nm')

        mode_custom_2100 = self.sm.get_mode(grating='2100',
                                            camera_targ='16.1',
                                            grating_targ='7.5',
                                            blocking_filter='GG455')
        self.assertEqual(mode_custom_2100, 'Custom_1334nm')

    def test_get_cam_grt_targ_angle(self):

        cam_targ, grt_targ = self.sm.get_cam_grt_targ_angle(1800, 'm10')
        self.assertIsNone(cam_targ)
        self.assertIsNone(grt_targ)

        cam_targ, grt_targ = self.sm.get_cam_grt_targ_angle(930, 'm5')
        self.assertEqual(cam_targ, '39.4')
        self.assertEqual(grt_targ, '19.7')

        cam_targ, grt_targ = self.sm.get_cam_grt_targ_angle(930, 'm7')
        self.assertIsNone(cam_targ)
        self.assertIsNone(grt_targ)



class TargetsTest(TestCase):

    def setUp(self):
        self.ccd = CCDData(data=np.ones((800, 2000)),
                           meta=fits.Header(),
                           unit='adu')

        self.profile_1 = models.Gaussian1D(amplitude=200,
                                           mean=100,
                                           stddev=10).rename('Profile_1')
        self.profile_2 = models.Gaussian1D(amplitude=200,
                                           mean=600,
                                           stddev=10).rename('Profile_2')

        profile_sum = self.profile_1 + self.profile_2
        for i in range(self.ccd.data.shape[1]):
            self.ccd.data[:, i] *= profile_sum(range(self.ccd.data.shape[0]))

    def tearDown(self):
        del self.ccd
        del self.profile_1
        del self.profile_2

    def test_identify_targets(self):
        self.ccd.header.set('OBSTYPE',
                            value='OBJECT',
                            comment='Fake values')
        self.ccd.header.set('SLIT',
                            value='1.03" long slit',
                            comment='Fake slit')
        self.ccd.header.set('CCDSUM',
                            value='1 1',
                            comment='Fake values')
        targets = identify_targets(ccd=self.ccd, nfind=2, plots=False)
        self.assertEqual(len(targets), 2)
        for target in targets:
            self.assertIsInstance(target, Model)

    def test_trace(self):
        trace_model = models.Polynomial1D(degree=2)
        fitter = fitting.LevMarLSQFitter()
        test_trace, trace_rms = trace(ccd=self.ccd,
                                      model=self.profile_1,
                                      trace_model=trace_model,
                                      model_fitter=fitter,
                                      sampling_step=5)
        self.assertEqual(test_trace.c0.value, self.profile_1.mean.value)
        self.assertAlmostEqual(test_trace.c1.value, 0.)
        self.assertAlmostEqual(test_trace.c2.value, 0.)

    def test_trace_targets(self):
        targets = [self.profile_1, self.profile_2]
        all_traces = trace_targets(ccd=self.ccd,
                                   target_list=targets,
                                   sampling_step=5,
                                   pol_deg=2,
                                   nsigmas=2,
                                   plots=False)
        for new_trace, profile, trace_info in all_traces:
            self.assertEqual(new_trace.c0.value, profile.mean.value)
            self.assertAlmostEqual(new_trace.c1.value, 0)
            self.assertAlmostEqual(new_trace.c2.value, 0)


class FitsFileIOAndOps(TestCase):

    def setUp(self):
        self.fake_image = CCDData(data=np.ones((100, 100)),
                                  meta=fits.Header(),
                                  unit='adu')

        self.file_name = 'sample_file.fits'
        self.target_non_zero = 4
        self.current_directory = os.getcwd()
        self.full_path = os.path.join(self.current_directory, self.file_name)
        self.parent_file = 'parent_file.fits'

        self.fake_image.header.set('CCDSUM',
                                   value='1 1',
                                   comment='Fake values')

        self.fake_image.header.set('OBSTYPE',
                                   value='OBJECT',
                                   comment='Fake values')

        self.fake_image.header.set('GSP_FNAM',
                                   value=self.file_name,
                                   comment='Fake values')

        self.fake_image.header.set('GSP_PNAM',
                                   value=self.parent_file,
                                   comment='Fake values')

        self.fake_image.write(self.full_path, overwrite=False)

    def test_write_fits(self):
        self.assertTrue(os.path.isfile(self.full_path))
        os.remove(self.full_path)
        write_fits(ccd=self.fake_image,
                   full_path=self.full_path,
                   parent_file=self.parent_file,
                   overwrite=False)
        self.assertTrue(os.path.isfile(self.full_path))

    def test_read_fits(self):
        self.recovered_fake_image = read_fits(self.full_path)
        self.assertIsInstance(self.recovered_fake_image, CCDData)

    def test_image_overscan(self):
        data_value = 100.
        overscan_value = 0.1
        # alter overscan region to a lower number
        self.fake_image.data *= data_value
        self.fake_image.data[:, 0:5] = overscan_value

        overscan_region = '[1:6,:]'
        self.assertEqual(self.fake_image.data[:, 6:99].mean(), data_value)
        self.assertEqual(self.fake_image.data[:, 0:5].mean(), overscan_value)
        self.fake_image = image_overscan(ccd=self.fake_image,
                                         overscan_region=overscan_region)

        self.assertEqual(self.fake_image.data[:, 6:99].mean(),
                         data_value - overscan_value)
        self.assertEqual(self.fake_image.header['GSP_OVER'], overscan_region)

    def test_image_overscan_none(self):
        new_fake_image = image_overscan(ccd=self.fake_image,
                                        overscan_region=None)
        self.assertEqual(new_fake_image, self.fake_image)

    def test_image_trim(self):
        self.assertEqual(self.fake_image.data.shape, (100, 100))
        trim_section = '[1:50,:]'
        self.fake_image = image_trim(ccd=self.fake_image,
                                     trim_section=trim_section,
                                     trim_type='trimsec')

        self.assertEqual(self.fake_image.data.shape, (100, 50))
        self.assertEqual(self.fake_image.header['GSP_TRIM'], trim_section)

    def test_save_extracted_target_zero(self):
        self.fake_image.header.set('GSP_FNAM', value=self.file_name)
        same_fake_image = save_extracted(ccd=self.fake_image,
                                         destination=self.current_directory,
                                         prefix='e',
                                         target_number=0)
        self.assertEqual(same_fake_image, self.fake_image)
        self.assertTrue(os.path.isfile('e' + self.file_name))

    def test_save_extracted_target_non_zero(self):
        self.fake_image.header.set('GSP_FNAM', value=self.file_name)
        same_fake_image = save_extracted(ccd=self.fake_image,
                                         destination=self.current_directory,
                                         prefix='e',
                                         target_number=self.target_non_zero)
        self.assertEqual(same_fake_image, self.fake_image)
        self.assertTrue(os.path.isfile('e' + re.sub('.fits',
                                       '_target_{:d}.fits'.format(
                                           self.target_non_zero),
                                       self.file_name)))

    def test_save_extracted_target_zero_comp(self):
        self.fake_image.header.set('GSP_FNAM', value=self.file_name)
        self.fake_image.header.set('OBSTYPE', value='COMP')
        self.fake_image.header.set('GSP_EXTR', value='100.00:101.00')
        same_fake_image = save_extracted(ccd=self.fake_image,
                                         destination=self.current_directory,
                                         prefix='e',
                                         target_number=0)

        self.assertEqual(same_fake_image, self.fake_image)
        self.assertTrue(os.path.isfile(self.fake_image.header['GSP_FNAM']))

    def tearDown(self):
        files_to_remove = [self.full_path, self.fake_image.header['GSP_FNAM']]

        for _file in files_to_remove:
            if os.path.isfile(_file):
                os.unlink(_file)


class NightDataContainerTests(TestCase):

    def setUp(self):
        self.container = NightDataContainer(path=os.getcwd(),
                                            instrument='Red',
                                            technique='Spectroscopy')

    @skip
    def test___repr___method(self):
        pass

    @skip
    def test__get_group_repr(self):
        pass

    @skip
    def test_add_bias(self):
        pass

    @skip
    def test_add_day_flats(self):
        pass

    @skip
    def test_add_data_group(self):
        pass

    @skip
    def test_add_comp_group(self):
        pass

    @skip
    def test_add_object_group(self):
        pass

    @skip
    def test_add_spec_group(self):
        pass

    @skip
    def test_set_sun_times(self):
        pass

    @skip
    def test_set_twilight_times(self):
        pass

    @skip
    def test_set_readout(self):
        pass


class SaturationValuesTest(TestCase):

    def setUp(self):
        self.ccd = CCDData(data=np.ones((100, 100)),
                           meta=fits.Header(),
                           unit='adu')
        self.ccd.header.set('INSTCONF', value='Red')
        self.ccd.header.set('GAIN', value=1.48)
        self.ccd.header.set('RDNOISE', value=3.89)

        self.half_full_well = 69257

        self.saturation_values = SaturationValues(ccd=self.ccd)

    def test_half_full_well_value(self):
        self.assertEqual(self.saturation_values.saturation_value,
                         self.half_full_well)

    def test_empty_result(self):
        self.ccd.header['GAIN'] = 2.3
        result = self.saturation_values.get_saturation_value(ccd=self.ccd)
        self.assertIsNone(result)
        self.assertIsNone(self.saturation_values.saturation_value)
