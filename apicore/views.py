from django.shortcuts import render, redirect
from rest_framework import viewsets, views, response
# from .serializers import FazzToolsUserSerializer, AltSerializer, ProfessionSerializer, ProfessionTierSerializer, ProfessionRecipeSerializer, AltProfessionSerializer, AltProfessionDataSerializer, EquipmentSerializer, EquipmentVariantSerializer, AltEquipmentSerializer
from apicore.serializers import *
# from .models import FazzToolsUser, Alt, Profession, ProfessionTier, ProfessionRecipe, AltProfession, AltProfessionData, Equipment, EquipmentVariant, AltEquipment
from apicore.models import *
import requests
from django.utils import timezone
import datetime
import hashlib
import hmac
from ratelimit import limits, sleep_and_retry

from types import SimpleNamespace
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from apicore.tasks import fullDataScan, fullAltScan

import environ

env = environ.Env()
environ.Env.read_env()

HASH_KEY = env("HASH_KEY").encode()
BLIZZ_CLIENT = env("BLIZZ_CLIENT")
BLIZZ_SECRET = env("BLIZZ_SECRET")

# Create your views here.


class DataProfessionView(viewsets.ModelViewSet):
    serializer_class = DataProfessionSerializer
    queryset = DataProfession.objects.all()


class DataProfessionTierView(viewsets.ModelViewSet):
    serializer_class = DataProfessionTierSerializer
    queryset = DataProfessionTier.objects.all()


class DataProfessionRecipeView(viewsets.ModelViewSet):
    serializer_class = DataProfessionRecipeSerializer
    queryset = DataProfessionRecipe.objects.all()


class DataReagentView(viewsets.ModelViewSet):
    serializer_class = DataReagentSerializer
    queryset = DataReagent.objects.all()


class DataRecipeReagentView(viewsets.ModelViewSet):
    serializer_class = DataRecipeReagentSerializer
    queryset = DataRecipeReagent.objects.all()


class DataEquipmentView(viewsets.ModelViewSet):
    serializer_class = DataEquipmentSerializer
    queryset = DataEquipment.objects.all()


class DataEquipmentVariantView(viewsets.ModelViewSet):
    serializer_class = DataEquipmentVariantSerializer
    queryset = DataEquipmentVariant.objects.all()


class DataMountView(viewsets.ModelViewSet):
    serializer_class = DataMountSerializer
    queryset = DataMount.objects.all()


#################################################################################
#                                                                               #
#                            Data/Profile Separator                             #
#                                                                               #
#################################################################################


class ProfileUserView(viewsets.ModelViewSet):
    serializer_class = ProfileUserSerializer
    queryset = ProfileUser.objects.all()


class ProfileUserMountView(viewsets.ModelViewSet):
    serializer_class = ProfileUserMountSerializer
    queryset = ProfileUserMount.objects.all()

    def list(self, request):
        user = request.query_params.get('user')
        queryset = ProfileUserMount.objects.all()
        if user is None:
            queryset = {}
        else:
            queryset = queryset.filter(user=user).select_related('mount').order_by('mount__mountName')
        mounts = {}
        for mount in queryset:
            try:
                mounts[mount.mount.mountSource].append([mount.mount.mountName, mount.mount.mountMediaIcon])
            except KeyError as e:
                mounts[mount.mount.mountSource] = [[mount.mount.mountName, mount.mount.mountMediaIcon]]
        queryset = list(map(list, mounts.items()))
        return response.Response(queryset)


class ProfileAltView(viewsets.ModelViewSet):
    serializer_class = ProfileAltSerializer
    queryset = ProfileAlt.objects.all()

    def list(self, request):
        user = request.query_params.get('user')
        fields = request.query_params.getlist('fields[]')
        queryset = ProfileAlt.objects.all()
        if user is None:
            queryset = {}
        else:
            queryset = queryset.filter(user=user).order_by('-altLevel')
        if not fields or fields[0] == '':
            fields = ['altId', 'altLevel', 'altName', 'altRealm', 'altRealmId', 'altRealmSlug', 'altClass', 'get_altClass_display', 'altRace', 'get_altRace_display', 'altGender', 'altFaction']
        alts = []
        for alt in queryset:
            temp = []
            for field in fields:
                if '_' in field:
                    temp.append(getattr(alt, field)())
                else:
                    temp.append(getattr(alt, field))
            alts.append(temp)
        return response.Response(alts)


