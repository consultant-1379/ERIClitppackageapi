##############################################################################
# COPYRIGHT Ericsson AB 2013
#
# The copyright to the computer program(s) herein is the property of
# Ericsson AB. The programs may be used and/or copied only with written
# permission from Ericsson AB. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
##############################################################################

from litp.core.extension import ModelExtension
from litp.core.model_type import ItemType
from litp.core.model_type import Property
from litp.core.model_type import PropertyType
from litp.core.model_type import Collection
from litp.core.validators import ValidationError
from litp.core.validators import ItemValidator


class PackageExtension(ModelExtension):

    """LITP Basic package extension for installation of software packages."""

    def define_property_types(self):

        package_name_re = r"[a-zA-Z0-9\-\._]+"

        return [
            PropertyType(
                "package_version",
                regex=r'^(latest|[a-zA-Z0-9\.\-_]+)$',
                regex_error_desc='Value must be either "latest" or '
                        'a valid alphanumeric package version number'
            ),
            PropertyType(
                "package_config",
                regex=r'^(keep|replace)$',
                regex_error_desc='Value must be "keep" or "replace"'
            ),
            PropertyType(
                "package_requires",
                regex=r"^((%s)(,(%s))*)$" % (package_name_re, package_name_re),
                regex_error_desc="Value must be a comma separated list "
                        "of package names"
            ),
        ]

    def define_item_types(self):
        return [
            ItemType(
                "package-list",
                item_description=("This item type represents a collection "
                                "of software packages to install."),
                extend_item="software-item",
                packages=Collection("package"),
                name=Property(
                    "basic_string",
                    prop_description="Name of package collection. This "
                            "property does not affect system state and so "
                            "changes to it will not result in task creation.",
                    required=True
                ),
                version=Property(
                    "basic_string",
                    prop_description="Version of package collection. This "
                            "property does not affect system state and so "
                            "changes to it will not result in task creation.",
                )
            ),
            ItemType(
                "package",
                extend_item="software-item",
                item_description=("This item type represents a "
                                "software package to install."),
                name=Property(
                    "basic_string",
                    prop_description="Name of package to install/remove."
                                     "Needs to match the filename of the "
                                     "underlying RPM.",
                    required=True,
                    updatable_rest=False,
                ),
                version=Property(
                    "package_version",
                    prop_description="Package version to install/remove.",
                ),
                release=Property(
                    "any_string",
                    prop_description="Release number of package to "
                                     "install/remove.",
                ),
                epoch=Property(
                    "integer",
                    prop_description="Epoch of package to "
                                     "install/remove.",
                    default="0",
                ),
                arch=Property(
                    "basic_string",
                    prop_description="Architecture (cpu) of package to "
                                     "install/remove.",
                ),
                config=Property(
                    "package_config",
                    prop_description="Handling of pre-existing configuration "
                                     "files. Must be either 'keep' or "
                                     "'replace'.",
                ),
                repository=Property(
                    "any_string",
                    prop_description="Defines a dependent repository which "
                                    "will be configured before installing "
                                    "the package",
                    deprecated=True,
                ),
                replaces=Property(
                    "basic_string",
                    prop_description="Name of the package to be replaced",
                    required=False,
                    default=None,
                    updatable_rest=False,
                    updatable_plugin=False,
                    site_specific=False,
                ),
                requires=Property(
                    "package_requires",
                    prop_description="A valid package name or a "
                            "comma-separated list of valid package names "
                            "required by the package to be installed first.",
                    required=False,
                    default=None,
                    updatable_rest=False,
                    updatable_plugin=False,
                    site_specific=False,
                ),
                validators=[PackageValidator()]
            )
        ]


class PackageValidator(ItemValidator):

    """
    Custom ItemValidator for package item type.

    Ensures the 'version' property is specified if the 'release' property
    is provided'.

    """

    def validate(self, properties):
        if 'release' in properties and 'version' not in properties:
            return ValidationError(
                property_name="release",
                error_message="The property 'version' must be specified "
                              "if a 'release' value is provided.")
        elif 'version' in properties:
            if 'release' in properties and '-' in properties['version']:
                return ValidationError(
                    property_name="release",
                    error_message="The property 'release' cannot be specified "
                                  "if the release is provided in the version.")
            elif 'release' in properties and \
                    properties['version'] == "latest":
                return ValidationError(
                    property_name="release",
                    error_message="The property 'release' cannot specified "
                                  "if 'version' is set to 'latest'")
            if 'release' not in properties and \
                    '-' not in properties['version'] and \
                    properties['version'] != 'latest':
                return ValidationError(
                    property_name="version",
                    error_message="Please define the release when the version "
                                  "is specified"
                                       )

        if 'replaces' in properties and 'name' in properties and \
                properties['replaces'] == properties['name']:
            return ValidationError(
                property_name="replaces",
                error_message='Replacement of a modelled package '\
                              '"{0}" with "{1}" is not allowed.'.\
                                            format(properties['replaces'],
                                                   properties['name'])
                )

        if 'requires' in properties and 'name' in properties:

            # get the CSV list of requires packages
            # each of these requirements must be validated
            package_name = properties['name']

            requires = [package for package \
                                in properties['requires'].split(',')]

            if package_name in requires:

                err_msg = ('Package "{0}" cannot require itself.'). \
                           format(package_name)
                return ValidationError(
                            property_name="requires",
                            error_message=err_msg
                        )

            checker = dict()

            # Python 2.6 doesn't implement Counter in collections
            for pkg in requires:
                if pkg in checker:
                    checker[pkg] = True
                else:
                    checker[pkg] = False

            duplicated = [package for package, duplicate \
                                  in checker.iteritems() if duplicate]

            if len(duplicated) > 0:

                # we have duplicates
                err_msg = ('Package "{0}" has duplicated requirements. ' + \
                           'Duplicate package requires are : '). \
                          format(package_name)

                for duplicate in sorted(duplicated):
                    err_msg += '"%s" ' % duplicate

                return ValidationError(
                            property_name="requires",
                            error_message=err_msg
                        )
