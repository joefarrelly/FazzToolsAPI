import datetime
import hashlib
import hmac
import logging
import os
import re
import string
import time

import environ
import requests
from django.utils import timezone
from requests.adapters import HTTPAdapter
from rest_framework import response, viewsets
from urllib3.util.retry import Retry

from apicore.libs.keybind_mapping import getKeybindMap
from apicore.libs.lua_parser import LuaParser
from apicore.models import (
    DataEquipment,
    DataEquipmentVariant,
    DataMount,
    DataPet,
    DataProfession,
    DataProfessionRecipe,
    DataProfessionTier,
    DataReagent,
    DataRecipeReagent,
    ProfileAlt,
    ProfileAltEquipment,
    ProfileAltProfession,
    ProfileAltProfessionData,
    ProfileUser,
    ProfileUserMount,
    ProfileUserPet,
)
from apicore.serializers import (
    DataEquipmentSerializer,
    DataEquipmentVariantSerializer,
    DataMountSerializer,
    DataPetSerializer,
    DataProfessionRecipeSerializer,
    DataProfessionSerializer,
    DataProfessionTierSerializer,
    DataReagentSerializer,
    DataRecipeReagentSerializer,
    ProfileAltEquipmentSerializer,
    ProfileAltProfessionDataSerializer,
    ProfileAltProfessionSerializer,
    ProfileAltSerializer,
    ProfileUserMountSerializer,
    ProfileUserPetSerializer,
    ProfileUserSerializer,
)
from apicore.tasks import fullAltScan, fullDataScan

logger = logging.getLogger(__name__)

env = environ.Env()
environ.Env.read_env()

HASH_KEY = env("HASH_KEY").encode()
BLIZZ_CLIENT = env("BLIZZ_CLIENT")
BLIZZ_SECRET = env("BLIZZ_SECRET")

_session = requests.Session()
_session.mount("https://", HTTPAdapter(max_retries=Retry(total=3, backoff_factor=1)))


# ---------------------------------------------------------------------------
# Data (static) views
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Profile views
# ---------------------------------------------------------------------------


class ProfileUserView(viewsets.ModelViewSet):
    serializer_class = ProfileUserSerializer
    queryset = ProfileUser.objects.all()

    def perform_update(self, serializer):
        user_id = serializer.validated_data.get("user_id")
        file = serializer.validated_data.get("user_file")

        logger.info("File upload attempt: %s", file.name)

        if file.name != "FazzToolsScraper.lua":
            logger.warning("Rejected upload: wrong filename %s", file.name)
            return

        if file.size >= 10_000_000:
            logger.warning("Rejected upload: file too large (%d bytes)", file.size)
            return

        file.name = user_id + ".lua"
        f = file.open("r+")
        content = f.read().decode("utf-8")

        if "FazzToolsScraperDB" not in content[0:25]:
            logger.warning("Rejected upload: invalid file header")
            f.close()
            return

        normalised = re.sub(r'(\r\n|\r|\n)(?=(?:[^"]*"[^"]*")*[^"]*$)', r"\n", content)
        f.seek(0)
        f.write(normalised.encode())
        f.truncate()
        f.close()

        user_obj = ProfileUser.objects.get(user_id=user_id)
        update_date = user_obj.user_last_update

        try:
            if user_obj.user_file:
                os.remove(user_obj.user_file.path)
        except OSError as exc:
            logger.warning("Could not remove old file: %s", exc)

        serializer.save(user_id=user_id, user_file=file, user_last_update=update_date)

    def list(self, request):
        user_id = request.query_params.get("user")
        page = request.query_params.get("page")

        if user_id is None or page is None:
            return response.Response("hey")

        try:
            user_obj = ProfileUser.objects.get(user_id=user_id)
        except ProfileUser.DoesNotExist:
            return response.Response([])

        if page == "header":
            ts = time.mktime(user_obj.user_last_update.timetuple()) * 1000
            return response.Response([ts])

        if not user_obj.user_file:
            return response.Response([])

        lines = [line.decode("utf-8") for line in user_obj.user_file.file.open("r").readlines()]
        user_obj.user_file.file.close()

        data = LuaParser(lines).parse()

        if page == "all":
            return response.Response(_build_all_keybinds(data, user_id))

        if page == "single":
            alt_name = request.query_params.get("alt", "").title()
            realm = string.capwords(request.query_params.get("realm", ""))
            spec = request.query_params.get("spec", "").title()
            return response.Response(_build_single_keybinds(data, alt_name, realm, spec))

        return response.Response([])