class ProfileAltProfessionView(viewsets.ModelViewSet):
    serializer_class = ProfileAltProfessionSerializer
    queryset = ProfileAltProfession.objects.all()

    def list(self, request):
        user = request.query_params.get('user')
        fields = request.query_params.getlist('fields[]')
        queryset = ProfileAlt.objects.filter(user=user).values_list('altId', flat=True)
        if user is None:
            queryset = {}
        else:
            queryset = ProfileAltProfession.objects.filter(alt__in=queryset).select_related('alt').order_by('-alt__altLevel')
        if not fields or fields[0] == '':
            fields = ['.altName', '.altRealm', 'profession1', 'get_profession1_display', 'profession2', 'get_profession2_display']
        alts = []
        for alt in queryset:
            temp = []
            for field in fields:
                if '_' in field:
                    temp.append(getattr(alt, field)())
                elif '.' in field:
                    temp.append(getattr(alt.alt, field[1:]))
                else:
                    temp.append(getattr(alt, field))
            alts.append(temp)
        return response.Response(alts)


class ProfileAltProfessionDataView(viewsets.ModelViewSet):
    serializer_class = ProfileAltProfessionDataSerializer
    queryset = ProfileAltProfessionData.objects.all()

    def list(self, request):
        if request.query_params.get('alt') is not None:
            tiers = {}
            # recipes = {}
            alt = ProfileAlt.objects.filter(altName=request.query_params.get('alt'), altRealm=request.query_params.get('realm'))[:1]
            profession = DataProfession.objects.filter(professionName=request.query_params.get('profession'))[:1]
            queryset = ProfileAltProfessionData.objects.select_related('profession', 'professionTier', 'professionRecipe').all()
            queryset = queryset.filter(alt=alt[0].altId, profession=profession[0].professionId)
            for entry in queryset:
                try:
                    tiers[entry.professionTier.tierName]
                except KeyError:
                    tiers[entry.professionTier.tierName] = {}
                try:
                    tiers[entry.professionTier.tierName][entry.professionRecipe.recipeCategory]
                except KeyError:
                    tiers[entry.professionTier.tierName][entry.professionRecipe.recipeCategory] = []
                # print(entry.professionRecipe)
                recipe_reagent = DataRecipeReagent.objects.select_related('reagent').filter(recipe=entry.professionRecipe)
                # print(recipe_reagent)
                # recipes = {}
                mats = []
                for reagent in recipe_reagent:
                    mats.append([reagent.reagent.reagentName, reagent.quantity, reagent.reagent.reagentMedia, reagent.reagent.reagentQuality])
                recipe_list = [entry.professionRecipe.recipeName, entry.professionRecipe.recipeRank, entry.professionRecipe.recipeCraftedQuantity]
                recipe_list.extend(mats)
                tiers[entry.professionTier.tierName][entry.professionRecipe.recipeCategory].append(recipe_list)
                # try:
                #     recipes[entry.professionRecipe.recipeCategory].append(recipe_list)
                # except KeyError:
                #     recipes[entry.professionRecipe.recipeCategory] = [recipe_list]
                # temp_recipes = list(map(list, recipes.items()))
                # try:
                #     tiers[entry.professionTier.tierName].append(temp_recipes)
                # except KeyError:
                #     tiers[entry.professionTier.tierName] = [temp_recipes]
            queryset = list(map(list, tiers.items()))
            for item in queryset:
                # print(item[1])
                # print('#######')
                item[1] = list(map(list, item[1].items()))
            # queryset = list(tiers[entry.professionTier.tierName].items())
            # queryset = [x for x in tiers.items()]
            # for key, value in queryset:
            #     value = value.sort()
            # print(queryset[-1][0])
            if 'Shadowlands' in queryset[-1][0]:
                queryset.insert(0, queryset.pop())
        else:
            queryset = {}
        return response.Response(queryset)


