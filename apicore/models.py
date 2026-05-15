from django.db import models
from django.utils.translation import gettext_lazy as _

from apicore.libs.race_mapping import RACE_NAMES


class DataProfession(models.Model):
    profession_id = models.PositiveIntegerField(primary_key=True)
    profession_name = models.CharField(max_length=128)
    profession_description = models.CharField(max_length=1024)

    class Meta:
        db_table = "ft_data_profession"

    def __str__(self):
        return f"{self.profession_id} - {self.profession_name}"


class DataProfessionTier(models.Model):
    profession = models.ForeignKey(DataProfession, on_delete=models.CASCADE)
    tier_id = models.PositiveSmallIntegerField(primary_key=True)
    tier_name = models.CharField(max_length=128)
    tier_min_skill = models.PositiveSmallIntegerField()
    tier_max_skill = models.PositiveSmallIntegerField()

    class Meta:
        db_table = "ft_data_professiontier"

    def __str__(self):
        return f"{self.tier_id} - {self.tier_name}"


class DataProfessionRecipe(models.Model):
    tier = models.ForeignKey(DataProfessionTier, on_delete=models.CASCADE)
    recipe_id = models.PositiveSmallIntegerField(primary_key=True)
    recipe_name = models.CharField(max_length=128)
    recipe_description = models.TextField()
    recipe_category = models.CharField(max_length=128)
    recipe_rank = models.PositiveSmallIntegerField()
    recipe_crafted_quantity = models.PositiveIntegerField()

    class Meta:
        db_table = "ft_data_professionrecipe"

    def __str__(self):
        return f"{self.recipe_id} - {self.recipe_name}"


class DataReagent(models.Model):
    reagent_id = models.PositiveIntegerField(primary_key=True)
    reagent_name = models.CharField(max_length=128)
    reagent_quality = models.CharField(max_length=32)
    reagent_media = models.CharField(max_length=256)

    class Meta:
        db_table = "ft_data_reagent"

    def __str__(self):
        return f"{self.reagent_id} - {self.reagent_name}"


class DataRecipeReagent(models.Model):
    recipe = models.ForeignKey(DataProfessionRecipe, on_delete=models.CASCADE)
    reagent = models.ForeignKey(DataReagent, on_delete=models.CASCADE)
    quantity = models.PositiveSmallIntegerField()

    class Meta:
        db_table = "ft_data_recipereagent"

    def __str__(self):
        return f"{self.recipe.recipe_name} - {self.reagent.reagent_name} - {self.quantity}"


class DataEquipment(models.Model):
    equipment_id = models.PositiveIntegerField(primary_key=True)
    equipment_name = models.CharField(max_length=128)
    equipment_type = models.CharField(max_length=32)
    equipment_slot = models.CharField(max_length=32)
    equipment_icon = models.CharField(max_length=128)

    class Meta:
        db_table = "ft_data_equipment"

    def __str__(self):
        return f"{self.equipment_id} - {self.equipment_name}"


class DataEquipmentVariant(models.Model):
    equipment = models.ForeignKey(DataEquipment, on_delete=models.CASCADE)
    variant = models.CharField(max_length=64)
    stamina = models.PositiveSmallIntegerField()
    armour = models.PositiveSmallIntegerField()
    strength = models.PositiveSmallIntegerField()
    agility = models.PositiveSmallIntegerField()
    intellect = models.PositiveSmallIntegerField()
    haste = models.PositiveSmallIntegerField()
    mastery = models.PositiveSmallIntegerField()
    vers = models.PositiveSmallIntegerField()
    crit = models.PositiveSmallIntegerField()
    level = models.PositiveSmallIntegerField()
    quality = models.CharField(max_length=32)

    class Meta:
        db_table = "ft_data_equipmentvariant"
        constraints = [
            models.UniqueConstraint(fields=["equipment", "variant"], name="unique_equipmentvariant")
        ]

    def __str__(self):
        return f"{self.equipment} - {self.variant}"


class DataMount(models.Model):
    mount_id = models.PositiveIntegerField(primary_key=True)
    mount_name = models.CharField(max_length=128)
    mount_description = models.CharField(max_length=1024)
    mount_source = models.CharField(max_length=64)
    mount_media_zoom = models.CharField(max_length=256)
    mount_media_icon = models.CharField(max_length=256)
    mount_faction = models.CharField(max_length=64)

    class Meta:
        db_table = "ft_data_mount"

    def __str__(self):
        return f"{self.mount_id} - {self.mount_name}"


class DataPet(models.Model):
    pet_id = models.PositiveIntegerField(primary_key=True)
    pet_name = models.CharField(max_length=128)
    pet_description = models.CharField(max_length=1024)
    pet_source = models.CharField(max_length=64)
    pet_media_icon = models.CharField(max_length=256)
    pet_faction = models.CharField(max_length=64)
    pet_npc_id = models.PositiveIntegerField()

    class Meta:
        db_table = "ft_data_pet"

    def __str__(self):
        return f"{self.pet_id} - {self.pet_name}"


#################################################################################
#                                                                               #
#                            Data/Profile Separator                             #
#                                                                               #
#################################################################################


class ProfileUser(models.Model):
    user_id = models.CharField(max_length=100, primary_key=True)
    user_file = models.FileField(upload_to="uploads")
    user_last_update = models.DateTimeField()

    class Meta:
        db_table = "ft_profile_user"

    def __str__(self):
        return self.user_id


class ProfileUserMount(models.Model):
    user = models.ForeignKey(ProfileUser, on_delete=models.CASCADE)
    mount = models.ForeignKey(DataMount, on_delete=models.CASCADE)

    class Meta:
        db_table = "ft_profile_usermount"
        constraints = [models.UniqueConstraint(fields=["user", "mount"], name="unique_usermount")]

    def __str__(self):
        return f"{self.user} - {self.mount}"