def _build_all_keybinds(data: dict, user_id: str) -> list:
    result = []
    for alt_key, alt_config in data.get("alts", {}).items():
        specs = []
        try:
            if alt_config.get("kb") is not None:
                specs = list(alt_config["kb"].keys())
            else:
                specs = ["---", "---", "---", "---"]
        except (KeyError, TypeError):
            specs = ["---", "---", "---", "---"]

        specs.sort()
        while len(specs) < 4:
            specs.append("---")

        name, realm = (alt_key.split("-", 1) + [""])[:2]
        try:
            alt_obj = ProfileAlt.objects.get(alt_name=name, alt_realm=realm)
            row = [name, realm, alt_obj.get_alt_class_display()] + specs
            result.append(row)
        except ProfileAlt.DoesNotExist:
            logger.debug("Alt not in DB: %s", alt_key)

    result.sort(key=lambda x: (x[1], x[0]))
    return result


def _build_single_keybinds(data: dict, alt: str, realm: str, spec: str) -> list:
    alt_key = f"{alt}-{realm}"
    alt_config = data["alts"][alt_key]
    keybind_map = getKeybindMap(alt_config["kbConfig"]["addon"])

    user_keybind: dict[str, str] = {}
    for slot, nice_spell in alt_config["kb"][spec].items():
        prefix = nice_spell.split(":")[0]

        if prefix == "spell":
            try:
                user_keybind[nice_spell] = alt_config["kbConfig"]["map"][keybind_map[int(slot)]]
            except (KeyError, ValueError):
                pass

        elif prefix == "macro":
            macro_name = nice_spell.split(":")[1]
            found = False
            for tab in alt_config.get("spell", {}).get(spec, {}):
                for spell_id, spell_info in alt_config["spell"][spec][tab].items():
                    if spell_info[0] in alt_config["macro"][macro_name][2]:
                        found = True
                        spell_key = f"spell:{spell_id}"
                        try:
                            bound = alt_config["kbConfig"]["map"][keybind_map[int(slot)]]
                        except (KeyError, ValueError):
                            continue
                        if spell_key not in user_keybind:
                            user_keybind[spell_key] = bound
                        elif user_keybind[spell_key] != bound:
                            user_keybind[spell_key] += f" | {bound}"
            if not found:
                try:
                    user_keybind[nice_spell] = alt_config["kbConfig"]["map"][keybind_map[int(slot)]]
                except (KeyError, ValueError):
                    pass

        elif prefix == "item":
            item_name = nice_spell.split(":")[1]
            if item_name in alt_config.get("item", {}):
                try:
                    user_keybind[nice_spell] = alt_config["kbConfig"]["map"][keybind_map[int(slot)]]
                except (KeyError, ValueError):
                    pass

    SPAM_FILTER = {
        "Auto Attack",
        "Mobile Banking",
        "Revive Battle Pets",
        "Vindicaar Matrix Crystal",
        "Shoot",
    }
    SECTION_ORDER = {"Base": 0, "Talent": 1, "Misc": 2}

    full_result = []
    for tab in alt_config.get("spell", {}).get(spec, {}):
        spells = []
        for spell_id, spell_info in alt_config["spell"][spec][tab].items():
            if spell_info[0] in SPAM_FILTER:
                continue
            entry = [spell_info[0]]
            if len(spell_info) > 1:
                entry.append(spell_info[1])
            entry.append(user_keybind.get(f"spell:{spell_id}", "UNBOUND"))
            spells.append(entry)
        spells.sort(key=lambda x: x[0])
        full_result.append([tab.title(), spells])

    misc = []
    for item_name, item_info in alt_config.get("item", {}).items():
        if f"item:{item_name}" in user_keybind:
            misc.append([item_info[0], user_keybind[f"item:{item_name}"]])
    for macro_name, macro_info in alt_config.get("macro", {}).items():
        if f"macro:{macro_name}" in user_keybind:
            misc.append([f"[Macro] {macro_info[0]}", user_keybind[f"macro:{macro_name}"]])
    misc.sort(key=lambda x: x[0])
    full_result.append(["Misc", misc])

    full_result.sort(key=lambda x: SECTION_ORDER.get(x[0], 99))

    if len(full_result) >= 2:
        full_result[0][1] = [x for x in full_result[0][1] if x not in full_result[1][1]]

    return full_result


