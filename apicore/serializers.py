from rest_framework import serializers
from .models import Alt


class AltSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Alt
        fields = ('altId', 'altLevel', 'altName', 'altRealm', 'altRealmId', 'altRealmSlug', 'altClass', 'altRace', 'altGender', 'altFaction', 'altExpiryDate')
