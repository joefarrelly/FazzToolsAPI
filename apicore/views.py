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
from django.core.cache import cache
from django.db import models
from django.utils import timezone
from requests.adapters import HTTPAdapter
from rest_framework import response, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAdminUser
from urllib3.util.retry import Retry

from apicore.libs.keybind_builder import build_all_keybinds, build_single_keybinds, tier_sort_key
from apicore.libs.lua_parser import LuaParser
from apicore.models import (
    DataAchievement,
    DataEquipment,
    DataEquipmentVariant,
    DataFaction,
    DataMount,
    DataPet,
    DataProfession,
    DataProfessionRecipe,
    DataProfessionTier,
    DataReagent,
    DataRecipeReagent,
    ProfileAlt,
    ProfileAltAchievement,
    ProfileAltEquipment,
    ProfileAltProfession,
    ProfileAltProfessionData,
    ProfileAltReputation,
    ProfileUser,
    ProfileUserMount,
    ProfileUserPet,
)
from apicore.permissions import IsSessionUser
from apicore.serializers import (
    DataAchievementSerializer,
    DataEquipmentSerializer,
    DataEquipmentVariantSerializer,
    DataFactionSerializer,
    DataMountSerializer,
    DataPetSerializer,
    DataProfessionRecipeSerializer,
    DataProfessionSerializer,
    DataProfessionTierSerializer,
    DataReagentSerializer,
    DataRecipeReagentSerializer,
    ProfileAltAchievementSerializer,
    ProfileAltEquipmentSerializer,
    ProfileAltProfessionDataSerializer,
    ProfileAltProfessionSerializer,
    ProfileAltReputationSerializer,
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

    def get_permissions(self):
        if self.action == "list":
            return [IsSessionUser()]
        return []

    def perform_update(self, serializer):
        user_id = serializer.validated_data.get("user_id")
        if self.request.session.get("user_id") != user_id:
            raise PermissionDenied()
        file = serializer.validated_data.get("user_file")

        logger.info("File upload attempt: %s", file.name)

        if file.name != "FazzToolsScraper.lua":
            logger.warning("Rejected upload: wrong filename %s", file.name)
            return

        if file.size >= 10_000_000:
            logger.warning("Rejected upload: file too large (%d bytes)", file.size)
            return

        file.name = user_id + ".lua"
        with file.open("r+") as f:
            content = f.read().decode("utf-8")

            if "FazzToolsScraperDB" not in content[0:25]:
                logger.warning("Rejected upload: invalid file header")
                return

            normalised = re.sub(r'(\r\n|\r|\n)(?=(?:[^"]*"[^"]*")*[^"]*$)', r"\n", content)
            f.seek(0)
            f.write(normalised.encode())
            f.truncate()

        user_obj = ProfileUser.objects.get(user_id=user_id)
        update_date = user_obj.user_last_update

        try:
            if user_obj.user_file:
                os.remove(user_obj.user_file.path)
        except OSError as exc:
            logger.warning("Could not remove old file: %s", exc)

        serializer.save(user_id=user_id, user_file=file, user_last_update=update_date)
        cache.delete(f"keybinds:{user_id}")

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

        cache_key = f"keybinds:{user_id}"
        data = cache.get(cache_key)
        if data is None:
            with user_obj.user_file.open("r") as f:
                lines = [line.decode("utf-8") for line in f.readlines()]
            data = LuaParser(lines).parse()
            cache.set(cache_key, data, timeout=None)

        if page == "all":
            return response.Response(build_all_keybinds(data, user_id))

        if page == "single":
            alt_name = request.query_params.get("alt", "").title()
            realm = string.capwords(request.query_params.get("realm", ""))
            spec = request.query_params.get("spec", "").title()
            return response.Response(build_single_keybinds(data, alt_name, realm, spec))

        return response.Response([])


class ProfileUserMountView(viewsets.ModelViewSet):
    serializer_class = ProfileUserMountSerializer
    queryset = ProfileUserMount.objects.all()
    permission_classes = [IsSessionUser]

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
    permission_classes = [IsSessionUser]

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
    permission_classes = [IsSessionUser]

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
    permission_classes = [IsSessionUser]

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

        if alt.user_id != request.session.get("user_id"):
            return response.Response({}, status=403)

        learned_ids = set(
            ProfileAltProfessionData.objects.filter(
                alt=alt.alt_id, profession=profession.profession_id
            ).values_list("profession_recipe_id", flat=True)
        )

        profession_tiers = DataProfessionTier.objects.filter(profession=profession)
        recipes = (
            DataProfessionRecipe.objects.filter(tier__in=profession_tiers)
            .select_related("tier")
            .prefetch_related(
                models.Prefetch(
                    "datarecipereagent_set",
                    queryset=DataRecipeReagent.objects.select_related("reagent"),
                )
            )
            .order_by("recipe_name")
        )

        # One entry per (tier, category, name) family — highest learned rank wins,
        # falling back to lowest unlearned rank if nothing is learned.
        families: dict[tuple[str, str, str], tuple[object, bool]] = {}
        for recipe in recipes:
            family_key = (recipe.tier.tier_name, recipe.recipe_category, recipe.recipe_name)
            is_learned = recipe.recipe_id in learned_ids
            if family_key not in families:
                families[family_key] = (recipe, is_learned)
            else:
                existing_recipe, existing_learned = families[family_key]
                if is_learned and not existing_learned:
                    families[family_key] = (recipe, True)
                elif is_learned == existing_learned and (
                    recipe.recipe_rank > existing_recipe.recipe_rank
                ):
                    families[family_key] = (recipe, is_learned)

        tiers: dict[str, dict] = {}
        for (tier_name, category, _), (recipe, is_learned) in families.items():
            tier_bucket = tiers.setdefault(tier_name, {})
            category_list = tier_bucket.setdefault(category, [])

            mats = [
                [
                    r.reagent.reagent_name,
                    r.quantity,
                    r.reagent.reagent_media,
                    r.reagent.reagent_quality,
                ]
                for r in recipe.datarecipereagent_set.all()
            ]
            recipe_row = [
                recipe.recipe_name,
                is_learned,
                recipe.recipe_rank,
                recipe.recipe_crafted_quantity,
                recipe.recipe_icon,
                *mats,
            ]
            category_list.append(recipe_row)

        result = [
            [tier_name, sorted(cats.items())]
            for tier_name, cats in sorted(
                tiers.items(), key=lambda x: tier_sort_key(x[0]), reverse=True
            )
        ]

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

        if request.session.get("user_id") != user_id:
            return response.Response([], status=403)

        alt_ids = ProfileAlt.objects.filter(user=user_id).values_list("alt_id", flat=True)
        queryset = (
            ProfileAltEquipment.objects.filter(alt__in=alt_ids)
            .select_related("alt")
            .order_by("-alt__alt_level")
        )
        variant_map = {
            (str(v.equipment_id), v.variant): v for v in DataEquipmentVariant.objects.all()
        }

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
                        variant = variant_map.get((equip_id, variant_code))
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

        if alt.user_id != request.session.get("user_id"):
            return response.Response([], status=403)

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

        slot_pairs = [s.split(":", 1) if ":" in s else None for s in slot_values]
        equip_ids = {p[0] for p in slot_pairs if p}
        equip_map = {
            str(e.equipment_id): e for e in DataEquipment.objects.filter(equipment_id__in=equip_ids)
        }
        variant_map = {
            (str(v.equipment_id), v.variant): v
            for v in DataEquipmentVariant.objects.filter(equipment_id__in=equip_ids)
        }

        result = []
        for parts in slot_pairs:
            if parts:
                equip_obj = equip_map.get(parts[0])
                variant_obj = variant_map.get((parts[0], parts[1]))
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

        request.session["user_id"] = user_id

        return response.Response({"user": user_id, "alts": alt_ids})


class DataAchievementView(viewsets.ModelViewSet):
    serializer_class = DataAchievementSerializer
    queryset = DataAchievement.objects.all()


class DataFactionView(viewsets.ModelViewSet):
    serializer_class = DataFactionSerializer
    queryset = DataFaction.objects.all()


class ProfileAltAchievementView(viewsets.ModelViewSet):
    serializer_class = ProfileAltAchievementSerializer
    queryset = ProfileAltAchievement.objects.all()

    def list(self, request):
        user_id = request.query_params.get("user")
        alt_name = request.query_params.get("alt", "").title()
        realm_slug = request.query_params.get("realm", "")

        if not user_id:
            return response.Response([])
        if request.session.get("user_id") != user_id:
            return response.Response([], status=403)

        if alt_name and realm_slug:
            alt = ProfileAlt.objects.filter(
                alt_name=alt_name, alt_realm_slug=realm_slug, user=user_id
            ).first()
            if not alt:
                return response.Response([])
            qs = (
                ProfileAltAchievement.objects.filter(alt=alt)
                .select_related("achievement")
                .order_by("-completed_timestamp")
            )
        else:
            alt_ids = ProfileAlt.objects.filter(user=user_id).values_list("alt_id", flat=True)
            qs = (
                ProfileAltAchievement.objects.filter(alt__in=alt_ids)
                .select_related("alt", "achievement")
                .order_by("alt__alt_name", "-completed_timestamp")
            )

        serializer = self.get_serializer(qs, many=True)
        return response.Response(serializer.data)


class ProfileAltReputationView(viewsets.ModelViewSet):
    serializer_class = ProfileAltReputationSerializer
    queryset = ProfileAltReputation.objects.all()

    def list(self, request):
        user_id = request.query_params.get("user")
        alt_name = request.query_params.get("alt", "").title()
        realm_slug = request.query_params.get("realm", "")

        if not user_id:
            return response.Response([])
        if request.session.get("user_id") != user_id:
            return response.Response([], status=403)

        if alt_name and realm_slug:
            alt = ProfileAlt.objects.filter(
                alt_name=alt_name, alt_realm_slug=realm_slug, user=user_id
            ).first()
            if not alt:
                return response.Response([])
            qs = (
                ProfileAltReputation.objects.filter(alt=alt)
                .select_related("faction")
                .order_by("-standing_value")
            )
        else:
            alt_ids = ProfileAlt.objects.filter(user=user_id).values_list("alt_id", flat=True)
            qs = (
                ProfileAltReputation.objects.filter(alt__in=alt_ids)
                .select_related("alt", "faction")
                .order_by("alt__alt_name", "-standing_value")
            )

        serializer = self.get_serializer(qs, many=True)
        return response.Response(serializer.data)


class ScanAlt(viewsets.ViewSet):
    def create(self, request):
        user_id = request.data.get("userid")
        if not user_id:
            return response.Response("nouser")
        if request.session.get("user_id") != user_id:
            return response.Response("forbidden", status=403)
        fullAltScan.delay(user_id, BLIZZ_CLIENT, BLIZZ_SECRET)
        return response.Response(timezone.now())


class DataScan(viewsets.ViewSet):
    permission_classes = [IsAdminUser]

    def create(self, request):
        fullDataScan.delay(BLIZZ_CLIENT, BLIZZ_SECRET)
        return response.Response("Scan started")