class ProfileUserMountView(viewsets.ModelViewSet):
    serializer_class = ProfileUserMountSerializer
    queryset = ProfileUserMount.objects.all()

    def list(self, request):
        user_id = request.query_params.get("user")
        if user_id is None:
            return response.Response([])

        collected_ids = set(
            ProfileUserMount.objects.filter(user=user_id).values_list("mount__mount_id", flat=True)
        )

        mounts: dict[str, dict] = {}
        for mount in DataMount.objects.all().order_by("mount_name"):
            bucket = mounts.setdefault(
                mount.mount_source,
                {
                    "collected": [],
                    "uncollected": [],
                },
            )
            entry = {"name": mount.mount_name, "icon": mount.mount_media_icon}
            if mount.mount_id in collected_ids:
                bucket["collected"].append(entry)
            else:
                bucket["uncollected"].append(entry)

        known = unknown = available = 0
        for source, bucket in mounts.items():
            n_collected = len(bucket["collected"])
            n_uncollected = len(bucket["uncollected"])
            bucket["collected_count"] = n_collected
            bucket["uncollected_count"] = n_uncollected
            bucket["total_count"] = n_collected + n_uncollected
            known += n_collected
            unknown += n_uncollected
            available += n_collected + n_uncollected

        result = list(mounts.items())
        result.extend([known, unknown, available])
        return response.Response(result)


class ProfileUserPetView(viewsets.ModelViewSet):
    serializer_class = ProfileUserPetSerializer
    queryset = ProfileUserPet.objects.all()

    def list(self, request):
        user_id = request.query_params.get("user")
        if user_id is None:
            return response.Response([])

        collected_ids = set(
            ProfileUserPet.objects.filter(user=user_id).values_list("pet__pet_id", flat=True)
        )

        pets: dict[str, dict] = {}
        for pet in DataPet.objects.all().order_by("pet_name"):
            bucket = pets.setdefault(
                pet.pet_source,
                {
                    "collected": [],
                    "uncollected": [],
                },
            )
            entry = {
                "name": pet.pet_name,
                "icon": pet.pet_media_icon,
                "link": f"https://www.wowhead.com/npc={pet.pet_npc_id}",
            }
            if pet.pet_id in collected_ids:
                bucket["collected"].append(entry)
            else:
                bucket["uncollected"].append(entry)

        known = unknown = available = 0
        for source, bucket in pets.items():
            n_collected = len(bucket["collected"])
            n_uncollected = len(bucket["uncollected"])
            bucket["collected_count"] = n_collected
            bucket["uncollected_count"] = n_uncollected
            bucket["total_count"] = n_collected + n_uncollected
            known += n_collected
            unknown += n_uncollected
            available += n_collected + n_uncollected

        result = list(pets.items())
        result.extend([known, unknown, available])
        return response.Response(result)


class ProfileAltView(viewsets.ModelViewSet):
    serializer_class = ProfileAltSerializer
    queryset = ProfileAlt.objects.all()

    def list(self, request):
        user_id = request.query_params.get("user")
        fields = request.query_params.getlist("fields[]")

        if user_id is None:
            return response.Response([])

        queryset = ProfileAlt.objects.filter(user=user_id).order_by("-alt_level")

        if not fields or fields[0] == "":
            fields = [
                "alt_id",
                "alt_account_id",
                "alt_level",
                "alt_name",
                "alt_realm",
                "alt_realm_id",
                "alt_realm_slug",
                "alt_class",
                "get_alt_class_display",
                "alt_race",
                "get_alt_race_display",
                "alt_gender",
                "alt_faction",
            ]

        alts = []
        for alt in queryset:
            row = []
            for field in fields:
                value = getattr(alt, field)
                row.append(value() if callable(value) else value)
            alts.append(row)
        return response.Response(alts)


class ProfileAltProfessionView(viewsets.ModelViewSet):
    serializer_class = ProfileAltProfessionSerializer
    queryset = ProfileAltProfession.objects.all()

    def list(self, request):
        user_id = request.query_params.get("user")
        fields = request.query_params.getlist("fields[]")

        if user_id is None:
            return response.Response([])

        alt_ids = ProfileAlt.objects.filter(user=user_id).values_list("alt_id", flat=True)
        queryset = (
            ProfileAltProfession.objects.filter(alt__in=alt_ids)
            .select_related("alt")
            .order_by("-alt__alt_level")
        )

        if not fields or fields[0] == "":
            fields = [
                ".alt_name",
                ".alt_realm",
                ".get_alt_class_display",
                "profession_1",
                "get_profession_1_display",
                "profession_2",
                "get_profession_2_display",
            ]

        alts = []
        for entry in queryset:
            row = []
            for field in fields:
                if field.startswith("."):
                    attr = getattr(entry.alt, field[1:])
                else:
                    attr = getattr(entry, field)
                row.append(attr() if callable(attr) else attr)
            alts.append(row)
        return response.Response(alts)


