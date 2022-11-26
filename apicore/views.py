from django.shortcuts import render, redirect
from rest_framework import viewsets, views, response
from rest_framework.parsers import MultiPartParser
# from .serializers import FazzToolsUserSerializer, AltSerializer, ProfessionSerializer, ProfessionTierSerializer, ProfessionRecipeSerializer, AltProfessionSerializer, AltProfessionDataSerializer, EquipmentSerializer, EquipmentVariantSerializer, AltEquipmentSerializer
from apicore.serializers import *
# from .models import FazzToolsUser, Alt, Profession, ProfessionTier, ProfessionRecipe, AltProfession, AltProfessionData, Equipment, EquipmentVariant, AltEquipment
from apicore.models import *
import requests
from django.utils import timezone
import datetime
import time
import hashlib
import hmac
from ratelimit import limits, sleep_and_retry

from types import SimpleNamespace
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from apicore.tasks import fullDataScan, fullAltScan
from apicore.libs.keybind_mapping import getKeybindMap
from apicore.libs.icon_mapping import getIconMap

import environ

import os

import ast
import re

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


class DataPetView(viewsets.ModelViewSet):
    serializer_class = DataPetSerializer
    queryset = DataPet.objects.all()


#################################################################################
#                                                                               #
#                            Data/Profile Separator                             #
#                                                                               #
#################################################################################


