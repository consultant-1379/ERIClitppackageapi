##############################################################################
# COPYRIGHT Ericsson AB 2013
#
# The copyright to the computer program(s) herein is the property of
# Ericsson AB. The programs may be used and/or copied only with written
# permission from Ericsson AB. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
##############################################################################

import re
import unittest

from litp.core.model_type import PropertyType, Property, ItemType
from litp.core.model_manager import ModelManager
from package_extension.package_extension import PackageExtension
from package_extension.package_extension import PackageValidator
from litp.core.validators import ValidationError


class TestPackageExtension(unittest.TestCase):

    def setUp(self):
        self.ext = PackageExtension()
        self.model_manager = ModelManager()
        self.validator = self.model_manager.validator
        self.package_validator = PackageValidator()

    def test_property_types_registered(self):
        prop_types_expected = ['package_version',
                               'package_config',
                               'package_requires']
        prop_types = [pt.property_type_id for pt in
                      self.ext.define_property_types()]
        self.assertEquals(prop_types_expected, prop_types)

    def test_item_types_registered(self):
        item_types_expected = ['package-list', 'package']
        item_types = [it.item_type_id for it in
                      self.ext.define_item_types()]
        self.assertEquals(item_types_expected, item_types)

    def test_validate_package_version(self):
        prop_type = PropertyType("basic_string")
        basic_prop = Property('basic_string')
        basic_prop.prop_type = prop_type

        item_type = ItemType(
            'package',
            name=basic_prop,
            version=basic_prop,
            release=basic_prop,
            validators=[PackageValidator()]
        )

        test_props = {
            'name': 'foo',
            'release': 'rc3'
        }

        self.model_manager.register_property_type(prop_type)
        self.model_manager.register_item_type(item_type)

        result = self.validator.validate_properties(item_type, test_props)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].property_name, 'release')
        self.assertEqual(result[0].error_message,
            "The property 'version' must be specified "
            "if a 'release' value is provided.")
        self.assertEqual(result[0].error_type, 'ValidationError')

        test_props.update({'version': '1.2'})
        result = self.validator.validate_properties(item_type, test_props)
        self.assertEqual(len(result), 0)

    def test_validate_package_replaces(self):
        expected_error = ValidationError(
            property_name="replaces",
            error_message='Replacement of a modelled package "foo" with "foo" '
                          'is not allowed.')

        test_props = {
            'name': 'foo',
            'replaces': 'foo'
        }

        error = self.package_validator.validate(test_props)
        self.assertEqual(expected_error, error)

    def test_validate_package_requires(self):
        """
            Test that the list of dependencies are parsed correctly using the
             using the correct property type.
        """

        # set up a package item with the requires property
        basic_string_type = PropertyType("basic_string")
        basic_string_prop = Property("basic_string")
        basic_string_prop.prop_type = basic_string_type

        requires_type = PropertyType("requires")
        requires_prop = Property("requires")
        requires_prop.prop_type = requires_type

        item_type = ItemType(
            'package',
            name=basic_string_prop,
            requires=requires_prop,
            validators=[PackageValidator()]
        )

        # add the package item to the model manager
        self.model_manager.register_property_type(basic_string_type)
        self.model_manager.register_property_type(requires_type)
        self.model_manager.register_item_type(item_type)

        # test 1. check the requires does not contain the package name
        test_1_properties = {
            'name': 'foo',
            'requires': 'some_other_pkg,foo,bar,foobar'
        }

        result = self.validator.validate_properties(
            item_type, test_1_properties)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].property_name, 'requires')
        self.assertEqual(result[0].error_message,
            'Package "foo" cannot require itself.')
        self.assertEqual(result[0].error_type, 'ValidationError')

        # test 2. check the requires does not contain the package name
        test_2_properties = {
            'name': 'foo',
            'requires': 'bar,foobar,bar,httpd,httpd'
        }

        result = self.validator.validate_properties(
            item_type, test_2_properties)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].property_name, 'requires')
        self.assertEqual(result[0].error_message,
            'Package "foo" has duplicated requirements. ' +
            'Duplicate package requires are : "bar" "httpd" '
            )
        self.assertEqual(result[0].error_type, 'ValidationError')

        # test 2. check the requires does not contain the package name
        test_2_properties = {
            'name': 'foo',
            'requires': 'bar,foobar,bar,httpd,httpd'
        }

        result = self.validator.validate_properties(
            item_type, test_2_properties)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].property_name, 'requires')
        self.assertEqual(result[0].error_message,
            'Package "foo" has duplicated requirements. ' +
            'Duplicate package requires are : "bar" "httpd" '
            )
        self.assertEqual(result[0].error_type, 'ValidationError')

if __name__ == '__main__':
    unittest.main()
