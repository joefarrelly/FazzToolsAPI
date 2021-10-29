from django.shortcuts import render, redirect
from rest_framework import viewsets, views, response
# from .serializers import FazzToolsUserSerializer, AltSerializer, ProfessionSerializer, ProfessionTierSerializer, ProfessionRecipeSerializer, AltProfessionSerializer, AltProfessionDataSerializer, EquipmentSerializer, EquipmentVariantSerializer, AltEquipmentSerializer
from .serializers import *
# from .models import FazzToolsUser, Alt, Profession, ProfessionTier, ProfessionRecipe, AltProfession, AltProfessionData, Equipment, EquipmentVariant, AltEquipment
from .models import *
import requests
from django.utils import timezone
import datetime
import hashlib
import hmac
from ratelimit import limits, sleep_and_retry

from types import SimpleNamespace
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

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


class ProfileFazzToolsUserView(viewsets.ModelViewSet):
    serializer_class = ProfileFazzToolsUserSerializer
    queryset = ProfileFazzToolsUser.objects.all()


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
                        user_obj = ProfileFazzToolsUser.objects.get(userId=result)
                    except ProfileFazzToolsUser.DoesNotExist:
                        user_obj = ProfileFazzToolsUser.objects.create(
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
        counter = 0
        if request.data.get('altId') or request.data.get('userid'):
            alts = []
            if request.data.get('altId'):
                alts.append(request.data.get('altId'))
            elif request.data.get('userid'):
                all_alts = ProfileAlt.objects.all()
                old_alts = all_alts.filter(user=request.data.get('userid'))
                for alt in old_alts:
                    alts.append(alt.altId)
            total = len(alts)
            for index, alt in enumerate(alts, start=1):
                print(counter)
                print('Processing: {} of {}'.format(index, total))
                alt_obj = ProfileAlt.objects.get(altId=alt)
                # if alt_obj.altName != 'Fazziest':
                #     continue
                realm = alt_obj.altRealmSlug
                name = alt_obj.altName.lower()
                url = 'https://eu.battle.net/oauth/token?grant_type=client_credentials'
                params = {'client_id': BLIZZ_CLIENT, 'client_secret': BLIZZ_SECRET}
                x = requests.post(url, data=params)
                counter += 1
                try:
                    token = x.json()['access_token']
                    urls = [
                        'https://eu.api.blizzard.com/profile/wow/character/' + realm + '/' + name + '/professions',
                        'https://eu.api.blizzard.com/profile/wow/character/' + realm + '/' + name + '/equipment'
                    ]
                    myobj = {'access_token': token, 'namespace': 'profile-eu', 'locale': 'en_US'}
                    dataobj = {'access_token': token, 'locale': 'en_US'}
                    for url in urls:
                        y = s.get(url, params=myobj, timeout=5)
                        counter += 1
                        if y.status_code == 200:
                            if 'professions' in url:
                                print('profession pending')
                                alt_profs = []
                                try:
                                    prof_obj = ProfileAltProfession.objects.get(alt=alt_obj)
                                except ProfileAltProfession.DoesNotExist:
                                    prof_obj = ProfileAltProfession.objects.create(
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
                                            obj = DataProfession.objects.get(professionId=prof['profession']['id'])
                                        except DataProfession.DoesNotExist:
                                            print('Does not exist: {}'.format(prof['profession']['name']))
                                        for tier in prof['tiers']:
                                            try:
                                                obj1 = DataProfessionTier.objects.get(tierId=tier['tier']['id'])
                                            except DataProfessionTier.DoesNotExist:
                                                print('Does not exist: {}'.format(tier['tier']['name']))
                                            try:
                                                for recipe in tier['known_recipes']:
                                                    try:
                                                        obj2 = DataProfessionRecipe.objects.get(recipeId=recipe['id'])
                                                    except DataProfessionRecipe.DoesNotExist:
                                                        print('Does not exist: {}'.format(recipe['name']))

                                                        recipe_response = limit_call(recipe['key']['href'], params=dataobj)
                                                        counter += 1
                                                        if recipe_response.status_code == 200:
                                                            try:
                                                                recipe_details = recipe_response.json()
                                                                try:
                                                                    rank = recipe_details['rank']
                                                                except KeyError as e:
                                                                    rank = 1
                                                                try:
                                                                    crafted_quantity = recipe_details['crafted_quantity']['value']
                                                                except KeyError as e:
                                                                    crafted_quantity = 1
                                                                try:
                                                                    description = recipe_details['description']
                                                                except KeyError as e:
                                                                    description = 'None'
                                                                obj2 = DataProfessionRecipe.objects.create(
                                                                    tier=obj1,
                                                                    recipeId=recipe_details['id'],
                                                                    recipeName=recipe_details['name'],
                                                                    recipeDescription=description,
                                                                    recipeCategory='N/A',
                                                                    recipeRank=rank,
                                                                    recipeCraftedQuantity=crafted_quantity
                                                                )
                                                            except KeyError as e:
                                                                pass
                                                    try:
                                                        obj3 = ProfileAltProfessionData.objects.get(alt=prof_obj, profession=obj, professionTier=obj1, professionRecipe=obj2)
                                                        obj3.altProfessionDataExpiryDate = timezone.now() + datetime.timedelta(days=30)
                                                        obj3.save()
                                                    except ProfileAltProfessionData.DoesNotExist:
                                                        obj3 = ProfileAltProfessionData.objects.create(
                                                            alt=prof_obj,
                                                            profession=obj,
                                                            professionTier=obj1,
                                                            professionRecipe=obj2,
                                                            altProfessionDataExpiryDate=timezone.now() + datetime.timedelta(days=30)
                                                        )
                                            except KeyError as e:
                                                pass
                                except KeyError as e:
                                    pass
                                while len(alt_profs) < 2:
                                    alt_profs.append(0)
                                old_alt_profs = [prof_obj.profession1, prof_obj.profession2]
                                for prof in old_alt_profs:
                                    if prof not in alt_profs:
                                        ProfileAltProfessionData.objects.filter(alt=prof_obj, profession=prof).delete()
                                prof_obj.profession1 = alt_profs[0]
                                prof_obj.profession2 = alt_profs[1]
                                prof_obj.altProfessionExpiryDate = timezone.now() + datetime.timedelta(days=30)
                                prof_obj.save()
                            elif 'equipment' in url:
                                print('equipment pending')
                                alt_equipment = {}
                                try:
                                    alt_equip_obj = ProfileAltEquipment.objects.get(alt=alt_obj)
                                except ProfileAltEquipment.DoesNotExist:
                                    alt_equip_obj = ProfileAltEquipment.objects.create(
                                        alt=alt_obj,
                                        head=0,
                                        neck=0,
                                        shoulder=0,
                                        back=0,
                                        chest=0,
                                        tabard=0,
                                        shirt=0,
                                        wrist=0,
                                        hands=0,
                                        belt=0,
                                        legs=0,
                                        feet=0,
                                        ring1=0,
                                        ring2=0,
                                        trinket1=0,
                                        trinket2=0,
                                        weapon1=0,
                                        weapon2=0,
                                        altEquipmentExpiryDate=timezone.now() + datetime.timedelta(days=30)
                                    )
                                try:
                                    data = y.json()['equipped_items']
                                    for item in data:
                                        try:
                                            obj = DataEquipment.objects.get(equipmentId=item['item']['id'])
                                        except DataEquipment.DoesNotExist:
                                            obj = DataEquipment.objects.create(
                                                equipmentId=item['item']['id'],
                                                equipmentName=item['name'],
                                                equipmentType=item['item_subclass']['name'],
                                                equipmentSlot=item['slot']['name'],
                                                equipmentIcon='not done yet'
                                            )
                                        variantCode = ''
                                        try:
                                            for bonus in item['bonus_list']:
                                                variantCode += str(bonus)
                                        except KeyError:
                                            variantCode = 'FLUFF'
                                        try:
                                            obj1 = DataEquipmentVariant.objects.get(equipment=obj, variant=variantCode)
                                        except DataEquipmentVariant.DoesNotExist:
                                            stamina = strength = agility = intellect = haste = mastery = vers = crit = 0
                                            try:
                                                for stat in item['stats']:
                                                    if stat['type']['type'] == 'STAMINA':
                                                        stamina = stat['value']
                                                    elif stat['type']['type'] == 'STRENGTH':
                                                        strength = stat['value']
                                                    elif stat['type']['type'] == 'AGILITY':
                                                        agility = stat['value']
                                                    elif stat['type']['type'] == 'INTELLECT':
                                                        intellect = stat['value']
                                                    elif stat['type']['type'] == 'HASTE_RATING':
                                                        haste = stat['value']
                                                    elif stat['type']['type'] == 'MASTERY_RATING':
                                                        mastery = stat['value']
                                                    elif stat['type']['type'] == 'VERSATILITY':
                                                        vers = stat['value']
                                                    elif stat['type']['type'] == 'CRIT_RATING':
                                                        crit = stat['value']
                                            except KeyError:
                                                pass
                                            try:
                                                armour = item['armor']['value']
                                            except KeyError:
                                                armour = 0
                                            obj1 = DataEquipmentVariant.objects.create(
                                                equipment=obj,
                                                variant=variantCode,
                                                stamina=stamina,
                                                armour=armour,
                                                strength=strength,
                                                agility=agility,
                                                intellect=intellect,
                                                haste=haste,
                                                mastery=mastery,
                                                vers=vers,
                                                crit=crit,
                                                level=item['level']['value'],
                                                quality=item['quality']['name']
                                            )
                                        alt_equipment[item['slot']['name'].lower()] = str(item['item']['id']) + ':' + variantCode
                                except KeyError as e:
                                    print(e)
                                setattr(alt_equip_obj, 'head', alt_equipment.get('head') or 0)
                                setattr(alt_equip_obj, 'neck', alt_equipment.get('neck') or 0)
                                setattr(alt_equip_obj, 'shoulder', alt_equipment.get('shoulders') or 0)
                                setattr(alt_equip_obj, 'back', alt_equipment.get('back') or 0)
                                setattr(alt_equip_obj, 'chest', alt_equipment.get('chest') or 0)
                                setattr(alt_equip_obj, 'tabard', alt_equipment.get('tabard') or 0)
                                setattr(alt_equip_obj, 'shirt', alt_equipment.get('shirt') or 0)
                                setattr(alt_equip_obj, 'wrist', alt_equipment.get('wrist') or 0)
                                setattr(alt_equip_obj, 'hands', alt_equipment.get('hands') or 0)
                                setattr(alt_equip_obj, 'belt', alt_equipment.get('waist') or 0)
                                setattr(alt_equip_obj, 'legs', alt_equipment.get('legs') or 0)
                                setattr(alt_equip_obj, 'feet', alt_equipment.get('feet') or 0)
                                setattr(alt_equip_obj, 'ring1', alt_equipment.get('ring 1') or 0)
                                setattr(alt_equip_obj, 'ring2', alt_equipment.get('ring 2') or 0)
                                setattr(alt_equip_obj, 'trinket1', alt_equipment.get('trinket 1') or 0)
                                setattr(alt_equip_obj, 'trinket2', alt_equipment.get('trinket 2') or 0)
                                setattr(alt_equip_obj, 'weapon1', alt_equipment.get('main hand') or 0)
                                setattr(alt_equip_obj, 'weapon2', alt_equipment.get('off hand') or 0)
                                alt_equip_obj.save()
                            else:
                                print('donebutnotdone')
                except Exception as e:
                    print(e)
            return response.Response(timezone.now())
        return response.Response('nouser')


def limit_call(url, params):
    response = s.get(url, params=params, timeout=5)
    return response


class DataScan(viewsets.ViewSet):
    def create(self, request):
        if request.data.get('password') == env("DATA_PASSWORD"):
            url = 'https://eu.battle.net/oauth/token?grant_type=client_credentials'
            params = {'client_id': BLIZZ_CLIENT, 'client_secret': BLIZZ_SECRET}
            x = requests.post(url, data=params)
            try:
                token = x.json()['access_token']
                urls = [
                    'https://eu.api.blizzard.com/data/wow/profession/indexddd',
                    'https://eu.api.blizzard.com/data/wow/mount/index',
                ]
                dataobj = {'access_token': token, 'namespace': 'static-eu', 'locale': 'en_US'}
                for url in urls:
                    y = limit_call(url, params=dataobj)
                    if y.status_code == 200:
                        if 'profession' in url:
                            try:
                                profession_index = y.json()['professions']
                                for profession in profession_index:
                                    # if profession['name'] != 'Mining':
                                    #     continue
                                    profession_response = limit_call(profession['key']['href'], params=dataobj)
                                    if profession_response.status_code == 200:
                                        try:
                                            profession_details = profession_response.json()
                                            try:
                                                obj_profession = DataProfession.objects.get(professionId=profession_details['id'])
                                            except DataProfession.DoesNotExist:
                                                obj_profession = DataProfession.objects.create(
                                                    professionId=profession_details['id'],
                                                    professionName=profession_details['name'],
                                                    professionDescription=profession_details['description']
                                                )
                                        except KeyError as e:
                                            print(e)
                                        try:
                                            tier_index = profession_details['skill_tiers']
                                            for tier in tier_index:
                                                print('Processing tier: {}'.format(tier['name']))
                                                tier_response = limit_call(tier['key']['href'], params=dataobj)
                                                if tier_response.status_code == 200:
                                                    try:
                                                        tier_details = tier_response.json()
                                                        try:
                                                            obj_tier = DataProfessionTier.objects.get(tierId=tier_details['id'])
                                                        except DataProfessionTier.DoesNotExist:
                                                            obj_tier = DataProfessionTier.objects.create(
                                                                profession=obj_profession,
                                                                tierId=tier_details['id'],
                                                                tierName=tier_details['name'],
                                                                tierMinSkill=tier_details['minimum_skill_level'],
                                                                tierMaxSkill=tier_details['maximum_skill_level']
                                                            )
                                                    except KeyError as e:
                                                        print(e)
                                                    try:
                                                        category_index = tier_details['categories']
                                                        for category in category_index:
                                                            print('Processing category: {}'.format(category['name']))
                                                            try:
                                                                recipe_index = category['recipes']
                                                                for recipe in recipe_index:
                                                                    print('Processing recipe: {}'.format(recipe['name']))
                                                                    recipe_response = limit_call(recipe['key']['href'], params=dataobj)
                                                                    if recipe_response.status_code == 200:
                                                                        try:
                                                                            recipe_details = recipe_response.json()
                                                                            try:
                                                                                obj_recipe = DataProfessionRecipe.objects.get(recipeId=recipe_details['id'])
                                                                            except DataProfessionRecipe.DoesNotExist:
                                                                                try:
                                                                                    rank = recipe_details['rank']
                                                                                except KeyError as e:
                                                                                    rank = 1
                                                                                try:
                                                                                    crafted_quantity = recipe_details['crafted_quantity']['value']
                                                                                except KeyError as e:
                                                                                    crafted_quantity = 1
                                                                                try:
                                                                                    description = recipe_details['description']
                                                                                except KeyError as e:
                                                                                    description = 'None'
                                                                                obj_recipe = DataProfessionRecipe.objects.create(
                                                                                    tier=obj_tier,
                                                                                    recipeId=recipe_details['id'],
                                                                                    recipeName=recipe_details['name'],
                                                                                    recipeDescription=description,
                                                                                    recipeCategory=category['name'],
                                                                                    recipeRank=rank,
                                                                                    recipeCraftedQuantity=crafted_quantity
                                                                                )
                                                                        except KeyError as e:
                                                                            print(e)
                                                                        try:
                                                                            reagent_index = recipe_details['reagents']
                                                                            for reagent in reagent_index:
                                                                                reagent_response = limit_call(reagent['reagent']['key']['href'], params=dataobj)
                                                                                if reagent_response.status_code == 200:
                                                                                    try:
                                                                                        reagent_details = reagent_response.json()
                                                                                        try:
                                                                                            obj_reagent = DataReagent.objects.get(reagentId=reagent_details['id'])
                                                                                        except DataReagent.DoesNotExist:
                                                                                            reagent_media_response = limit_call(reagent_details['media']['key']['href'], params=dataobj)
                                                                                            if reagent_media_response.status_code == 200:
                                                                                                try:
                                                                                                    media = reagent_media_response.json()['assets'][0]['value']
                                                                                                except KeyError as e:
                                                                                                    media = 'Not Found'
                                                                                            else:
                                                                                                print(reagent_media_response.status_code)
                                                                                            obj_reagent = DataReagent.objects.create(
                                                                                                reagentId=reagent_details['id'],
                                                                                                reagentName=reagent_details['name'],
                                                                                                reagentQuality=reagent_details['quality']['name'],
                                                                                                reagentMedia=media
                                                                                            )
                                                                                    except KeyError as e:
                                                                                        print(e)
                                                                                    try:
                                                                                        obj_recipereagent = DataRecipeReagent.objects.get(recipe=obj_recipe, reagent=obj_reagent)
                                                                                    except DataRecipeReagent.DoesNotExist:
                                                                                        obj_recipereagent = DataRecipeReagent.objects.create(
                                                                                            recipe=obj_recipe,
                                                                                            reagent=obj_reagent,
                                                                                            quantity=reagent['quantity']
                                                                                        )
                                                                                else:
                                                                                    print(reagent_response.status_code)
                                                                        except KeyError as e:
                                                                            print(e)
                                                                    else:
                                                                        print(recipe_response.status_code)
                                                            except KeyError as e:
                                                                print(e)
                                                    except KeyError as e:
                                                        print(e)
                                                else:
                                                    print(tier_response.status_code)
                                        except KeyError as e:
                                            print(e)
                                    else:
                                        print(profession_response.status_code)
                            except KeyError as e:
                                print(e)
                        elif 'mount' in url:
                            try:
                                mount_index = y.json()['mounts']
                                for mount in mount_index:
                                    print(mount['name'])
                                    mount_response = limit_call(mount['key']['href'], params=dataobj)
                                    if mount_response.status_code == 200:
                                        try:
                                            mount_details = mount_response.json()
                                            try:
                                                obj_mount = DataMount.objects.get(mountId=mount_details['id'])
                                            except DataMount.DoesNotExist:
                                                mount_media_response = limit_call(mount_details['creature_displays'][0]['key']['href'], params=dataobj)
                                                if mount_media_response.status_code == 200:
                                                    try:
                                                        media = mount_media_response.json()['assets'][0]['value']
                                                    except KeyError as e:
                                                        media = 'Not Found'
                                                else:
                                                    print(mount_media_response.status_code)
                                                try:
                                                    faction = mount_details['faction']['name']
                                                except KeyError as e:
                                                    faction = 'N/A'
                                                try:
                                                    source = mount_details['source']['name']
                                                except KeyError as e:
                                                    source = 'N/A'
                                                try:
                                                    description = mount_details['description']
                                                except KeyError as e:
                                                    description = 'None'
                                                if description is None:
                                                    description = 'None'
                                                obj_mount = DataMount.objects.create(
                                                    mountId=mount_details['id'],
                                                    mountName=mount_details['name'],
                                                    mountDescription=description,
                                                    mountSource=source,
                                                    mountMedia=media,
                                                    mountFaction=faction
                                                )
                                        except KeyError as e:
                                            print(e)
                                    else:
                                        print(mount_response.status_code)
                            except KeyError as e:
                                print(e)
                    else:
                        print(y.status_code)
            except KeyError as e:
                print(e)
            return response.Response('Passowrd Correct')
        else:
            return response.Response('Incorrect Password')
