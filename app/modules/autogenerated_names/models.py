# -*- coding: utf-8 -*-
"""
Autogeneratednames database models
--------------------
"""

import enum
import logging
import uuid

from app.extensions import HoustonModel, db
from app.utils import HoustonException

log = logging.getLogger(__name__)  # pylint: disable=invalid-name

AUTOGEN_NAME_PREFIX_MIN_LENGTH = 2
AUTOGEN_NAME_PREFIX_MAX_LENGTH = 10
AUTOGEN_NAME_CONTEXT_PREFIX = 'auto'


class AutogeneratedNameType(str, enum.Enum):
    auto_species = 'auto_species'
    auto_region = 'auto_region'
    auto_project = 'auto_project'
    auto_organization = 'auto_organization'


class AutogeneratedName(db.Model, HoustonModel):
    """
    AutogeneratedNames database model.
    """

    guid = db.Column(
        db.GUID, default=uuid.uuid4, primary_key=True
    )  # pylint: disable=invalid-name

    type = db.Column(
        db.Enum(AutogeneratedNameType),
        default=AutogeneratedNameType.auto_species,
        nullable=False,
        index=True,
    )
    prefix = db.Column(db.String(), index=True, nullable=False)
    # taxonomy guid for species
    # TODO should this become nullable=False ?
    reference_guid = db.Column(db.GUID, index=True, nullable=True)
    next_value = db.Column(db.Integer, default=0)

    def __repr__(self):
        return (
            '<{class_name}('
            'guid={self.guid}, '
            'type={self.type}, '
            'prefix={self.prefix}, '
            'reference_guid={self.reference_guid}'
            ')>'.format(class_name=self.__class__.__name__, self=self)
        )

    @classmethod
    def type_enabled(cls, type):
        if not type or type not in AutogeneratedNameType.__members__.values():
            return False
        # TODO/FIXME make this look at settings etc!!
        return True

    # we may have persisted AutogeneratedNames (from previous) but site has disabled them/all/something
    def enabled(self):
        return AutogeneratedName.type_enabled(self.type)

    def get_next(self):
        with db.session.begin():
            # keep read/modify/write all within the single db.session to make it atomic WRT the DB
            next_val = str(self.next_value).zfill(4)
            self.next_value += 1
            db.session.merge(self)
        return str(next_val)

    # takes a Name and returns human-facing value
    @classmethod
    def resolve_value(cls, name):
        if not name.context.startswith('autogen-'):
            return name.value  # lets be kind
        agn = AutogeneratedName.query.get(name.context[8:])
        if not agn:
            log.warning(f'no matching AutogeneratedName for {name}')
            return None
        return f'{agn.prefix}-{name.value}'

    @classmethod
    def validate_names(cls, new_autogen_names):
        assert isinstance(new_autogen_names, dict)
        for new_agn_guid in new_autogen_names:
            new_agn = new_autogen_names[new_agn_guid]
            if 'type' not in new_agn or 'prefix' not in new_agn:
                raise HoustonException(
                    log, 'All autogenerated names need a type and a prefix'
                )
            prefix_len = len(new_agn['prefix'])
            if (
                prefix_len < AUTOGEN_NAME_PREFIX_MIN_LENGTH
                or prefix_len > AUTOGEN_NAME_PREFIX_MAX_LENGTH
            ):
                raise HoustonException(
                    log,
                    f'Prefix {new_agn["prefix"]} invalid, must be between {AUTOGEN_NAME_PREFIX_MIN_LENGTH} and '
                    f'{AUTOGEN_NAME_PREFIX_MAX_LENGTH} characters long',
                )
            if new_agn['type'] not in AutogeneratedNameType.__members__.values():
                raise HoustonException(log, f"Type {new_agn['type']} not supported")

        existing_names = AutogeneratedName.query.all()
        # validate all present, cannot remove any type/prefix combinations
        for agn in existing_names:
            if str(agn.guid) not in new_autogen_names:
                raise HoustonException(
                    log,
                    f'Cannot remove existing autogen name type:{agn.type} prefix:{agn.prefix}',
                )
            new_agn = new_autogen_names[str(agn.guid)]
            new_matches = []
            for new_agn_guid in new_autogen_names:
                new_agn_match = new_autogen_names[new_agn_guid]
                if (
                    agn.type == new_agn_match['type']
                    and agn.prefix == new_agn_match['prefix']
                ):
                    new_matches.append(new_agn_guid)
            if len(new_matches) > 1:
                raise HoustonException(
                    log,
                    f'Cannot create an additional autogenerated name for type:{agn.type}, prefix:{agn.prefix}',
                )
            if new_agn['type'] != agn.type.value:
                raise HoustonException(
                    log,
                    f'Cannot change type of existing autogen name guid {agn.guid}, type:{agn.type}',
                )
            if new_agn['prefix'] != agn.prefix:
                raise HoustonException(
                    log,
                    f'Cannot change prefix of existing autogen name guid {agn.guid}, prefix:{agn.prefix}',
                )
            if (
                'reference_guid' in new_agn
                and new_agn['reference_guid'] != agn.reference_guid
            ):
                raise HoustonException(
                    log,
                    f'Cannot change prefix of existing autogen name guid {agn.guid}, reference guid:{agn.reference_guid}',
                )
            if 'start_value' in new_agn and new_agn['start_value'] < agn.next_value:
                raise HoustonException(
                    log,
                    f'Cannot lower start value of existing autogen name guid {agn.guid}, next_value:{agn.next_value}',
                )

    @classmethod
    def set_names_as_rest(cls, new_autogen_names):

        for new_agn_guid in new_autogen_names:
            new_agn = new_autogen_names[new_agn_guid]
            existing_agn = AutogeneratedName.query.get(new_agn_guid)
            if existing_agn:
                with db.session.begin(subtransactions=True):
                    existing_agn.next_value = new_agn['start_value']
                    db.session.merge(existing_agn)
            else:
                with db.session.begin(subtransactions=True):
                    reference_guid = (
                        uuid.UUID(new_agn['reference_guid'])
                        if 'reference_guid' in new_agn
                        else None
                    )
                    next_value = new_agn['next_value'] if 'next_value' in new_agn else 0
                    autogenerated_name = AutogeneratedName(
                        guid=uuid.UUID(new_agn_guid),
                        type=new_agn['type'],
                        prefix=new_agn['prefix'],
                        reference_guid=reference_guid,
                        next_value=next_value,
                    )
                    db.session.add(autogenerated_name)

                import app.extensions.logging as AuditLog  # NOQA

                AuditLog.user_create_object(log, autogenerated_name)

    @classmethod
    def get_rest_response(cls):
        ret_val = {}
        all_agn = AutogeneratedName.query.all()
        for agn in all_agn:
            ret_val[str(agn.guid)] = {
                'type': agn.type,
                'prefix': agn.prefix,
                'reference_guid': agn.reference_guid,
                'next_value': agn.next_value,
            }
        return ret_val
