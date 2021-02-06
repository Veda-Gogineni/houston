# -*- coding: utf-8 -*-
"""
Encounters database models
--------------------
"""

from app.extensions import db, FeatherModel, HoustonModel

from app.modules.submissions import models as submissions_models  # NOQA
from app.modules.assets import models as assets_models  # NOQA


import uuid


class EncounterAssets(db.Model, HoustonModel):
    encounter_guid = db.Column(db.GUID, db.ForeignKey('encounter.guid'), primary_key=True)
    asset_guid = db.Column(db.GUID, db.ForeignKey('asset.guid'), primary_key=True)
    encounter = db.relationship('Encounter', back_populates='assets')
    asset = db.relationship('Asset')


class Encounter(db.Model, FeatherModel):
    """
    Encounters database model.
    """

    guid = db.Column(
        db.GUID, default=uuid.uuid4, primary_key=True
    )  # pylint: disable=invalid-name
    version = db.Column(db.BigInteger, default=None, nullable=True)

    from app.modules.sightings.models import Sighting

    sighting_guid = db.Column(
        db.GUID, db.ForeignKey('sighting.guid'), index=True, nullable=True
    )
    sighting = db.relationship('Sighting', backref=db.backref('encounters'))

    owner_guid = db.Column(db.GUID, db.ForeignKey('user.guid'), index=True, nullable=True)
    owner = db.relationship('User', backref=db.backref('owned_encounters'))

    public = db.Column(db.Boolean, default=False, nullable=False)

    projects = db.relationship('ProjectEncounter', back_populates='encounter')

    assets = db.relationship('EncounterAssets')

    def __repr__(self):
        return (
            '<{class_name}('
            'guid={self.guid}, '
            'version={self.version}, '
            'owner={self.owner},'
            ')>'.format(class_name=self.__class__.__name__, self=self)
        )

    def get_owner(self):
        return self.owner

    def get_sighting(self):
        return self.sighting

    # not going to check for ownership by User.get_public_user() because:
    #  a) this allows for other-user-owned data to be toggled to public
    #  b) allows for us to _disallow_ public access to public-user-owned data
    def is_public(self):
        return self.public

    def has_read_permission(self, obj):
        # todo, check if the encounter owns the sighting once Colin's sightings code is merged in
        # if isinstance(obj, Sighting):
        # check sightings array
        # else look to see if the object is owned by any sighting
        return False

    def get_assets(self):
        return [ref.asset for ref in self.assets]

    def add_asset_in_context(self, asset):
        rel = EncounterAssets(encounter=self, asset=asset)
        db.session.add(rel)
        self.assets.append(rel)

    def delete(self):
        with db.session.begin():
            while self.assets:
                db.session.delete(self.assets.pop())
            db.session.delete(self)

    def delete_from_edm(self, current_app):
        request_func = current_app.edm.delete_passthrough
        passthrough_kwargs = {}
        current_app.edm.ensure_initialed()
        endpoint_url_ = current_app.edm.get_target_endpoint_url('default')
        endpoint = '%s/api/v0/org.ecocean.Encounter/%s' % (
            endpoint_url_,
            str(self.guid),
        )
        response = current_app.edm.request_passthrough(
            endpoint, 'default', request_func, passthrough_kwargs
        )
        return response
