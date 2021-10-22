from django.shortcuts import render, redirect
from rest_framework import viewsets, views, response
from .serializers import FazzToolsUserSerializer, AltSerializer, ProfessionSerializer, ProfessionTierSerializer, ProfessionRecipeSerializer, AltProfessionSerializer, AltProfessionDataSerializer, AltAchievementSerializer, AltQuestCompletedSerializer, AltMediaSerializer, EquipmentSerializer, AltEquipmentSerializer
from .models import FazzToolsUser, Alt, Profession, ProfessionTier, ProfessionRecipe, AltProfession, AltProfessionData, AltAchievement, AltQuestCompleted, AltMedia, Equipment, AltEquipment
import requests
from django.utils import timezone
import datetime
import hashlib
import hmac

import environ

env = environ.Env()
environ.Env.read_env()

HASH_KEY = env("HASH_KEY").encode()
BLIZZ_CLIENT = env("BLIZZ_CLIENT")
BLIZZ_SECRET = env("BLIZZ_SECRET")

# Create your views here.


class FazzToolsUserView(viewsets.ModelViewSet):
    serializer_class = FazzToolsUserSerializer
    queryset = FazzToolsUser.objects.all()


class AltView(viewsets.ModelViewSet):
    serializer_class = AltSerializer
    queryset = Alt.objects.all()

    def get_queryset(self):
        queryset = Alt.objects.all()
        user = self.request.query_params.get('user')
        if user is None:
            queryset = {}
        else:
            queryset = queryset.filter(user=user)
        return queryset


class ProfessionView(viewsets.ModelViewSet):
    serializer_class = ProfessionSerializer
    queryset = Profession.objects.all()


class ProfessionTierView(viewsets.ModelViewSet):
    serializer_class = ProfessionTierSerializer
    queryset = ProfessionTier.objects.all()


class ProfessionRecipeView(viewsets.ModelViewSet):
    serializer_class = ProfessionRecipeSerializer
    queryset = ProfessionRecipe.objects.all()


class AltProfessionView(viewsets.ModelViewSet):
    serializer_class = AltProfessionSerializer
    queryset = AltProfession.objects.all()

    def get_queryset(self):
        user = self.request.query_params.get('user')
        queryset = Alt.objects.filter(user=user).values_list('altId', flat=True)
        if user is None:
            queryset = {}
        else:
            queryset = AltProfession.objects.filter(alt__in=queryset)
        return queryset


class AltProfessionDataView(viewsets.ModelViewSet):
    serializer_class = AltProfessionDataSerializer
    queryset = AltProfessionData.objects.all()

    def get_queryset(self):
        alt = self.request.query_params.get('alt')
        profession = self.request.query_params.get('profession')
        queryset = AltProfessionData.objects.all()
        if alt is None:
            queryset = {}
        else:
            queryset = queryset.filter(alt=alt, profession=profession)
        return queryset


class AltAchievementView(viewsets.ModelViewSet):
    serializer_class = AltAchievementSerializer
    queryset = AltAchievement.objects.all()


class AltQuestCompletedView(viewsets.ModelViewSet):
    serializer_class = AltQuestCompletedSerializer
    queryset = AltQuestCompleted.objects.all()


class AltMediaView(viewsets.ModelViewSet):
    serializer_class = AltMediaSerializer
    queryset = AltMedia.objects.all()


class EquipmentView(viewsets.ModelViewSet):
    serializer_class = EquipmentSerializer
    queryset = Equipment.objects.all()


class AltEquipmentView(viewsets.ModelViewSet):
    serializer_class = AltEquipmentSerializer
    queryset = AltEquipment.objects.all()


class BnetLogin(viewsets.ViewSet):
    def create(self, request):
        print(BLIZZ_SECRET)
        if request.data.get('state') == 'blizzardeumz76c':
            url = 'https://eu.battle.net/oauth/token?grant_type=authorization_code'
            params = {'client_id': request.data.get('client_id'), 'client_secret': BLIZZ_SECRET, 'code': request.data.get('code'), 'redirect_uri': 'http://localhost:3000/redirect/'}
            x = requests.post(url, data=params)
            try:
                token = x.json()['access_token']
                url = "https://eu.api.blizzard.com/profile/user/wow?namespace=profile-eu&locale=en_US"
                myobj = {'access_token': token}
                y = requests.get(url, params=myobj)
                if y.status_code == 200:
                    encoded = str(y.json()['id']).encode()
                    result = hmac.new(HASH_KEY, encoded, hashlib.sha256).hexdigest()
                    try:
                        user_obj = FazzToolsUser.objects.get(userId=result)
                    except FazzToolsUser.DoesNotExist:
                        user_obj = FazzToolsUser.objects.create(
                            userId=result
                        )
                    altId = []
                    test1 = y.json()['wow_accounts']
                    for key1 in test1:
                        test = key1['characters']
                        for key in test:
                            altId.append(key['id'])
                            try:
                                obj = Alt.objects.get(altId=key['id'])
                                obj.altLevel = key['level']
                                obj.altName = key['name']
                                obj.altRealm = key['realm']['name']
                                obj.altRealmId = key['realm']['id']
                                obj.altRealmSlug = key['realm']['slug']
                                obj.altClass = key['playable_class']['id']
                                obj.altRace = key['playable_race']['id']
                                obj.altGender = key['gender']['name']
                                obj.altFaction = key['faction']['name']
                                obj.altExpiryDate = timezone.now() + datetime.timedelta(days=30)
                                obj.user = user_obj
                                obj.save()
                            except Alt.DoesNotExist:
                                Alt.objects.create(
                                    altId=key['id'],
                                    altLevel=key['level'],
                                    altName=key['name'],
                                    altRealm=key['realm']['name'],
                                    altRealmId=key['realm']['id'],
                                    altRealmSlug=key['realm']['slug'],
                                    altClass=key['playable_class']['id'],
                                    altRace=key['playable_race']['id'],
                                    altGender=key['gender']['name'],
                                    altFaction=key['faction']['name'],
                                    altExpiryDate=timezone.now() + datetime.timedelta(days=30),
                                    user=user_obj
                                )
                    return response.Response({"user": result, "alts": altId})
            except KeyError:
                return response.Response(x.text)
        else:
            return response.Response('error')