class ProfileAltEquipmentView(viewsets.ModelViewSet):
    serializer_class = ProfileAltEquipmentSerializer
    queryset = ProfileAltEquipment.objects.all()

    def list(self, request):
        user = request.query_params.get('user')
        fields = request.query_params.getlist('fields[]')
        queryset = ProfileAlt.objects.filter(user=user).values_list('altId', flat=True)
        extra_queryset = DataEquipmentVariant.objects.all()
        if user is None:
            queryset = {}
        else:
            queryset = ProfileAltEquipment.objects.filter(alt__in=queryset).select_related('alt').order_by('-alt__altLevel')
        if not fields or fields[0] == '':
            fields = ['.altName', '.altRealm', 'head', 'neck', 'shoulder', 'back', 'chest', 'tabard', 'shirt', 'wrist', 'hands', 'belt', 'legs', 'feet', 'ring1', 'ring2', 'trinket1', 'trinket2', 'weapon1', 'weapon2']
        alts = []
        for alt in queryset:
            avg_level = []
            temp = []
            for field in fields:
                if '.' in field:
                    temp.append(getattr(alt.alt, field[1:]))
                else:
                    if getattr(alt, field) != '0':
                        equipment, variant = getattr(alt, field).split(':')
                        temp3 = extra_queryset.filter(equipment=equipment, variant=variant)
                        temp.append(temp3[0].level)
                        if field != 'tabard' and field != 'shirt':
                            avg_level.append(temp3[0].level)
                    else:
                        temp.append(getattr(alt, field))
                        if field != 'tabard' and field != 'shirt':
                            avg_level.append(0)
            if avg_level[-1] == 0:
                avg_level.pop()
                avg_level.append(avg_level[-1])
            avg_level = sum(avg_level) / 16
            temp.insert(2, '{0:.2f}'.format(avg_level))
            alts.append(temp)
        return response.Response(sorted(alts, key=lambda x: float(x[2]), reverse=True))


class BnetLogin(viewsets.ViewSet):
    def create(self, request):
        if request.data.get('state') == 'blizzardeumz76c':
            url = 'https://eu.battle.net/oauth/token?grant_type=authorization_code'
            params = {'client_id': request.data.get('client_id'), 'client_secret': BLIZZ_SECRET, 'code': request.data.get('code'), 'redirect_uri': 'https://fazztools.hopto.org/redirect/'}
            # http://localhost:3000/redirect/
            # https://fazztools.hopto.org/redirect/
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
                        user_obj = ProfileUser.objects.get(userId=result)
                    except ProfileUser.DoesNotExist:
                        user_obj = ProfileUser.objects.create(
                            userId=result
                        )
                    altId = []
                    test1 = y.json()['wow_accounts']
                    for key1 in test1:
                        test = key1['characters']
                        for key in test:
                            altId.append(key['id'])
                            try:
                                obj = ProfileAlt.objects.get(altId=key['id'])
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
                            except ProfileAlt.DoesNotExist:
                                ProfileAlt.objects.create(
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


s = requests.Session()
retries = Retry(total=3, backoff_factor=1)
s.mount('https://', HTTPAdapter(max_retries=retries))


class ScanAlt(viewsets.ViewSet):
    def create(self, request):
        if request.data.get('userid'):
            fullAltScan.delay(request.data.get('userid'), BLIZZ_CLIENT, BLIZZ_SECRET)
            return response.Response(timezone.now())
        return response.Response('nouser')


def limit_call(url, params):
    try:
        response = s.get(url, params=params, timeout=5)
        return response
    except requests.exceptions.RequestsException as e:
        temp_response = {'status_code': 999}
        response = SimpleNamespace(**temp_response)
        return response


class DataScan(viewsets.ViewSet):
    def create(self, request):
        if request.data.get('password') == env("DATA_PASSWORD"):
            fullDataScan.delay(BLIZZ_CLIENT, BLIZZ_SECRET)
            return response.Response('Passowrd Correct')
        else:
            return response.Response('Incorrect Password')
