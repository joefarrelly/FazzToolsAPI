from django.db import models
from django.utils.translation import gettext_lazy as _

# Create your models here.


class DataProfession(models.Model):
    professionId = models.PositiveIntegerField(primary_key=True)
    professionName = models.CharField(max_length=50)
    professionDescription = models.CharField(max_length=300)

    class Meta:
        db_table = 'ft_data_profession'

    def __str__(self):
        return '%s - %s' % (self.professionId, self.professionName)


class DataProfessionTier(models.Model):
    profession = models.ForeignKey(DataProfession, on_delete=models.CASCADE)
    tierId = models.PositiveSmallIntegerField(primary_key=True)
    tierName = models.CharField(max_length=100)
    tierMinSkill = models.PositiveSmallIntegerField()
    tierMaxSkill = models.PositiveSmallIntegerField()

    class Meta:
        db_table = 'ft_data_professiontier'

    def __str__(self):
        return '%s - %s' % (self.tierId, self.tierName)


class DataProfessionRecipe(models.Model):
    tier = models.ForeignKey(DataProfessionTier, on_delete=models.CASCADE)
    recipeId = models.PositiveSmallIntegerField(primary_key=True)
    recipeName = models.CharField(max_length=100)
    recipeDescription = models.CharField(max_length=500)
    recipeCategory = models.CharField(max_length=100)
    recipeRank = models.PositiveSmallIntegerField()
    recipeCraftedQuantity = models.PositiveIntegerField()

    class Meta:
        db_table = 'ft_data_professionrecipe'

    def __str__(self):
        return '%s - %s' % (self.recipeId, self.recipeName)


class DataReagent(models.Model):
    reagentId = models.PositiveIntegerField(primary_key=True)
    reagentName = models.CharField(max_length=100)
    reagentQuality = models.CharField(max_length=20)
    reagentMedia = models.CharField(max_length=150)

    class Meta:
        db_table = 'ft_data_reagent'

    def __str__(self):
        return '%s - %s' % (self.reagentId, self.reagentName)


class DataRecipeReagent(models.Model):
    recipe = models.ForeignKey(DataProfessionRecipe, on_delete=models.CASCADE)
    reagent = models.ForeignKey(DataReagent, on_delete=models.CASCADE)
    quantity = models.PositiveSmallIntegerField()

    class Meta:
        db_table = 'ft_data_recipereagent'

    def __str__(self):
        return '%s - %s - %s' % (self.recipe.recipeName, self.reagent.reagentName, self.quantity)


class DataEquipment(models.Model):
    equipmentId = models.PositiveIntegerField(primary_key=True)
    equipmentName = models.CharField(max_length=80)
    equipmentType = models.CharField(max_length=20)
    equipmentSlot = models.CharField(max_length=20)
    equipmentIcon = models.CharField(max_length=100)

    class Meta:
        db_table = 'ft_data_equipment'

    def __str__(self):
        return '%s - %s' % (self.equipmentId, self.equipmentName)


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
    quality = models.CharField(max_length=20)

    class Meta:
        db_table = 'ft_data_equipmentvariant'
        constraints = [
            models.UniqueConstraint(fields=['equipment', 'variant'], name='unique_equipmentvariant')
        ]


class DataMount(models.Model):
    mountId = models.PositiveIntegerField(primary_key=True)
    mountName = models.CharField(max_length=100)
    mountDescription = models.CharField(max_length=500)
    mountSource = models.CharField(max_length=50)
    mountMediaZoom = models.CharField(max_length=150)
    mountMediaIcon = models.CharField(max_length=150)
    mountFaction = models.CharField(max_length=30)

    class Meta:
        db_table = 'ft_data_mount'


#################################################################################
#                                                                               #
#                            Data/Profile Separator                             #
#                                                                               #
#################################################################################


class ProfileUser(models.Model):
    userId = models.CharField(max_length=100, primary_key=True)
    userFile = models.FileField(upload_to='uploads')
    userLastUpdate = models.DateTimeField()

    class Meta:
        db_table = 'ft_profile_user'


class ProfileUserMount(models.Model):
    user = models.ForeignKey(ProfileUser, on_delete=models.CASCADE)
    mount = models.ForeignKey(DataMount, on_delete=models.CASCADE)

    class Meta:
        db_table = 'ft_profile_usermount'


