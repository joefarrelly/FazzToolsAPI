from django.shortcuts import render, redirect
from rest_framework import viewsets, views, response
from .serializers import FazzToolsUserSerializer, AltSerializer, ProfessionSerializer, ProfessionTierSerializer, ProfessionRecipeSerializer, AltProfessionSerializer, AltProfessionDataSerializer, EquipmentSerializer, EquipmentVariantSerializer, AltEquipmentSerializer
from .models import FazzToolsUser, Alt, Profession, ProfessionTier, ProfessionRecipe, AltProfession, AltProfessionData, Equipment, EquipmentVariant, AltEquipment
import requests
from django.utils import timezone
import datetime
import hashlib
import hmac
from ratelimit import limits, sleep_and_retry

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

    def list(self, request):
        user = request.query_params.get('user')
        fields = request.query_params.getlist('fields[]')
        queryset = Alt.objects.all()
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

    def list(self, request):
        user = request.query_params.get('user')
        fields = request.query_params.getlist('fields[]')
        queryset = Alt.objects.filter(user=user).values_list('altId', flat=True)
        if user is None:
            queryset = {}
        else:
            queryset = AltProfession.objects.filter(alt__in=queryset).select_related('alt').order_by('-alt__altLevel')
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


class AltProfessionDataView(viewsets.ModelViewSet):
    serializer_class = AltProfessionDataSerializer
    queryset = AltProfessionData.objects.all()

    def list(self, request):
        if request.query_params.get('alt') is not None:
            tiers = {}
            alt = Alt.objects.filter(altName=request.query_params.get('alt'), altRealm=request.query_params.get('realm'))[:1]
            profession = Profession.objects.filter(professionName=request.query_params.get('profession'))[:1]
            queryset = AltProfessionData.objects.select_related('profession', 'professionTier', 'professionRecipe').all()
            queryset = queryset.filter(alt=alt[0].altId, profession=profession[0].professionId)
            for entry in queryset:
                # print(entry)
                try:
                    tiers[entry.professionTier.tierName].append([entry.professionRecipe.recipeName, entry.professionRecipe.recipeRank, entry.professionRecipe.recipeCraftedQuantity])
                except KeyError:
                    tiers[entry.professionTier.tierName] = [[entry.professionRecipe.recipeName, entry.professionRecipe.recipeRank, entry.professionRecipe.recipeCraftedQuantity]]
            queryset = list(map(list, tiers.items()))
            # print(queryset)
            for key, value in queryset:
                value = value.sort()
            if 'Shadowlands' in queryset[-1][0]:
                queryset.insert(0, queryset.pop())
        else:
            queryset = {}
        return response.Response(queryset)


class EquipmentView(viewsets.ModelViewSet):
    serializer_class = EquipmentSerializer
    queryset = Equipment.objects.all()


class EquipmentVariantView(viewsets.ModelViewSet):
    serializer_class = EquipmentVariantSerializer
    queryset = EquipmentVariant.objects.all()