class ProfileUserView(viewsets.ModelViewSet):
    serializer_class = ProfileUserSerializer
    queryset = ProfileUser.objects.all()

    def perform_update(self, serializer):
        user = serializer.validated_data.get('userId')
        file = serializer.validated_data.get('userFile')
        # print(file.read().decode('utf-8')[1:19])
        # print('FazzToolsScraperDB')
        # print(file.read().decode('utf-8')[1:19] == 'FazzToolsScraperDB')
        # testing = file.read().decode('utf-8')[1:19]
        # print((testing.strip()) == 'FazzToolsScraperDB')
        # print(len(testing))
        # print(len('FazzToolsScraperDB'))
        print(file.name)
        if file.name == 'FazzToolsScraper.lua':
            file.name = user + '.lua'
            print(file.name)
            if file.size < 10000000:
                print(file.size)
                # if file.content_type == 'text/x-lua':
                #     print(file.content_type)
                # fileCheck = file.read().decode('utf-8')[1:21]
                f = file.open('r+')
                fileCheck = f.read().decode('utf-8')
                # print(fileCheck[1:19])
                # if fileCheck[1:19].decode('utf-8') == 'FazzToolsScraperDB':
                if 'FazzToolsScraperDB' in fileCheck[0:25]:
                    print("here")
                    # print(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
                    final_file = re.sub(r'(\r\n|\r|\n)(?=(?:[^"]*"[^"]*")*[^"]*$)', r'\n', fileCheck)
                    f.seek(0)
                    f.write(final_file.encode())
                    f.truncate()
                    obj_user = ProfileUser.objects.get(userId=user)
                    updateDate = obj_user.userLastUpdate
                    try:
                        os.remove(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)) + obj_user.userFile.url)
                    except Exception as e:
                        print(e)
                    serializer.save(userId=user, userFile=file, userLastUpdate=updateDate)
                else:
                    print("Invalid 4")
                f.close()
            else:
                print("Invalid 2")
        else:
            print("Invalid 3")

    def list(self, request):
        global all_lines
        user = request.query_params.get('user')
        queryset = ProfileUser.objects.all()
        if user is None:
            queryset = {}
        else:
            queryset = queryset.filter(userId=user)
        result = []
        if request.query_params.get('page') is None:
            queryset = ProfileUser.objects.all()
            return response.Response('hey')
        elif request.query_params.get('page') == 'header':
            tempDate = queryset[0].userLastUpdate
            temp2Date = time.mktime(tempDate.timetuple()) * 1000
            result.append(temp2Date)
        else:
            if queryset[0].userFile:
                temp = queryset[0].userFile
                temp2 = temp.file.open('r')
                # temp3 = temp2.read()
                temp3 = temp2.readlines()
                # temp6 = temp3.decode('utf-8')
                # print(repr(temp3))
                all_lines = [line.decode('utf-8') for line in temp3]
                temp.file.close()
                temp4 = recursive()
                temp7 = temp4[1]
                # print(temp6)
                # print(temp7)
                if request.query_params.get('page') == 'all':
                    for alt in temp7['alts']:
                        specs = []
                        if temp7['alts'][alt]['kb'] is not None:
                            for spec in temp7['alts'][alt]['kb']:
                                specs.append(spec)
                        else:
                            specs = ['---', '---', '---', '---']
                        specs.sort()
                        while len(specs) < 4:
                            specs.append('---')
                        alt_specs = alt.split('-')
                        alt_obj = ProfileAlt.objects.get(altName=alt_specs[0], altRealm=alt_specs[1])
                        alt_specs.append(alt_obj.get_altClass_display())
                        alt_specs.extend(specs)
                        result.append(alt_specs)
                    result.sort(key=lambda x: (x[1], x[0]))
                elif request.query_params.get('page') == 'single':
                    alt = request.query_params.get('alt').title()
                    realm = request.query_params.get('realm').title()
                    spec = request.query_params.get('spec').title()
                    altFull = alt + '-' + realm
                    alt_config = temp7['alts'][altFull]
                    keybind_map = getKeybindMap(alt_config['kbConfig']['addon'])
                    user_keybind = {}
                    for spell in alt_config['kb'][spec]:
                        nice_spell = alt_config['kb'][spec][spell]
                        if nice_spell.split(':')[0] == 'spell':
                            try:
                                user_keybind[nice_spell] = alt_config['kbConfig']['map'][keybind_map[int(spell)]]
                            except:
                                pass
                        elif nice_spell.split(':')[0] == 'macro':
                            found = False
                            for thing in alt_config['spell'][spec]:
                                for name_spell in alt_config['spell'][spec][thing]:
                                    if alt_config['spell'][spec][thing][name_spell][1] in alt_config['macro'][nice_spell.split(':')[1]][3]:
                                        found = True
                                        if not user_keybind.get('spell:' + str(name_spell)):
                                            try:
                                                user_keybind['spell:' + str(name_spell)] = alt_config['kbConfig']['map'][keybind_map[int(spell)]]
                                            except:
                                                pass
                                        else:
                                            if user_keybind['spell:' + str(name_spell)] != alt_config['kbConfig']['map'][keybind_map[int(spell)]]:
                                                user_keybind['spell:' + str(name_spell)] += " | " + alt_config['kbConfig']['map'][keybind_map[int(spell)]]
                                if not found:
                                    try:
                                        user_keybind[nice_spell] = alt_config['kbConfig']['map'][keybind_map[int(spell)]]
                                    except:
                                        pass
                        elif nice_spell.split(':')[0] == 'item':
                            for name_spell in alt_config['item']:
                                if name_spell == nice_spell.split(':')[1]:
                                    try:
                                        user_keybind[nice_spell] = alt_config['kbConfig']['map'][keybind_map[int(spell)]]
                                    except:
                                        pass
                    alt = request.query_params.get('alt').title()
                    realm = request.query_params.get('realm').title()
                    spec = request.query_params.get('spec').title()
                    altFull = alt + '-' + realm
                    alt_config = temp7['alts'][altFull]
                    alt_obj = ProfileAlt.objects.get(altName=alt, altRealm=realm)
                    user_class = alt_obj.get_altClass_display()
                    SPELLS_ORDER = {'Base': 0, 'Talent': 1, 'Misc': 2}
                    spam_filter = ['Auto Attack', 'Mobile Banking', 'Revive Battle Pets', 'Vindicaar Matrix Crystal', 'Shoot']
                    full_result = []
                    for tab in alt_config['spell'][spec]:
                        list_spells = []
                        for spell in alt_config['spell'][spec][tab]:
                            if alt_config['spell'][spec][tab][spell][1] in spam_filter:
                                continue
                            list_spell_single = []
                            for stat in alt_config['spell'][spec][tab][spell]:
                                if stat == 1:
                                    list_spell_single.append(alt_config['spell'][spec][tab][spell][stat])
                            try:
                                list_spell_single.append(user_keybind['spell:' + str(spell)])
                            except:
                                list_spell_single.append('UNBOUND')
                            list_spells.append(list_spell_single)
                        list_spells = sorted(list_spells, key=lambda x: x[0])
                        full_result.append([tab.title(), list_spells])
                    list_spells = []
                    for item in alt_config['item']:
                        if user_keybind.get('item:' + str(item)):
                            list_spells.append([alt_config['item'][item][1], user_keybind['item:' + str(item)]])
                    for macro in alt_config['macro']:
                        if user_keybind.get('macro:' + str(macro)):
                            list_spells.append(['[Macro] {}'.format(alt_config['macro'][macro][1]), user_keybind['macro:' + str(macro)]])
                    list_spells = sorted(list_spells, key=lambda x: x[0])
                    full_result.append(['Misc', list_spells])
                    result = sorted(full_result, key=lambda x: SPELLS_ORDER[x[0]])
                    testing1 = [x for x in result[0][1] if x not in result[1][1]]
                    result[0][1] = testing1
                else:
                    result = ['sadge']
                # temp.file.close()
            else:
                result = []
        return response.Response(result)


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
        all_mounts = DataMount.objects.all().order_by('mountName')
        # print(all_mounts[1])
        # print(queryset)
        collected = []
        if queryset:
            for known in queryset:
                collected.append(known.mount.mountId)
            # counter = 0
            for mount in all_mounts:
                try:
                    mounts[mount.mountSource]
                except KeyError as e:
                    mounts[mount.mountSource] = {}
                try:
                    mounts[mount.mountSource]['collected']
                except KeyError as e:
                    mounts[mount.mountSource]['collected'] = []
                try:
                    mounts[mount.mountSource]['uncollected']
                except KeyError as e:
                    mounts[mount.mountSource]['uncollected'] = []
                # if mount.mountId == queryset[counter].mount.mountId:
                if mount.mountId in collected:
                    mounts[mount.mountSource]['collected'].append({'name': mount.mountName, 'icon': mount.mountMediaIcon})
                    # counter += 1
                else:
                    mounts[mount.mountSource]['uncollected'].append({'name': mount.mountName, 'icon': mount.mountMediaIcon})
            # for mount in queryset:
            #     try:
            #         mounts[mount.mount.mountSource].append({'name': mount.mount.mountName, 'icon': mount.mount.mountMediaIcon})
            #     except KeyError as e:
            #         mounts[mount.mount.mountSource] = [{'name': mount.mount.mountName, 'icon': mount.mount.mountMediaIcon}]
            # queryset = list(map(list, mounts.items()))
            known = 0
            unknown = 0
            available = 0
            for category_name, category_data in mounts.items():
                collected = len(category_data['collected'])
                uncollected = len(category_data['uncollected'])
                total = collected + uncollected
                mounts[category_name]['collected_count'] = collected
                mounts[category_name]['uncollected_count'] = uncollected
                mounts[category_name]['total_count'] = total
                known += collected
                unknown += uncollected
                available += total
            # mounts['known'] = known
            # mounts['unknown'] = unknown
            # mounts['available'] = available

            queryset = list(mounts.items())
            queryset.append(known)
            queryset.append(unknown)
            queryset.append(available)
        # queryset = mounts
        return response.Response(queryset)