class ProfileAltProfessionDataView(viewsets.ModelViewSet):
    serializer_class = ProfileAltProfessionDataSerializer
    queryset = ProfileAltProfessionData.objects.all()

    def list(self, request):
        alt_name = request.query_params.get("alt")
        if alt_name is None:
            return response.Response({})

        alt = ProfileAlt.objects.filter(
            alt_name=alt_name.title(),
            alt_realm_slug=request.query_params.get("realm"),
        ).first()
        profession = DataProfession.objects.filter(
            profession_name=request.query_params.get("profession", "").title()
        ).first()

        if alt is None or profession is None:
            return response.Response({})

        queryset = ProfileAltProfessionData.objects.select_related(
            "profession", "profession_tier", "profession_recipe"
        ).filter(alt=alt.alt_id, profession=profession.profession_id)

        tiers: dict[str, dict] = {}
        for entry in queryset:
            tier_bucket = tiers.setdefault(entry.profession_tier.tier_name, {})
            category_list = tier_bucket.setdefault(entry.profession_recipe.recipe_category, [])

            mats = [
                [
                    r.reagent.reagent_name,
                    r.quantity,
                    r.reagent.reagent_media,
                    r.reagent.reagent_quality,
                ]
                for r in DataRecipeReagent.objects.select_related("reagent").filter(
                    recipe=entry.profession_recipe
                )
            ]
            recipe_row = [
                entry.profession_recipe.recipe_name,
                entry.profession_recipe.recipe_rank,
                entry.profession_recipe.recipe_crafted_quantity,
                *mats,
            ]
            category_list.append(recipe_row)

        result = [[tier_name, list(cats.items())] for tier_name, cats in tiers.items()]

        if result and "Shadowlands" in result[-1][0]:
            result.insert(0, result.pop())

        return response.Response(result)


class ProfileAltEquipmentView(viewsets.ModelViewSet):
    serializer_class = ProfileAltEquipmentSerializer
    queryset = ProfileAltEquipment.objects.all()

    def list(self, request):
        page = request.query_params.get("page")

        if page == "all":
            return self._list_all(request)
        if page == "single":
            return self._list_single(request)
        return response.Response([])

    def _list_all(self, request):
        user_id = request.query_params.get("user")
        fields = request.query_params.getlist("fields[]")

        if user_id is None:
            return response.Response([])

        alt_ids = ProfileAlt.objects.filter(user=user_id).values_list("alt_id", flat=True)
        queryset = (
            ProfileAltEquipment.objects.filter(alt__in=alt_ids)
            .select_related("alt")
            .order_by("-alt__alt_level")
        )
        variants = DataEquipmentVariant.objects.all()

        if not fields or fields[0] == "":
            fields = [
                ".alt_name",
                ".alt_realm",
                ".get_alt_class_display",
                "head",
                "neck",
                "shoulder",
                "back",
                "chest",
                "tabard",
                "shirt",
                "wrist",
                "hands",
                "belt",
                "legs",
                "feet",
                "ring1",
                "ring2",
                "trinket1",
                "trinket2",
                "weapon1",
                "weapon2",
            ]

        alts = []
        for entry in queryset:
            row = []
            avg_level = []
            for field in fields:
                if field.startswith("."):
                    attr = getattr(entry.alt, field[1:])
                    row.append(attr() if callable(attr) else attr)
                else:
                    raw = getattr(entry, field)
                    if raw != "0":
                        equip_id, variant_code = raw.split(":", 1)
                        variant = variants.filter(equipment=equip_id, variant=variant_code).first()
                        level = variant.level if variant else 0
                    else:
                        level = 0
                    row.append(level)
                    if field not in ("tabard", "shirt"):
                        avg_level.append(level)

            if avg_level and avg_level[-1] == 0:
                avg_level[-1] = avg_level[-2] if len(avg_level) >= 2 else 0
            avg = sum(avg_level) / 16 if avg_level else 0
            row.insert(3, f"{avg:.2f}")
            alts.append(row)

        return response.Response(sorted(alts, key=lambda x: float(x[3]), reverse=True))

    def _list_single(self, request):
        alt_name = request.query_params.get("alt", "").title()
        realm_slug = request.query_params.get("realm", "")

        alt = ProfileAlt.objects.filter(alt_name=alt_name, alt_realm_slug=realm_slug).first()
        if alt is None:
            return response.Response([])

        try:
            record = ProfileAltEquipment.objects.get(alt=alt)
        except ProfileAltEquipment.DoesNotExist:
            return response.Response([])

        slot_values = [
            record.head,
            record.neck,
            record.shoulder,
            record.back,
            record.chest,
            record.tabard,
            record.shirt,
            record.wrist,
            record.hands,
            record.belt,
            record.legs,
            record.feet,
            record.ring1,
            record.ring2,
            record.trinket1,
            record.trinket2,
            record.weapon1,
            record.weapon2,
        ]

        result = []
        for slot in slot_values:
            parts = slot.split(":", 1)
            if len(parts) == 2:
                equip_obj = DataEquipment.objects.filter(equipment_id=parts[0]).first()
                variant_obj = DataEquipmentVariant.objects.filter(
                    variant=parts[1], equipment=equip_obj
                ).first()
                if equip_obj and variant_obj:
                    result.append([equip_obj.equipment_name, variant_obj.level])
                else:
                    result.append(["None", "0"])
            else:
                result.append(["None", "0"])

        return response.Response(result)