class ProfileUserPet(models.Model):
    user = models.ForeignKey(ProfileUser, on_delete=models.CASCADE)
    pet = models.ForeignKey(DataPet, on_delete=models.CASCADE)

    class Meta:
        db_table = "ft_profile_userpet"
        constraints = [models.UniqueConstraint(fields=["user", "pet"], name="unique_userpet")]

    def __str__(self):
        return f"{self.user} - {self.pet}"


class ProfileAlt(models.Model):
    class AltClass(models.IntegerChoices):
        NO_CLASS = 0, _("No Class")
        WARRIOR = 1, _("Warrior")
        PALADIN = 2, _("Paladin")
        HUNTER = 3, _("Hunter")
        ROGUE = 4, _("Rogue")
        PRIEST = 5, _("Priest")
        DEATH_KNIGHT = 6, _("Death Knight")
        SHAMAN = 7, _("Shaman")
        MAGE = 8, _("Mage")
        WARLOCK = 9, _("Warlock")
        MONK = 10, _("Monk")
        DRUID = 11, _("Druid")
        DEMON_HUNTER = 12, _("Demon Hunter")
        EVOKER = 13, _("Evoker")

    alt_id = models.PositiveIntegerField(primary_key=True)
    alt_account_id = models.PositiveIntegerField()
    alt_level = models.PositiveSmallIntegerField()
    alt_name = models.CharField(max_length=64)
    alt_realm = models.CharField(max_length=64)
    alt_realm_id = models.PositiveSmallIntegerField()
    alt_realm_slug = models.CharField(max_length=64)
    alt_class = models.PositiveSmallIntegerField(
        choices=AltClass.choices, default=AltClass.NO_CLASS
    )
    alt_race = models.PositiveSmallIntegerField(default=0)
    alt_gender = models.CharField(max_length=16)
    alt_faction = models.CharField(max_length=16)
    alt_expiry_date = models.DateTimeField()
    user = models.ForeignKey(ProfileUser, on_delete=models.CASCADE)

    class Meta:
        db_table = "ft_profile_alt"
        constraints = [
            models.UniqueConstraint(fields=["alt_name", "alt_realm_slug"], name="unique_alt")
        ]

    def __str__(self):
        return f"{self.alt_name} - {self.alt_realm}"

    def get_alt_race_display(self):
        return RACE_NAMES.get(self.alt_race, str(self.alt_race))


class ProfileAltProfession(models.Model):
    class Profession(models.IntegerChoices):
        MISSING = 0, _("Missing")
        ALCHEMY = 171, _("Alchemy")
        BLACKSMITHING = 164, _("Blacksmithing")
        ENCHANTING = 333, _("Enchanting")
        ENGINEERING = 202, _("Engineering")
        INSCRIPTION = 773, _("Inscription")
        JEWELCRAFTING = 755, _("Jewelcrafting")
        LEATHERWORKING = 165, _("Leatherworking")
        TAILORING = 197, _("Tailoring")
        HERBALISM = 182, _("Herbalism")
        MINING = 186, _("Mining")
        SKINNING = 393, _("Skinning")

    alt = models.OneToOneField(ProfileAlt, on_delete=models.CASCADE, primary_key=True)
    profession_1 = models.PositiveIntegerField(
        choices=Profession.choices, default=Profession.MISSING
    )
    profession_2 = models.PositiveIntegerField(
        choices=Profession.choices, default=Profession.MISSING
    )
    alt_profession_expiry_date = models.DateTimeField()

    class Meta:
        db_table = "ft_profile_altprofession"

    def __str__(self):
        return f"{self.alt.alt_name} - {self.alt.alt_realm}"


class ProfileAltProfessionData(models.Model):
    alt = models.ForeignKey(ProfileAltProfession, on_delete=models.CASCADE)
    profession_recipe = models.ForeignKey(DataProfessionRecipe, on_delete=models.CASCADE)
    profession_tier = models.ForeignKey(DataProfessionTier, on_delete=models.CASCADE)
    profession = models.ForeignKey(DataProfession, on_delete=models.CASCADE)
    alt_profession_data_expiry_date = models.DateTimeField()

    class Meta:
        db_table = "ft_profile_altprofessiondata"
        constraints = [
            models.UniqueConstraint(
                fields=["alt", "profession", "profession_tier", "profession_recipe"],
                name="unique_altprofessiondata",
            )
        ]

    def __str__(self):
        return f"{self.alt} - {self.profession_recipe}"


class ProfileAltEquipment(models.Model):
    alt = models.OneToOneField(ProfileAlt, on_delete=models.CASCADE, primary_key=True)
    head = models.CharField(max_length=64)
    neck = models.CharField(max_length=64)
    shoulder = models.CharField(max_length=64)
    back = models.CharField(max_length=64)
    chest = models.CharField(max_length=64)
    tabard = models.CharField(max_length=64)
    shirt = models.CharField(max_length=64)
    wrist = models.CharField(max_length=64)
    hands = models.CharField(max_length=64)
    belt = models.CharField(max_length=64)
    legs = models.CharField(max_length=64)
    feet = models.CharField(max_length=64)
    ring1 = models.CharField(max_length=64)
    ring2 = models.CharField(max_length=64)
    trinket1 = models.CharField(max_length=64)
    trinket2 = models.CharField(max_length=64)
    weapon1 = models.CharField(max_length=64)
    weapon2 = models.CharField(max_length=64)
    alt_equipment_expiry_date = models.DateTimeField()

    class Meta:
        db_table = "ft_profile_altequipment"

    def __str__(self):
        return f"{self.alt.alt_name} - {self.alt.alt_realm}"