class ProfileUserPetView(viewsets.ModelViewSet):
    serializer_class = ProfileUserPetSerializer
    queryset = ProfileUserPet.objects.all()

    def list(self, request):
        user = request.query_params.get('user')
        queryset = ProfileUserPet.objects.all()
        if user is None:
            queryset = {}
        else:
            queryset = queryset.filter(user=user).select_related('pet').order_by('pet__petName')
        pets = {}
        all_pets = DataPet.objects.all().order_by('petName')
        collected = []
        if queryset:
            for known in queryset:
                collected.append(known.pet.petId)
            # counter = 0
            for pet in all_pets:
                try:
                    pets[pet.petSource]
                except KeyError as e:
                    pets[pet.petSource] = {}
                try:
                    pets[pet.petSource]['collected']
                except KeyError as e:
                    pets[pet.petSource]['collected'] = []
                try:
                    pets[pet.petSource]['uncollected']
                except KeyError as e:
                    pets[pet.petSource]['uncollected'] = []
                if pet.petId in collected:
                    pets[pet.petSource]['collected'].append({'name': pet.petName, 'icon': pet.petMediaIcon, 'link': 'https://www.wowhead.com/npc={}'.format(pet.petNpcId)})
                else:
                    pets[pet.petSource]['uncollected'].append({'name': pet.petName, 'icon': pet.petMediaIcon, 'link': 'https://www.wowhead.com/npc={}'.format(pet.petNpcId)})
            known = 0
            unknown = 0
            available = 0
            for category_name, category_data in pets.items():
                collected = len(category_data['collected'])
                uncollected = len(category_data['uncollected'])
                total = collected + uncollected
                pets[category_name]['collected_count'] = collected
                pets[category_name]['uncollected_count'] = uncollected
                pets[category_name]['total_count'] = total
                known += collected
                unknown += uncollected
                available += total
                # if collected == 0:
                #     pets[category_name]['collected'].append({'name': 'MoWasEre', 'icon': 'placeholder'})
                #     known += 1
                # if uncollected == 0:
                #     pets[category_name]['uncollected'].append({'name': 'MoWasEre', 'icon': 'placeholder'})
                #     unknown += 1

            queryset = list(pets.items())
            queryset.append(known)
            queryset.append(unknown)
            queryset.append(available)
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
            fields = ['altId', 'altAccountId', 'altLevel', 'altName', 'altRealm', 'altRealmId', 'altRealmSlug', 'altClass', 'get_altClass_display', 'altRace', 'get_altRace_display', 'altGender', 'altFaction']
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
            fields = ['.altName', '.altRealm', '.get_altClass_display', 'profession1', 'get_profession1_display', 'profession2', 'get_profession2_display']
        alts = []
        for alt in queryset:
            temp = []
            for field in fields:
                if '.' in field and '_' in field:
                    temp.append(getattr(alt.alt, field[1:])())
                elif '_' in field:
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
            alt = ProfileAlt.objects.filter(altName=request.query_params.get('alt').title(), altRealmSlug=request.query_params.get('realm'))[:1]
            profession = DataProfession.objects.filter(professionName=request.query_params.get('profession').title())[:1]
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
            fields = ['.altName', '.altRealm', '.get_altClass_display', 'head', 'neck', 'shoulder', 'back', 'chest', 'tabard', 'shirt', 'wrist', 'hands', 'belt', 'legs', 'feet', 'ring1', 'ring2', 'trinket1', 'trinket2', 'weapon1', 'weapon2']
        alts = []
        for alt in queryset:
            avg_level = []
            temp = []
            for field in fields:
                if '.' in field:
                    if '_' in field:
                        temp.append(getattr(alt.alt, field[1:])())
                    else:
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
            temp.insert(3, '{0:.2f}'.format(avg_level))
            alts.append(temp)
        return response.Response(sorted(alts, key=lambda x: float(x[3]), reverse=True))