# ---------------------------------------------------------------------------
# Custom endpoints
# ---------------------------------------------------------------------------


class BnetLogin(viewsets.ViewSet):
    def create(self, request):
        if request.data.get("state") != "blizzardeumz76c":
            return response.Response("error")

        token_resp = requests.post(
            "https://eu.battle.net/oauth/token?grant_type=authorization_code",
            data={
                "client_id": request.data.get("client_id"),
                "client_secret": BLIZZ_SECRET,
                "code": request.data.get("code"),
                "redirect_uri": env("BLIZZ_REDIRECT_URI"),
            },
        )

        try:
            token = token_resp.json()["access_token"]
        except KeyError:
            return response.Response(token_resp.text)

        profile_resp = requests.get(
            "https://eu.api.blizzard.com/profile/user/wow",
            params={"namespace": "profile-eu", "locale": "en_US"},
            headers={"Authorization": f"Bearer {token}"},
        )

        if profile_resp.status_code != 200:
            return response.Response(profile_resp.text)

        profile = profile_resp.json()
        user_id = hmac.new(HASH_KEY, str(profile["id"]).encode(), hashlib.sha256).hexdigest()

        user_obj, _ = ProfileUser.objects.get_or_create(
            user_id=user_id,
            defaults={"user_file": "", "user_last_update": timezone.now()},
        )

        alt_ids = []
        for account in profile.get("wow_accounts", []):
            for char in account.get("characters", []):
                alt_ids.append(char["id"])
                ProfileAlt.objects.update_or_create(
                    alt_id=char["id"],
                    defaults={
                        "alt_account_id": account["id"],
                        "alt_level": char["level"],
                        "alt_name": char["name"],
                        "alt_realm": char["realm"]["name"],
                        "alt_realm_id": char["realm"]["id"],
                        "alt_realm_slug": char["realm"]["slug"],
                        "alt_class": char["playable_class"]["id"],
                        "alt_race": char["playable_race"]["id"],
                        "alt_gender": char["gender"]["name"],
                        "alt_faction": char["faction"]["name"],
                        "alt_expiry_date": timezone.now() + datetime.timedelta(days=30),
                        "user": user_obj,
                    },
                )

        return response.Response({"user": user_id, "alts": alt_ids})


class ScanAlt(viewsets.ViewSet):
    def create(self, request):
        user_id = request.data.get("userid")
        if not user_id:
            return response.Response("nouser")
        fullAltScan.delay(user_id, BLIZZ_CLIENT, BLIZZ_SECRET)
        return response.Response(timezone.now())


class DataScan(viewsets.ViewSet):
    def create(self, request):
        if request.data.get("password") != env("DATA_PASSWORD"):
            return response.Response("Incorrect Password")
        fullDataScan.delay(BLIZZ_CLIENT, BLIZZ_SECRET)
        return response.Response("Password Correct")