class AltEquipmentView(viewsets.ModelViewSet):
    serializer_class = AltEquipmentSerializer
    queryset = AltEquipment.objects.all()

    def list(self, request):
        user = request.query_params.get('user')
        fields = request.query_params.getlist('fields[]')
        queryset = Alt.objects.filter(user=user).values_list('altId', flat=True)
        extra_queryset = EquipmentVariant.objects.all()
        if user is None:
            queryset = {}
        else:
            queryset = AltEquipment.objects.filter(alt__in=queryset).select_related('alt').order_by('-alt__altLevel')
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
    @sleep_and_retry
    @limits(calls=100, period=1)
    def create(self, request):
        # print(request.data)
        if request.data.get('altId') or request.data.get('userid'):
            alts = []
            if request.data.get('altId'):
                alts.append(request.data.get('altId'))
            elif request.data.get('userid'):
                all_alts = Alt.objects.all()
                old_alts = all_alts.filter(user=request.data.get('userid'))
                for alt in old_alts:
                    alts.append(alt.altId)
            total = len(alts)
            for index, alt in enumerate(alts, start=1):
                print('Processing: {} of {}'.format(index, total))
                alt_obj = Alt.objects.get(altId=alt)
                # if alt_obj.altName != 'Fazziest':
                #     continue
                realm = alt_obj.altRealmSlug
                name = alt_obj.altName.lower()
                url = 'https://eu.battle.net/oauth/token?grant_type=client_credentials'
                params = {'client_id': BLIZZ_CLIENT, 'client_secret': BLIZZ_SECRET}
                x = requests.post(url, data=params)
                try:
                    token = x.json()['access_token']
                    urls = [
                        'https://eu.api.blizzard.com/profile/wow/character/' + realm + '/' + name + '/professions',
                        'https://eu.api.blizzard.com/profile/wow/character/' + realm + '/' + name + '/equipment'
                    ]
                    myobj = {'access_token': token, 'namespace': 'profile-eu', 'locale': 'en_US'}
                    dataobj = {'access_token': token, 'locale': 'en_US'}
                    for url in urls:
                        y = requests.get(url, params=myobj)
                        if y.status_code == 200:
                            if 'professions' in url:
                                print('profession pending')
                                alt_profs = []
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
                                            # print(tier['tier']['name'])
                                            # print(len(prof['tiers']))
                                            try:
                                                obj1 = ProfessionTier.objects.get(tierId=tier['tier']['id'])
                                            except ProfessionTier.DoesNotExist:
                                                obj1 = ProfessionTier.objects.create(
                                                    profession=obj,
                                                    tierId=tier['tier']['id'],
                                                    tierName=tier['tier']['name']
                                                )
                                            try:
                                                for recipe in tier['known_recipes']:
                                                    try:
                                                        obj2 = ProfessionRecipe.objects.get(recipeId=recipe['id'])
                                                    except ProfessionRecipe.DoesNotExist:
                                                        try:
                                                            z = requests.get(recipe['key']['href'], params=dataobj)
                                                            recipeData = z.json()
                                                        except Exception as e:
                                                            print(e)
                                                        # print(recipeData['rank'])
                                                        # print(recipeData['crafted_quantity']['value'])
                                                        try:
                                                            rank = recipeData['rank']
                                                        except Exception:
                                                            rank = 1
                                                        try:
                                                            quantity = recipeData['crafted_quantity']['value']
                                                        except Exception:
                                                            quantity = 1
                                                        obj2 = ProfessionRecipe.objects.create(
                                                            professionTier=obj1,
                                                            recipeId=recipe['id'],
                                                            recipeName=recipe['name'],
                                                            recipeRank=rank,
                                                            recipeCraftedQuantity=quantity
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
                                            except KeyError as e:
                                                pass
                                except KeyError as e:
                                    # print(e)
                                    pass
                                while len(alt_profs) < 2:
                                    alt_profs.append(0)
                                old_alt_profs = [prof_obj.profession1, prof_obj.profession2]
                                for prof in old_alt_profs:
                                    if prof not in alt_profs:
                                        # print('{} : changes'.format(prof))
                                        AltProfessionData.objects.filter(alt=prof_obj, profession=prof).delete()
                                # obj4 = AltProfession.objects.get(alt=alt_obj)
                                prof_obj.profession1 = alt_profs[0]
                                prof_obj.profession2 = alt_profs[1]
                                prof_obj.altProfessionExpiryDate = timezone.now() + datetime.timedelta(days=30)
                                prof_obj.save()
                            elif 'equipment' in url:
                                print('equipment pending')
                                alt_equipment = {}
                                try:
                                    alt_equip_obj = AltEquipment.objects.get(alt=alt_obj)
                                except AltEquipment.DoesNotExist:
                                    alt_equip_obj = AltEquipment.objects.create(
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
                                            obj = Equipment.objects.get(equipmentId=item['item']['id'])
                                        except Equipment.DoesNotExist:
                                            obj = Equipment.objects.create(
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
                                            obj1 = EquipmentVariant.objects.get(equipment=obj, variant=variantCode)
                                        except EquipmentVariant.DoesNotExist:
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
                                            obj1 = EquipmentVariant.objects.create(
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

                                        # if average_item_level_dict['OFF_HAND'] == 0:
                                            # average_item_level_dict['OFF_HAND'] = average_item_level_dict['MAIN_HAND']
                                        # average_item_level = sum(average_item_level_dict.values()) / 16

                                        # try:
                                        #     obj2 = AltEquipmentData.objects.get(alt=alt_equip_obj, equipmentVariant=obj1)
                                        #     obj2.altEquipmentDataExpiryDate = timezone.now() + datetime.timedelta(days=30)
                                        #     obj2.save()
                                        # except AltEquipmentData.DoesNotExist:
                                        #     obj2 = AltEquipmentData.objects.create(
                                        #         alt=alt_equip_obj,
                                        #         equipmentVariant=obj1,
                                        #         altEquipmentDataExpiryDate=timezone.now() + datetime.timedelta(days=30)
                                        #     )
                                        alt_equipment[item['slot']['name'].lower()] = str(item['item']['id']) + ':' + variantCode
                                except KeyError as e:
                                    print(e)
                                # print(alt_equipment)
                                # while len(alt_profs) < 2:
                                #     alt_profs.append(0)
                                # old_alt_profs = [prof_obj.profession1, prof_obj.profession2]
                                # for prof in old_alt_profs:
                                #     if prof not in alt_profs:
                                #         print('{} : changes'.format(prof))
                                #         AltProfessionData.objects.filter(alt=prof_obj, profession=prof).delete()
                                # obj3 = AltEquipment.objects.get(alt=alt_obj)
                                # print(alt_equip_obj.head)
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
                                # print(alt_equip_obj.head)
                                # print('###########')
                                # print(alt_equip_obj.shirt)
                                # setattr(alt_equip_obj, 'shirt', alt_equipment.get('shirt') or 0)
                                # print(alt_equip_obj.shirt)
                                alt_equip_obj.save()
                                # print('### Processing ###')
                                # alt_equip_obj.head = alt_profs[0]
                                # alt_equip_obj.neck = alt_profs[1]
                                # alt_equip_obj.altProfessionExpiryDate = timezone.now() + datetime.timedelta(days=30)
                                # alt_equip_obj.save()
                            else:
                                print('donebutnotdone')
                except Exception as e:
                    print(e)
            return response.Response(timezone.now())
        return response.Response('nouser')
