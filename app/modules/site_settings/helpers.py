# -*- coding: utf-8 -*-
"""
Site Settings interactions with other modules
This is where the knowledge is of the component specific functionality where some site settings needs to be
read/stored/validated
--------------------
"""
import logging

from flask_login import current_user  # NOQA

import app.extensions.logging as AuditLog  # NOQA
from app.modules import is_module_enabled
from app.utils import HoustonException

log = logging.getLogger(__name__)  # pylint: disable=invalid-name


# Helper for validating the required fields in any level dictionary
def validate_fields(dictionary, fields, error_str):
    for field, field_type, mandatory in fields:
        if mandatory:
            if field not in dictionary:
                raise HoustonException(log, f'{field} field missing from {error_str}')
            if not isinstance(dictionary[field], field_type):
                raise HoustonException(
                    log,
                    f'{field} field had incorrect type, expected {field_type.__name__} in {error_str}',
                )

            if field_type == list:
                # All mandatory lists must have at least one entry
                if len(dictionary[field]) < 1:
                    raise HoustonException(
                        log, f'{field} in {error_str} must have at least one entry'
                    )
        elif field in dictionary:
            if not isinstance(dictionary[field], field_type):
                raise HoustonException(log, f'{field} incorrect type in {error_str}')

        if (
            mandatory
            and field_type == str
            and field in dictionary
            and len(dictionary[field]) == 0
        ):
            raise HoustonException(log, f'{field} cannot be empty string in {error_str}')


class SiteSettingSpecies(object):
    @classmethod
    def validate(cls, value):
        assert isinstance(value, list)
        species_fields = [
            ('commonNames', list, True),
            ('scientificName', str, True),
            ('itisTsn', int, False),
        ]
        for spec in value:
            validate_fields(spec, species_fields, 'site.species')

    @classmethod
    def set(cls, key, value, key_data):
        import uuid

        from .models import SiteSetting

        log.debug(f'updating Houston Setting key={key} value={value}')
        for spec in value:
            if 'id' not in spec:
                spec['id'] = str(uuid.uuid4())

        SiteSetting.set(key, data=value, public=key_data.get('public', True))


class SiteSettingModules(object):
    @classmethod
    def validate_autogen_names(cls, value):
        if is_module_enabled('autogenerated_names'):
            from app.modules.autogenerated_names.models import AutogeneratedName

            return AutogeneratedName.validate_names(value)
        else:
            return []

    @classmethod
    def update_autogen_names(cls, value):
        if is_module_enabled('autogenerated_names'):
            from app.modules.autogenerated_names.models import AutogeneratedName

            AutogeneratedName.set_names_as_rest(value)

    @classmethod
    def validate_social_group_roles(cls, value):
        if is_module_enabled('social_groups'):
            from app.modules.social_groups.models import SocialGroup

            SocialGroup.validate_roles(value)

    @classmethod
    def update_social_group_roles(cls, value=None):
        if is_module_enabled('social_groups'):
            from app.modules.social_groups.models import SocialGroup

            SocialGroup.site_settings_updated()

    @classmethod
    def validate_relationship_type_roles(cls, value):
        from .schemas import RelationshipTypeSchema

        if not isinstance(value, dict):
            raise HoustonException(log, 'value must be a dict')
        schema = RelationshipTypeSchema()
        for relationship_object in value.values():
            errors = schema.validate(relationship_object)
            if errors:
                raise HoustonException(log, schema.get_error_message(errors))