class BnetLogin(viewsets.ViewSet):
    def create(self, request):
        if request.data.get('state') == 'blizzardeumz76c':
            url = 'https://eu.battle.net/oauth/token?grant_type=authorization_code'
            params = {'client_id': request.data.get('client_id'), 'client_secret': BLIZZ_SECRET, 'code': request.data.get('code'), 'redirect_uri': env("BLIZZ_REDIRECT_URI")}
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
                            userId=result,
                            userFile='',
                            userLastUpdate=timezone.now()
                        )
                    altId = []
                    test1 = y.json()['wow_accounts']
                    for key1 in test1:
                        test = key1['characters']
                        account = key1['id']
                        for key in test:
                            altId.append(key['id'])
                            try:
                                obj = ProfileAlt.objects.get(altId=key['id'])
                                obj.altAccountId = account
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
                                    altAccountId=account,
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


line_data_regex = re.compile(r'^\s*(.*?),?(?: -- \[\d+\])?$')
key_value_regex = re.compile(r'^\[(.*?)\] = (.*?)?$')
index_count = 0

def recursive():
    global index_count
    s_type = 'list'
    result = []
    print(index_count)
    while index_count < len(all_lines):
        index_count = index_count + 1
        line_data = re.search(line_data_regex, all_lines[index_count])
        if not line_data:
            sys.exit('bad input on some line')
        line_single = line_data.group(1)
        if line_single == '{':
            return_text = recursive()
            if return_text[1] != '[]':
                result.append(return_text[1])
            continue
        if line_single == '}':
            break
        key_value_data = re.search(key_value_regex, line_single)
        if key_value_data:
            s_type = 'dict'
            key_single = key_value_data.group(1)
            value_single = key_value_data.group(2)
            if key_single[0] != '"':
                key_single = '"{}"'.format(key_single)
            if value_single == '{':
                return_text = recursive()
                if return_text[1] != '[]':
                    result.append('{}:{}'.format(key_single, return_text[1]))
                continue
            if value_single == '}':
                break
            result.append('{}:{}'.format(key_single, value_single))
        else:
            result.append(line_single)
    if s_type == 'list':
        return (s_type, '[{}]'.format(','.join(result)))
    else:
        return (s_type, '{{{}}}'.format(','.join(result)))


##########################################################################################
# class FileUpload(viewsets.ViewSet):
#     def create(self, request):
#         print(request.data.get('file'))
#         user_file = request.data.get('file')
#         file_name = str(user_file)
#         with open("media/uploads/{}".format(file_name), 'wb+') as f:
#             for chunk in user_file.chunks():
#                 f.write(chunk)
#         return response.Response('yes')
##########################################################################################