class ScanAlt(viewsets.ViewSet):
    def create(self, request):
        print(request.data)
        if request.data.get('altId'):
            temp = Alt.objects.get(altId=request.data.get('altId'))
            realm = temp.altRealmSlug
            name = temp.altName.lower()
        # if request.data.get('name') and request.data.get('realm'):
            url = 'https://eu.battle.net/oauth/token?grant_type=client_credentials'
            params = {'client_id': BLIZZ_CLIENT, 'client_secret': BLIZZ_SECRET}
            x = requests.post(url, data=params)
            try:
                token = x.json()['access_token']
                url = 'https://eu.api.blizzard.com/profile/wow/character/' + realm + '/' + name + '/professions'
                myobj = {'access_token': token, 'namespace': 'profile-eu', 'locale': 'en_US'}
                y = requests.get(url, params=myobj)
                if y.status_code == 200:
                    alt_profs = []
                    alt_obj = Alt.objects.get(altId=y.json()['character']['id'])
                    try:
                        prof_obj = AltProfession.objects.get(alt=alt_obj)
                    except AltProfession.DoesNotExist:
                        prof_obj = AltProfession.objects.create(
                            alt=alt_obj,
                            profession1=0,
                            profession2=0,
                            altProfessionExpiryDate=timezone.now() + datetime.timedelta(days=30)
                        )
                    try:
                        data = y.json()['primaries']
                        for prof in data:
                            alt_profs.append(prof['profession']['id'])
                            try:
                                obj = Profession.objects.get(professionId=prof['profession']['id'])
                            except Profession.DoesNotExist:
                                obj = Profession.objects.create(
                                    professionId=prof['profession']['id'],
                                    professionName=prof['profession']['name']
                                )
                            for tier in prof['tiers']:
                                try:
                                    obj1 = ProfessionTier.objects.get(tierId=tier['tier']['id'])
                                except ProfessionTier.DoesNotExist:
                                    obj1 = ProfessionTier.objects.create(
                                        profession=obj,
                                        tierId=tier['tier']['id'],
                                        tierName=tier['tier']['name']
                                    )
                                for recipe in tier['known_recipes']:
                                    try:
                                        obj2 = ProfessionRecipe.objects.get(recipeId=recipe['id'])
                                    except ProfessionRecipe.DoesNotExist:
                                        obj2 = ProfessionRecipe.objects.create(
                                            professionTier=obj1,
                                            recipeId=recipe['id'],
                                            recipeName=recipe['name']
                                        )
                                    try:
                                        obj3 = AltProfessionData.objects.get(alt=prof_obj, profession=obj, professionTier=obj1, professionRecipe=obj2)
                                        obj3.altProfessionDataExpiryDate = timezone.now() + datetime.timedelta(days=30)
                                        obj3.save()
                                    except AltProfessionData.DoesNotExist:
                                        obj3 = AltProfessionData.objects.create(
                                            alt=prof_obj,
                                            profession=obj,
                                            professionTier=obj1,
                                            professionRecipe=obj2,
                                            altProfessionDataExpiryDate=timezone.now() + datetime.timedelta(days=30)
                                        )
                    except KeyError:
                        return response.Response('keyerrordude')
                    while len(alt_profs) < 2:
                        alt_profs.append(0)
                    obj4 = AltProfession.objects.get(alt=alt_obj)
                    obj4.profession1 = alt_profs[0]
                    obj4.profession2 = alt_profs[1]
                    obj4.altProfessionExpiryDate = timezone.now() + datetime.timedelta(days=30)
                    obj4.save()
                    return response.Response('done')
                else:
                    return response.Response('donebutnotdone')
            except Exception as e:
                print(e)
                return response.Response('notdone')