class ProfileAlt(models.Model):
    altId = models.PositiveIntegerField(primary_key=True)
    altAccountId = models.PositiveIntegerField()
    altLevel = models.PositiveSmallIntegerField()
    altName = models.CharField(max_length=40)
    altRealm = models.CharField(max_length=40)
    altRealmId = models.PositiveSmallIntegerField()
    altRealmSlug = models.CharField(max_length=40)

    class AltClass(models.IntegerChoices):
        NO_CLASS = 0, _('No Class')
        WARRIOR = 1, _('Warrior')
        PALADIN = 2, _('Paladin')
        HUNTER = 3, _('Hunter')
        ROGUE = 4, _('Rogue')
        PRIEST = 5, _('Priest')
        DEATH_KNIGHT = 6, _('Death Knight')
        SHAMAN = 7, _('Shaman')
        MAGE = 8, _('Mage')
        WARLOCK = 9, _('Warlock')
        MONK = 10, _('Monk')
        DRUID = 11, _('Druid')
        DEMON_HUNTER = 12, _('Demon Hunter')
    altClass = models.PositiveSmallIntegerField(choices=AltClass.choices, default=AltClass.NO_CLASS)

    class AltRace(models.IntegerChoices):
        NO_RACE = 0, _('No Race')
        HUMAN = 1, _('Human')
        ORC = 2, _('Orc')
        DWARF = 3, _('Dwarf')
        NIGHT_ELF = 4, _('Night Elf')
        UNDEAD = 5, _('Undead')
        TAUREN = 6, _('Tauren')
        GNOME = 7, _('Gnome')
        TROLL = 8, _('Troll')
        GOBLIN = 9, _('Goblin')
        BLOOD_ELF = 10, _('Blood Elf')
        DRAENEI = 11, _('Draenei')
        WORGEN = 22, _('Worgen')
        PANDAREN_NEUTRAL = 24, _('Pandaren')
        PANDAREN_ALLIANCE = 25, _('Pandaren')
        PANDAREN_HORDE = 26, _('Pandaren')
        NIGHTBOURNE = 27, _('Nightbourne')
        HIGHMOUNTAIN_TAUREN = 28, _('Highmountain Tauren')
        VOID_ELF = 29, _('Void Elf')
        LIGHTFORGED_DRAENEI = 30, _('Lightforged Draenei')
        ZANDALARI_TROLL = 31, _('Zandalari Troll')
        KUL_TIRAN = 32, _('Kul Tiran')
        DARK_IRON_DWARF = 34, _('Dark Iron Dwarf')
        VULPERA = 35, _('Vulpera')
        MAGHAR_ORC = 36, _('Mag\'ar Orc')
        MECHAGNOME = 37, _('Mechagnome')
    altRace = models.PositiveSmallIntegerField(choices=AltRace.choices, default=AltRace.NO_RACE)

    altGender = models.CharField(max_length=6)
    altFaction = models.CharField(max_length=10)
    altExpiryDate = models.DateTimeField()

    user = models.ForeignKey(ProfileUser, on_delete=models.CASCADE)

    class Meta:
        db_table = 'ft_profile_alt'
        constraints = [
            models.UniqueConstraint(fields=['altName', 'altRealmSlug'], name='unique_alt')
        ]

    def __str__(self):
        return '%s - %s' % (self.altName, self.altRealm)


class ProfileAltProfession(models.Model):
    alt = models.OneToOneField(ProfileAlt, on_delete=models.CASCADE, primary_key=True)

    class Profession(models.IntegerChoices):
        MISSING = 0, _('Missing')
        ALCHEMY = 171, _('Alchemy')
        BLACKSMITHING = 164, _('Blacksmithing')
        ENCHANTING = 333, _('Enchanting')
        ENGINEERING = 202, _('Engineering')
        INSCRIPTION = 773, _('Inscription')
        JEWELCRAFTING = 755, _('Jewelcrafting')
        LEATHERWORKING = 165, _('Leatherworking')
        TAILORING = 197, _('Tailoring')
        HERBALISM = 182, _('Herbalism')
        MINING = 186, _('Mining')
        SKINNING = 393, _('Skinning')
    profession1 = models.PositiveIntegerField(choices=Profession.choices, default=Profession.MISSING)
    profession2 = models.PositiveIntegerField(choices=Profession.choices, default=Profession.MISSING)
    altProfessionExpiryDate = models.DateTimeField()

    class Meta:
        db_table = 'ft_profile_altprofession'

    def __str__(self):
        return '%s - %s' % (self.alt.altName, self.alt.altRealm)


class ProfileAltProfessionData(models.Model):
    alt = models.ForeignKey(ProfileAltProfession, on_delete=models.CASCADE)
    professionRecipe = models.ForeignKey(DataProfessionRecipe, on_delete=models.CASCADE)
    professionTier = models.ForeignKey(DataProfessionTier, on_delete=models.CASCADE)
    profession = models.ForeignKey(DataProfession, on_delete=models.CASCADE)
    altProfessionDataExpiryDate = models.DateTimeField()

    class Meta:
        db_table = 'ft_profile_altprofessiondata'
        constraints = [
            models.UniqueConstraint(fields=['alt', 'profession', 'professionTier', 'professionRecipe'], name='unique_altprofessiondata')
        ]


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
    altEquipmentExpiryDate = models.DateTimeField()

    class Meta:
        db_table = 'ft_profile_altequipment'

    def __str__(self):
        return '%s - %s' % (self.alt.altName, self.alt.altRealm)
