import datetime
import logging
from types import SimpleNamespace

import requests
from celery import group, shared_task
from django.utils import timezone
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from apicore.libs.faction_expansion import FACTION_EXPANSION
from apicore.libs.mount_icons import MOUNT_ICONS
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

logger = logging.getLogger(__name__)

_EU_TOKEN_URL = "https://eu.battle.net/oauth/token"
_EU_API_BASE = "https://eu.api.blizzard.com"
_PROFILE_PARAMS = {"namespace": "profile-eu", "locale": "en_US"}
_STATIC_PARAMS = {"namespace": "static-eu", "locale": "en_US"}
_LOCALE_PARAMS = {"locale": "en_US"}

_EQUIPMENT_SLOTS = [
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

_SLOT_MAP = {
    "head": "head",
    "neck": "neck",
    "shoulders": "shoulder",
    "back": "back",
    "chest": "chest",
    "tabard": "tabard",
    "shirt": "shirt",
    "wrist": "wrist",
    "hands": "hands",
    "waist": "belt",
    "legs": "legs",
    "feet": "feet",
    "ring 1": "ring1",
    "ring 2": "ring2",
    "trinket 1": "trinket1",
    "trinket 2": "trinket2",
    "main hand": "weapon1",
    "off hand": "weapon2",
}

_STAT_FIELDS = {
    "STAMINA": "stamina",
    "STRENGTH": "strength",
    "AGILITY": "agility",
    "INTELLECT": "intellect",
    "HASTE_RATING": "haste",
    "MASTERY_RATING": "mastery",
    "VERSATILITY": "vers",
    "CRIT_RATING": "crit",
}

_session = requests.Session()
_session.mount(
    "https://",
    HTTPAdapter(
        max_retries=Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST"],
        )
    ),
)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _fetch_token(client: str, secret: str) -> str:
    resp = _session.post(
        f"{_EU_TOKEN_URL}?grant_type=client_credentials",
        data={"client_id": client, "client_secret": secret},
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def _api_get(url: str, params: dict, headers: dict) -> object:
    try:
        return _session.get(url, params=params, headers=headers, timeout=5)
    except requests.exceptions.RequestException as exc:
        logger.warning("Request failed %s: %s", url, exc)
        return SimpleNamespace(status_code=999)


# ---------------------------------------------------------------------------
# Alt scan — coordinator + per-alt worker
# ---------------------------------------------------------------------------


@shared_task
def fullAltScan(user_id: str, client: str, secret: str) -> None:
    token = _fetch_token(client, secret)
    alt_ids = list(ProfileAlt.objects.filter(user=user_id).values_list("alt_id", flat=True))
    ProfileUser.objects.filter(user_id=user_id).update(user_last_update=timezone.now())
    logger.info("Dispatching %d alt scan tasks for user %s", len(alt_ids), user_id)
    group(scan_single_alt.s(alt_id, user_id, token) for alt_id in alt_ids).apply_async()
    scan_user_collection.delay(user_id, token)


@shared_task(bind=True)
def scan_single_alt(self, alt_id: int, user_id: str, token: str) -> None:
    try:
        alt = ProfileAlt.objects.get(alt_id=alt_id)
        auth_headers = {"Authorization": f"Bearer {token}"}

        char_base = (
            f"{_EU_API_BASE}/profile/wow/character/{alt.alt_realm_slug}/{alt.alt_name.lower()}"
        )

        summary_resp = _api_get(char_base, _PROFILE_PARAMS, auth_headers)
        if summary_resp.status_code == 200:
            ilvl = summary_resp.json().get("equipped_item_level", 0)
            ProfileAlt.objects.filter(alt_id=alt_id).update(alt_ilvl=ilvl)

        endpoints = {
            "professions": f"{char_base}/professions",
            "equipment": f"{char_base}/equipment",
            "reputations": f"{char_base}/reputations",
        }

        for key, url in endpoints.items():
            resp = _api_get(url, _PROFILE_PARAMS, auth_headers)
            if resp.status_code != 200:
                logger.warning("Blizzard API %s %s", resp.status_code, url)
                continue
            if key == "professions":
                _sync_professions(alt, resp.json(), auth_headers)
            elif key == "equipment":
                _sync_equipment(alt, resp.json())
            elif key == "reputations":
                _sync_reputations(alt, resp.json())

        logger.info("Completed alt scan: %s-%s", alt.alt_name, alt.alt_realm_slug)
    except Exception as exc:
        logger.error(
            "scan_single_alt failed: alt_id=%s user_id=%s task_id=%s error=%s",
            alt_id,
            user_id,
            self.request.id,
            exc,
        )
        raise


@shared_task
def scan_user_collection(user_id: str, token: str) -> None:
    """Fetch account-wide data (mounts, pets, achievements) from one alt per faction."""
    try:
        user = ProfileUser.objects.get(user_id=user_id)
        auth_headers = {"Authorization": f"Bearer {token}"}

        alts_by_faction: dict[str, ProfileAlt] = {}
        for alt in ProfileAlt.objects.filter(user=user_id).order_by("-alt_level", "-alt_ilvl"):
            faction = alt.alt_faction.upper()
            if faction not in alts_by_faction:
                alts_by_faction[faction] = alt
            if len(alts_by_faction) >= 2:
                break

        for faction, alt in alts_by_faction.items():
            char_base = (
                f"{_EU_API_BASE}/profile/wow/character/{alt.alt_realm_slug}/{alt.alt_name.lower()}"
            )
            for endpoint, key in [
                (f"{char_base}/collections/mounts", "mounts"),
                (f"{char_base}/collections/pets", "pets"),
                (f"{char_base}/achievements", "achievements"),
            ]:
                resp = _api_get(endpoint, _PROFILE_PARAMS, auth_headers)
                if resp.status_code != 200:
                    logger.warning("Blizzard API %s %s", resp.status_code, endpoint)
                    continue
                if key == "mounts":
                    _sync_mounts(user, resp.json())
                elif key == "pets":
                    _sync_pets(user, resp.json())
                elif key == "achievements":
                    _sync_achievements(alt, resp.json())

            logger.info(
                "Completed collection scan for %s faction via %s-%s",
                faction,
                alt.alt_name,
                alt.alt_realm_slug,
            )
    except Exception as exc:
        logger.error("scan_user_collection failed: user_id=%s error=%s", user_id, exc)
        raise


def _sync_professions(alt: ProfileAlt, data: dict, auth_headers: dict) -> None:
    expiry = timezone.now() + datetime.timedelta(days=30)
    prof_record, _ = ProfileAltProfession.objects.get_or_create(
        alt=alt,
        defaults={
            "profession_1": 0,
            "profession_2": 0,
            "alt_profession_expiry_date": expiry,
        },
    )

    active_prof_ids: list[int] = []

    for prof_data in data.get("primaries", []):
        prof_id = prof_data["profession"]["id"]
        active_prof_ids.append(prof_id)

        profession, _ = DataProfession.objects.get_or_create(
            profession_id=prof_id,
            defaults={
                "profession_name": prof_data["profession"]["name"],
                "profession_description": "",
            },
        )

        for tier_data in prof_data.get("tiers", []):
            try:
                tier = DataProfessionTier.objects.get(tier_id=tier_data["tier"]["id"])
            except DataProfessionTier.DoesNotExist:
                logger.debug("Unknown tier: %s", tier_data["tier"]["name"])
                continue

            for recipe_ref in tier_data.get("known_recipes", []):
                recipe = _get_or_fetch_recipe(recipe_ref, tier, auth_headers)
                if recipe is None:
                    continue
                ProfileAltProfessionData.objects.get_or_create(
                    alt=prof_record,
                    profession=profession,
                    profession_tier=tier,
                    profession_recipe=recipe,
                    defaults={"alt_profession_data_expiry_date": expiry},
                )

    while len(active_prof_ids) < 2:
        active_prof_ids.append(0)

    for stale_id in [prof_record.profession_1, prof_record.profession_2]:
        if stale_id not in active_prof_ids:
            ProfileAltProfessionData.objects.filter(alt=prof_record, profession=stale_id).delete()

    prof_record.profession_1 = active_prof_ids[0]
    prof_record.profession_2 = active_prof_ids[1]
    prof_record.alt_profession_expiry_date = expiry
    prof_record.save()


def _get_or_fetch_recipe(
    recipe_ref: dict, tier: DataProfessionTier, auth_headers: dict
) -> DataProfessionRecipe | None:
    try:
        return DataProfessionRecipe.objects.get(recipe_id=recipe_ref["id"])
    except DataProfessionRecipe.DoesNotExist:
        pass

    resp = _api_get(recipe_ref["key"]["href"], _LOCALE_PARAMS, auth_headers)
    if resp.status_code != 200:
        logger.warning("Blizzard API %s %s", resp.status_code, recipe_ref["key"]["href"])
        return None

    try:
        details = resp.json()
        recipe, _ = DataProfessionRecipe.objects.get_or_create(
            recipe_id=details["id"],
            defaults={
                "tier": tier,
                "recipe_name": details["name"],
                "recipe_description": details.get("description") or "None",
                "recipe_category": "N/A",
                "recipe_rank": details.get("rank", 1),
                "recipe_crafted_quantity": (details.get("crafted_quantity", {}).get("value", 1)),
            },
        )
        return recipe
    except (KeyError, TypeError) as exc:
        logger.warning("Failed to parse recipe %s: %s", recipe_ref.get("id"), exc)
        return None


def _sync_equipment(alt: ProfileAlt, data: dict) -> None:
    expiry = timezone.now() + datetime.timedelta(days=30)
    equip_record, _ = ProfileAltEquipment.objects.get_or_create(
        alt=alt,
        defaults={
            **{slot: "0" for slot in _EQUIPMENT_SLOTS},
            "alt_equipment_expiry_date": expiry,
        },
    )

    new_slots = {slot: "0" for slot in _EQUIPMENT_SLOTS}

    for item in data.get("equipped_items", []):
        try:
            equipment, _ = DataEquipment.objects.get_or_create(
                equipment_id=item["item"]["id"],
                defaults={
                    "equipment_name": item["name"],
                    "equipment_type": item["item_subclass"]["name"],
                    "equipment_slot": item["slot"]["name"],
                    "equipment_icon": "not done yet",
                },
            )

            try:
                variant_code = "".join(str(b) for b in item["bonus_list"])
            except KeyError:
                variant_code = "FLUFF"

            variant, _ = DataEquipmentVariant.objects.get_or_create(
                equipment=equipment,
                variant=variant_code,
                defaults=_parse_item_stats(item),
            )

            field_name = _SLOT_MAP.get(item["slot"]["name"].lower())
            if field_name:
                new_slots[field_name] = f"{item['item']['id']}:{variant_code}"
        except (KeyError, TypeError) as exc:
            logger.warning("Failed to parse equipment item: %s", exc)

    for field, value in new_slots.items():
        setattr(equip_record, field, value)
    equip_record.alt_equipment_expiry_date = expiry
    equip_record.save()


def _parse_item_stats(item: dict) -> dict:
    defaults = {v: 0 for v in _STAT_FIELDS.values()}
    defaults["armor"] = 0

    for stat in item.get("stats", []):
        field = _STAT_FIELDS.get(stat.get("type", {}).get("type", ""))
        if field:
            defaults[field] = stat.get("value", 0)

    defaults["armor"] = item.get("armor", {}).get("value", 0)
    defaults["level"] = item.get("level", {}).get("value", 0)
    defaults["quality"] = item.get("quality", {}).get("name", "")
    return defaults


def _sync_mounts(user: ProfileUser, data: dict) -> None:
    for mount_data in data.get("mounts", []):
        try:
            mount = DataMount.objects.get(mount_id=mount_data["mount"]["id"])
        except DataMount.DoesNotExist:
            logger.debug(
                "Unknown mount: %s (%s)",
                mount_data["mount"]["id"],
                mount_data["mount"]["name"],
            )
            continue
        ProfileUserMount.objects.get_or_create(user=user, mount=mount)


def _sync_pets(user: ProfileUser, data: dict) -> None:
    for pet_data in data.get("pets", []):
        try:
            pet = DataPet.objects.get(pet_id=pet_data["species"]["id"])
        except DataPet.DoesNotExist:
            logger.debug(
                "Unknown pet: %s (%s)",
                pet_data["species"]["id"],
                pet_data["species"]["name"],
            )
            continue
        ProfileUserPet.objects.get_or_create(user=user, pet=pet)


# ---------------------------------------------------------------------------
# Data scan — static WoW data
# ---------------------------------------------------------------------------


@shared_task
def fullDataScan(client: str, secret: str) -> str:
    scanProfessionData.delay(client, secret)
    scanMountData.delay(client, secret)
    scanPetData.delay(client, secret)
    scanAchievementData.delay(client, secret)
    scanFactionData.delay(client, secret)
    return "Dispatched all data scans"


@shared_task
def scanProfessionData(client: str, secret: str) -> str:
    token = _fetch_token(client, secret)
    auth_headers = {"Authorization": f"Bearer {token}"}
    resp = _api_get(f"{_EU_API_BASE}/data/wow/profession/index", _STATIC_PARAMS, auth_headers)
    if resp.status_code != 200:
        logger.error("Blizzard API %s profession/index", resp.status_code)
        return "Failed"
    _sync_profession_data(resp.json(), auth_headers)
    return "Done"


@shared_task
def scanMountData(client: str, secret: str) -> str:
    token = _fetch_token(client, secret)
    auth_headers = {"Authorization": f"Bearer {token}"}
    resp = _api_get(f"{_EU_API_BASE}/data/wow/mount/index", _STATIC_PARAMS, auth_headers)
    if resp.status_code != 200:
        logger.error("Blizzard API %s mount/index", resp.status_code)
        return "Failed"
    _sync_mount_data(resp.json(), auth_headers)
    return "Done"


@shared_task
def scanPetData(client: str, secret: str) -> str:
    token = _fetch_token(client, secret)
    auth_headers = {"Authorization": f"Bearer {token}"}
    resp = _api_get(f"{_EU_API_BASE}/data/wow/pet/index", _STATIC_PARAMS, auth_headers)
    if resp.status_code != 200:
        logger.error("Blizzard API %s pet/index", resp.status_code)
        return "Failed"
    _sync_pet_data(resp.json(), auth_headers)
    return "Done"


@shared_task
def scanAchievementData(client: str, secret: str) -> str:
    token = _fetch_token(client, secret)
    auth_headers = {"Authorization": f"Bearer {token}"}
    resp = _api_get(f"{_EU_API_BASE}/data/wow/achievement/index", _STATIC_PARAMS, auth_headers)
    if resp.status_code != 200:
        logger.error("Blizzard API %s achievement/index", resp.status_code)
        return "Failed"
    _sync_achievement_data(resp.json(), auth_headers)
    return "Done"


@shared_task
def scanFactionData(client: str, secret: str) -> str:
    token = _fetch_token(client, secret)
    auth_headers = {"Authorization": f"Bearer {token}"}
    resp = _api_get(
        f"{_EU_API_BASE}/data/wow/reputation-faction/index", _STATIC_PARAMS, auth_headers
    )
    if resp.status_code != 200:
        logger.error("Blizzard API %s reputation-faction/index", resp.status_code)
        return "Failed"
    _sync_faction_data(resp.json())
    return "Done"


def _sync_profession_data(index_data: dict, auth_headers: dict) -> None:
    for profession_ref in index_data.get("professions", []):
        resp = _api_get(profession_ref["key"]["href"], _STATIC_PARAMS, auth_headers)
        if resp.status_code != 200:
            logger.warning("Blizzard API %s %s", resp.status_code, profession_ref["key"]["href"])
            continue

        try:
            details = resp.json()
            profession, _ = DataProfession.objects.get_or_create(
                profession_id=details["id"],
                defaults={
                    "profession_name": details["name"],
                    "profession_description": details.get("description") or "",
                },
            )
        except (KeyError, TypeError) as exc:
            logger.warning("Failed to parse profession: %s", exc)
            continue

        for tier_ref in details.get("skill_tiers", []):
            _sync_tier_data(tier_ref, profession, auth_headers)


def _sync_tier_data(tier_ref: dict, profession: DataProfession, auth_headers: dict) -> None:
    logger.info("Processing tier: %s", tier_ref["name"])
    resp = _api_get(tier_ref["key"]["href"], _STATIC_PARAMS, auth_headers)
    if resp.status_code != 200:
        logger.warning("Blizzard API %s %s", resp.status_code, tier_ref["key"]["href"])
        return

    try:
        details = resp.json()
        tier, _ = DataProfessionTier.objects.get_or_create(
            tier_id=details["id"],
            defaults={
                "profession": profession,
                "tier_name": details["name"],
                "tier_min_skill": details["minimum_skill_level"],
                "tier_max_skill": details["maximum_skill_level"],
            },
        )
    except (KeyError, TypeError) as exc:
        logger.warning("Failed to parse tier: %s", exc)
        return

    for category in details.get("categories", []):
        for recipe_ref in category.get("recipes", []):
            _sync_recipe_data(recipe_ref, category["name"], tier, auth_headers)


def _sync_recipe_data(
    recipe_ref: dict, category_name: str, tier: DataProfessionTier, auth_headers: dict
) -> None:
    logger.info("Processing recipe: %s", recipe_ref["name"])
    resp = _api_get(recipe_ref["key"]["href"], _STATIC_PARAMS, auth_headers)
    if resp.status_code != 200:
        logger.warning("Blizzard API %s %s", resp.status_code, recipe_ref["key"]["href"])
        return

    try:
        details = resp.json()
        crafted_item_href = details.get("crafted_item", {}).get("key", {}).get("href")
        if crafted_item_href:
            item_resp = _api_get(crafted_item_href, _STATIC_PARAMS, auth_headers)
            media_href = (
                item_resp.json().get("media", {}).get("key", {}).get("href")
                if item_resp.status_code == 200
                else None
            )
        else:
            media_href = details.get("media", {}).get("key", {}).get("href")
        if media_href:
            media_resp = _api_get(media_href, _STATIC_PARAMS, auth_headers)
            recipe_icon = (
                media_resp.json().get("assets", [{}])[0].get("value", "Not Found")
                if media_resp.status_code == 200
                else "Not Found"
            )
        else:
            recipe_icon = "Not Found"
        recipe, _ = DataProfessionRecipe.objects.update_or_create(
            recipe_id=details["id"],
            defaults={
                "tier": tier,
                "recipe_name": details["name"],
                "recipe_description": details.get("description") or "None",
                "recipe_category": category_name,
                "recipe_rank": details.get("rank", 1),
                "recipe_crafted_quantity": (details.get("crafted_quantity", {}).get("value", 1)),
                "recipe_icon": recipe_icon,
            },
        )
    except (KeyError, TypeError) as exc:
        logger.warning("Failed to parse recipe %s: %s", recipe_ref["name"], exc)
        return

    for reagent_ref in details.get("reagents", []):
        _sync_reagent_data(reagent_ref, recipe, auth_headers)


def _sync_reagent_data(reagent_ref: dict, recipe: DataProfessionRecipe, auth_headers: dict) -> None:
    resp = _api_get(reagent_ref["reagent"]["key"]["href"], _STATIC_PARAMS, auth_headers)
    if resp.status_code != 200:
        logger.warning(
            "Blizzard API %s %s",
            resp.status_code,
            reagent_ref["reagent"]["key"]["href"],
        )
        return

    try:
        details = resp.json()

        try:
            reagent = DataReagent.objects.get(reagent_id=details["id"])
        except DataReagent.DoesNotExist:
            media_resp = _api_get(details["media"]["key"]["href"], _STATIC_PARAMS, auth_headers)
            if media_resp.status_code == 200:
                media = media_resp.json().get("assets", [{}])[0].get("value", "Not Found")
            else:
                logger.warning(
                    "Blizzard API %s %s",
                    media_resp.status_code,
                    details["media"]["key"]["href"],
                )
                media = "Not Found"
            reagent, _ = DataReagent.objects.get_or_create(
                reagent_id=details["id"],
                defaults={
                    "reagent_name": details["name"],
                    "reagent_quality": details["quality"]["name"],
                    "reagent_media": media,
                },
            )

        DataRecipeReagent.objects.get_or_create(
            recipe=recipe,
            reagent=reagent,
            defaults={"quantity": reagent_ref["quantity"]},
        )
    except (KeyError, TypeError) as exc:
        logger.warning("Failed to parse reagent: %s", exc)


def _sync_mount_data(index_data: dict, auth_headers: dict) -> None:
    for mount_ref in index_data.get("mounts", []):
        logger.info("Processing mount: %s", mount_ref["name"])
        resp = _api_get(mount_ref["key"]["href"], _STATIC_PARAMS, auth_headers)
        if resp.status_code != 200:
            logger.warning("Blizzard API %s %s", resp.status_code, mount_ref["key"]["href"])
            continue

        try:
            details = resp.json()
            if DataMount.objects.filter(mount_id=details["id"]).exists():
                continue

            displays = details.get("creature_displays", [])
            media_zoom = "Not Found"
            if displays:
                media_resp = _api_get(displays[0]["key"]["href"], _STATIC_PARAMS, auth_headers)
                if media_resp.status_code == 200:
                    media_zoom = media_resp.json().get("assets", [{}])[0].get("value", "Not Found")
                else:
                    logger.warning(
                        "Blizzard API %s %s",
                        media_resp.status_code,
                        displays[0]["key"]["href"],
                    )

            icon_name = MOUNT_ICONS.get(details["id"], "inv_misc_questionmark")
            media_icon = f"https://render.worldofwarcraft.com/eu/icons/56/{icon_name}.jpg"

            DataMount.objects.get_or_create(
                mount_id=details["id"],
                defaults={
                    "mount_name": details["name"],
                    "mount_description": details.get("description") or "None",
                    "mount_source": details.get("source", {}).get("name", "N/A"),
                    "mount_media_zoom": media_zoom,
                    "mount_media_icon": media_icon,
                    "mount_faction": details.get("faction", {}).get("name", "N/A"),
                },
            )
        except (KeyError, TypeError) as exc:
            logger.warning("Failed to parse mount: %s", exc)


def _sync_pet_data(index_data: dict, auth_headers: dict) -> None:
    for pet_ref in index_data.get("pets", []):
        logger.info("Processing pet: %s", pet_ref["name"])
        resp = _api_get(pet_ref["key"]["href"], _STATIC_PARAMS, auth_headers)
        if resp.status_code != 200:
            logger.warning("Blizzard API %s %s", resp.status_code, pet_ref["key"]["href"])
            continue

        try:
            details = resp.json()
            if DataPet.objects.filter(pet_id=details["id"]).exists():
                continue

            if details.get("is_horde_only"):
                faction = "Horde"
            elif details.get("is_alliance_only"):
                faction = "Alliance"
            else:
                faction = "N/A"

            DataPet.objects.get_or_create(
                pet_id=details["id"],
                defaults={
                    "pet_name": details["name"],
                    "pet_description": details.get("description") or "None",
                    "pet_source": details.get("source", {}).get("name", "N/A"),
                    "pet_media_icon": details.get(
                        "icon",
                        "https://render.worldofwarcraft.com/eu/icons/56/inv_misc_questionmark.jpg",
                    ),
                    "pet_faction": faction,
                    "pet_npc_id": details.get("creature", {}).get("id", 0),
                },
            )
        except (KeyError, TypeError) as exc:
            logger.warning("Failed to parse pet: %s", exc)


# ---------------------------------------------------------------------------
# Maintenance — purge stale profile data
# ---------------------------------------------------------------------------


@shared_task
def purge_stale_profiles() -> None:
    now = timezone.now()
    prof_data_deleted, _ = ProfileAltProfessionData.objects.filter(
        alt_profession_data_expiry_date__lt=now
    ).delete()
    prof_deleted, _ = ProfileAltProfession.objects.filter(
        alt_profession_expiry_date__lt=now
    ).delete()
    equip_deleted, _ = ProfileAltEquipment.objects.filter(
        alt_equipment_expiry_date__lt=now
    ).delete()
    ach_deleted, _ = ProfileAltAchievement.objects.filter(
        alt_achievement_expiry_date__lt=now
    ).delete()
    rep_deleted, _ = ProfileAltReputation.objects.filter(
        alt_reputation_expiry_date__lt=now
    ).delete()
    alt_deleted, _ = ProfileAlt.objects.filter(alt_expiry_date__lt=now).delete()
    logger.info(
        "purge_stale_profiles: deleted %d profession_data, %d professions, %d equipment, "
        "%d achievements, %d reputations, %d alts",
        prof_data_deleted,
        prof_deleted,
        equip_deleted,
        ach_deleted,
        rep_deleted,
        alt_deleted,
    )


# ---------------------------------------------------------------------------
# Per-alt sync helpers — achievements + reputations
# ---------------------------------------------------------------------------


def _sync_achievements(alt: ProfileAlt, data: dict) -> None:
    expiry = timezone.now() + datetime.timedelta(days=30)
    for ach_data in data.get("achievements", []):
        try:
            ach_ref = ach_data.get("achievement", {})
            ach_id = ach_ref.get("id") or ach_data.get("id")
            if not ach_id:
                continue
            achievement, _ = DataAchievement.objects.get_or_create(
                achievement_id=ach_id,
                defaults={"achievement_name": ach_ref.get("name", "Unknown")},
            )
            ts = ach_data.get("completed_timestamp")
            completed = timezone.datetime.fromtimestamp(ts / 1000, tz=datetime.UTC) if ts else None
            ProfileAltAchievement.objects.update_or_create(
                alt=alt,
                achievement=achievement,
                defaults={
                    "completed_timestamp": completed,
                    "alt_achievement_expiry_date": expiry,
                },
            )
        except (KeyError, TypeError) as exc:
            logger.warning("Failed to sync achievement for %s: %s", alt.alt_name, exc)


def _sync_reputations(alt: ProfileAlt, data: dict) -> None:
    expiry = timezone.now() + datetime.timedelta(days=30)
    for rep_data in data.get("reputations", []):
        try:
            faction_ref = rep_data.get("faction", {})
            faction_id = faction_ref.get("id")
            if not faction_id:
                continue
            standing = rep_data.get("standing", {})
            if not standing:
                continue
            faction, _ = DataFaction.objects.update_or_create(
                faction_id=faction_id,
                defaults={
                    "faction_name": faction_ref.get("name", "Unknown"),
                    "faction_category": FACTION_EXPANSION.get(faction_id, ""),
                },
            )
            ProfileAltReputation.objects.update_or_create(
                alt=alt,
                faction=faction,
                defaults={
                    "standing_type": standing.get("name", ""),
                    "standing_value": standing.get("raw", 0),
                    "alt_reputation_expiry_date": expiry,
                },
            )
        except (KeyError, TypeError) as exc:
            logger.warning("Failed to sync reputation for %s: %s", alt.alt_name, exc)


# ---------------------------------------------------------------------------
# Static data sync helpers — achievements + factions
# ---------------------------------------------------------------------------


def _sync_achievement_data(index_data: dict, auth_headers: dict) -> None:
    achievements = index_data.get("achievements", [])
    total = len(achievements)
    logger.info("Achievement scan: %d achievements to process", total)
    for i, ach_ref in enumerate(achievements, 1):
        if i % 100 == 0 or i == total:
            logger.info("Achievement scan: %d/%d", i, total)
        resp = _api_get(ach_ref["key"]["href"], _STATIC_PARAMS, auth_headers)
        if resp.status_code != 200:
            logger.warning("Blizzard API %s %s", resp.status_code, ach_ref["key"]["href"])
            continue
        try:
            details = resp.json()
            DataAchievement.objects.update_or_create(
                achievement_id=details["id"],
                defaults={
                    "achievement_name": details["name"],
                    "achievement_points": details.get("points", 0),
                    "achievement_category": details.get("category", {}).get("name", ""),
                },
            )
        except (KeyError, TypeError) as exc:
            logger.warning("Failed to parse achievement %s: %s", ach_ref.get("id"), exc)
    logger.info("Achievement scan complete")


def _sync_faction_data(index_data: dict) -> None:
    for faction_ref in index_data.get("factions", []):
        try:
            DataFaction.objects.get_or_create(
                faction_id=faction_ref["id"],
                defaults={"faction_name": faction_ref["name"]},
            )
        except (KeyError, TypeError) as exc:
            logger.warning("Failed to parse faction %s: %s", faction_ref.get("id"), exc)