class SiteSettingCustomFields(object):
    @classmethod
    def validate_categories(cls, value):
        if not isinstance(value, list):
            raise HoustonException(log, 'customFieldCategories needs to be a list')
        category_fields = [
            ('id', str, True),
            ('label', str, True),
            ('type', str, True),
        ]
        for cat in value:
            validate_fields(cat, category_fields, 'customFieldCategories')
            # To be resolved by DEX-1351
            # TODO, check the type for being 'sighting', 'encounter' or 'individual'?
            # TODO check for existing to see if this is an attempted change

    # class_name is Captitalized (Encounter, Sighting, Individual)
    @classmethod
    def _validate_fields(cls, value, class_name):
        from .models import SiteSetting

        field_str = f'customFields.{class_name}'
        if 'definitions' not in value:
            raise HoustonException(log, f"{field_str} must contain a 'definitions' block")
        defs = value['definitions']
        if not isinstance(defs, list):
            raise HoustonException(log, f'{field_str} needs to be a list')
        custom_fields = [
            ('id', str, True),
            ('name', str, True),
            ('schema', dict, True),
            ('multiple', bool, True),
        ]
        schema_fields = [
            ('category', str, True),
            ('description', str, False),
            ('displayType', str, True),
            ('label', str, True),
        ]
        # for each displayType there is a corresponding `type` that is what is stored; not sure FE needs this
        # TODO investigate DEX 1351
        # internal type is noted as comment here (if different than displayType) in case we need it
        # this list is from a conversation with ben 1/21/2022 - not sure if this is current
        valid_display_types = {
            'string',
            'longstring',  # str
            'select',  # string (valid from schema.choices)
            'multiselect',  # [strings] (valid from schema.choices)  multiple=T
            'boolean',
            'integer',
            'float',
            'date',  # datetime
            'feetmeters',  # float (stored as meters)
            'daterange',  # [ date, date ]  multiple=T value len must == 2
            'specifiedTime',  # json -> { time: datetime, timeSpecificity: string (ComplexDateTime.specificities }
            'locationId',  # string (valid region id)
            # not yet supported, see: DEX-1261
            'file',  # FileUpload (guid)
            # not yet supported, see: DEX-1038
            'latlong',  # [ float, float ]  multiple=T  value len must == 2  NOTE: this might be called 'geo'?  see ticket
            'individual',  # guid (valid indiv guid)
        }
        categories = SiteSetting.get_value('site.custom.customFieldCategories')
        current_data = SiteSetting.get_value(f'site.custom.{field_str}')
        existing_ids = []
        existing_fields = []
        if current_data:
            existing_fields = current_data.get('definitions')
            existing_ids = [exist['id'] for exist in existing_fields]
        dropped_ids = existing_ids.copy()  # will be whittled down

        # 'type' value is all lowercase, thus:
        category_ids = [
            cat['id'] for cat in categories if cat['type'] == class_name.lower()
        ]
        for cf_def in defs:
            validate_fields(cf_def, custom_fields, field_str)
            validate_fields(cf_def['schema'], schema_fields, f'{field_str} schema')
            cf_cat_id = cf_def['schema']['category']
            if cf_cat_id not in category_ids:
                raise HoustonException(
                    log, f'{field_str} category-id {cf_cat_id} not found'
                )
            cf_id = cf_def['id']
            if cf_id in dropped_ids:
                dropped_ids.remove(cf_id)
            if cf_id in existing_ids:
                current_val = [
                    current for current in existing_fields if current['id'] == cf_id
                ]
                assert len(current_val) == 1
                if current_val[0] != cf_def:
                    # this will raise exception if trouble
                    cls._change_data(current_val[0], cf_def, class_name)
            display_type = cf_def['schema']['displayType']
            if display_type not in valid_display_types:
                raise HoustonException(
                    log,
                    f'{field_str} id {cf_cat_id}: displayType {display_type} not valid',
                )

            # see DEX-1270
            if display_type in {'select', 'multiselect'}:
                if 'choices' not in cf_def['schema'] or not isinstance(
                    cf_def['schema']['choices'], list
                ):
                    raise HoustonException(
                        log,
                        f'{field_str} id {cf_cat_id}: displayType {display_type} requires "choices" list in schema',
                    )
                    if (
                        len(cf_def['schema']['choices']) < 1
                    ):  # i guess we allow choices of only 1 value??
                        raise HoustonException(
                            log,
                            f'{field_str} id {cf_cat_id}: displayType {display_type} requires "choices" have at least one value',
                        )
                    choice_values = {}
                    for choice in cf_def['schema']['choices']:
                        if not isinstance(choice, dict):
                            raise HoustonException(
                                log,
                                f'{field_str} id {cf_cat_id}: displayType {display_type} non-dict choice: {choice}',
                            )
                        if 'label' not in choice:
                            raise HoustonException(
                                log,
                                f'{field_str} id {cf_cat_id}: displayType {display_type} choice missing "label": {choice}',
                            )
                        if 'value' not in choice:
                            raise HoustonException(
                                log,
                                f'{field_str} id {cf_cat_id}: displayType {display_type} choice missing "value": {choice}',
                            )
                        value = choice.get('value')
                        if value in choice_values:
                            raise HoustonException(
                                log,
                                f'{field_str} id {cf_cat_id}: displayType {display_type} duplicate choice value in: {choice}',
                            )
                        choice_values.add(value)

        # after iterating thru defs, if we have anything in dropped_ids, it means it is a definition we _had_ but
        #   has not been sent, so must have been dropped.  now we deal with that.
        for cf_id in dropped_ids:
            cls._drop_data(cf_id, class_name)

    @classmethod
    def get_definition(cls, cls_name, guid):
        from .models import SiteSetting

        # bad cls_name will get raise HoustonException
        data = SiteSetting.get_value(f'site.custom.customFields.{cls_name}')
        if not data or not isinstance(data.get('definitions'), list):
            return None
        for defn in data['definitions']:
            if guid == defn.get('id'):
                return defn
        return None

    @classmethod
    # replace=False will silently fail if already exists
    def add_definition(cls, class_name, guid, defn, replace=False):
        from .models import SiteSetting

        # bad class_name will get raise HoustonException
        data = SiteSetting.get_value(f'site.custom.customFields.{class_name}')
        if not data or not isinstance(data.get('definitions'), list):
            data = {'definitions': []}
        found = False
        for i in range(len(data['definitions'])):
            if guid == data['definitions'][i].get('id'):
                if replace:
                    found = True
                    data['definitions'][i] = defn
                else:
                    return  # exists - no update!
        if not found:
            data['definitions'].append(defn)
        AuditLog.audit_log(log, f'add_definition added {guid} to {class_name}')
        SiteSetting.set(f'site.custom.customFields.{class_name}', data=data)

    # WARNING: this does no safety check (_drop_data etc), so really other code that
    #   wraps this should be used, e.g. patch_remove()
    @classmethod
    def remove_definition(cls, class_name, guid):
        from .models import SiteSetting

        # bad class_name will get raise HoustonException
        data = SiteSetting.get_value(f'site.custom.customFields.{class_name}')
        if not data or not isinstance(data.get('definitions'), list):
            return
        new_list = []
        found = False
        for defn in data['definitions']:
            if guid == defn.get('id'):
                found = True
            else:
                new_list.append(defn)
        if found:
            AuditLog.audit_log(log, f'remove_definition dropped {guid} for {class_name}')
            SiteSetting.set(
                f'site.custom.customFields.{class_name}', data={'definitions': new_list}
            )

    # expects cf_defn as from above
    # NOTE this is very very likely incomplete.  the 'type' value in definitions are quite complex.
    #    probably need to check in with FE for what is actually needed
    #    see also:  valid_display_types under _validate_fields
    #
    # !! a NOTE on None ... it remains to be seen if None *always should* be allowed as a valid value,
    #    regardless of type/scenario.  for now, it is allowed (except where choices is involved)
    #    a None will cause the customField to have an entry like { CFD_ID: None } ... which is -- what it is.
    #    the more pedantic among us might prefer to use op=remove for this scenario, i suppose
    @classmethod
    def is_valid_value(cls, cf_defn, value):
        import copy
        import datetime

        # see note above
        #  FIXME fix this for choices when we get to that.  :(
        if value is None:
            return True

        if cf_defn.get('multiple', False):
            if not isinstance(value, list):
                log.debug(f'multiple=T but value not list: value={value} defn={cf_defn}')
                return False
            # a little hackery / slight-of-hand
            cf_defn_single = copy.deepcopy(cf_defn)
            cf_defn_single['multiple'] = False
            for val in value:
                val_ok = cls.is_valid_value(cf_defn_single, val)
                if not val_ok:
                    return False
            return True  # all passed

        # this is just what the value must be in terms of instance
        base_type = {
            'string': str,
            'integer': int,
            'double': float,
            'boolean': bool,
            'json': dict,  # can json also be a list?
            'date': datetime.datetime,
            'geo': list,
        }
        # defaults to str ???
        instance_type = base_type.get(cf_defn['type'], str)

        if not isinstance(value, instance_type):
            log.debug(
                f'value not instance of {str(instance_type)}: value={value} defn={cf_defn}'
            )
            return False

        # FIXME get more strict here, like:
        #  * len(geo) == 2 and must be valid lat/lon
        #  * if choices, value must be one of choices

        return True

    @classmethod
    def is_valid_value_for_class(cls, cls_name, cfd_id, value):
        defn = cls.get_definition(cls_name, cfd_id)
        if not defn:
            return False
        if not cls.is_valid_value(defn, value):
            return False
        return True

    # DEX-1337 PATCH op=remove path=site.custom.customFields.CLASS/GUID must be supported
    #   this also will be called for (currently unused) PATCH op=remove path=site.custom.customFieldCategories fwiw (see DEX-1362)
    #   force_removal=True means go ahead and blow away all the data that exists.  ouch!
    #
    #   note: this *intentionally* disallows straight-up reseting entire customFields.CLASS object.  youre welcome.
    @classmethod
    def patch_remove(cls, key, force_removal=False):
        import re

        m = re.search(r'site.custom.customFields.(\w+)/([\w\-]+)', key)
        assert m and len(m.groups()) == 2
        class_name = m.group(1)
        cf_id = m.group(2)
        defn = cls.get_definition(class_name, cf_id)
        if not defn:
            raise ValueError(f'invalid guid {cf_id} for class {class_name}')
        # FIXME _drop_data does not yet take into consideration force=True so this needs fixing
        #       for now it will just outright fail if there is data (safest route)
        cls._drop_data(cf_id, class_name)
        cls.remove_definition(class_name, cf_id)

    # "in the future" this can be much smarter, including things like:
    # - checking valid transformations, like int -> float etc.
    # - looking at modifications of schema.choices and check for validity
    # - possibly providing hints at transforming (e.g. "Male" becomes "male")
    #
    # for now, it basically will disallow changing a definition *if it is used at all*
    @classmethod
    def _change_data(cls, cf_def_old, cf_def_new, class_name):
        cf_id = cf_def_new.get('id')
        assert cf_id
        objs_using = cls._find_data(cf_id, class_name)
        if objs_using:
            raise HoustonException(
                log,
                f'customFields.{class_name} id {cf_id} in use by {len(objs_using)} objects; cannot be changed',
            )

    # like above, for now we just fail to let a CustomFieldDefinition be dropped *if it is used at all*
    #   (but can expand later to check for data, admin verification of data-loss, etc)
    #  TODO this should also be used when PATCH op=remove of a CFD:   (note 'force' boolean to destroy data)
    #      {'force': False, 'op': 'remove', 'path': 'site.custom.customFields.Encounter/DEFNGUID'}
    #      DEX 1337 will sort this out
    @classmethod
    def _drop_data(cls, cf_id, class_name):
        assert cf_id
        objs_using = cls._find_data(cf_id, class_name)
        if objs_using:
            raise HoustonException(
                log,
                f'customFields.{class_name} id {cf_id} in use by {len(objs_using)} objects; cannot be dropped',
            )

    # NOTE a bit hactacular/experimental
    #   this is for finding actual objects which are using (have values for) a given customFieldDefinition
    @classmethod
    def _find_data(cls, cf_id, class_name):
        # hacky - it limits us to these 3 classes, alas
        from app.extensions import db
        from app.modules.encounters.models import Encounter
        from app.modules.individuals.models import Individual
        from app.modules.sightings.models import Sighting

        assert cf_id
        cls_map = {
            'Encounter': Encounter,
            'Sighting': Sighting,
            'Individual': Individual,
        }
        cls = cls_map.get(class_name)
        assert cls
        has_values = []
        res = db.session.execute(
            # h/t https://stackoverflow.com/a/68679549 for this madness
            f'SELECT guid FROM {class_name.lower()} WHERE (custom_fields #>> \'{{}}\')::jsonb->\'{cf_id}\' IS NOT NULL'
        )
        for row in res:
            obj = cls.query.get(row[0])
            has_values.append(obj)
        return has_values

    @classmethod
    def validate_encounters(cls, value):
        cls._validate_fields(value, 'Encounter')

    @classmethod
    def validate_sightings(cls, value):
        cls._validate_fields(value, 'Sighting')

    @classmethod
    def validate_individuals(cls, value):
        cls._validate_fields(value, 'Individual')