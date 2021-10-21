from django.db import models
from django.utils.translation import gettext_lazy as _

# Create your models here.


class FazzToolsUser(models.Model):
    userId = models.CharField(max_length=100, primary_key=True)

    class Meta:
        db_table = 'ft_fazztoolsuser'


class Alt(models.Model):
    altId = models.PositiveIntegerField(primary_key=True)
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

    user = models.ForeignKey(FazzToolsUser, on_delete=models.CASCADE)

    class Meta:
        db_table = 'ft_alt'
        constraints = [
            models.UniqueConstraint(fields=['altName', 'altRealmSlug'], name='unique_alt')
        ]

    def __str__(self):
        return '%s - %s' % (self.altName, self.altRealm)


class Profession(models.Model):
    professionId = models.PositiveIntegerField(primary_key=True)
    professionName = models.CharField(max_length=25)

    class Meta:
        db_table = 'ft_profession'

    def __str__(self):
        return '%s - %s' % (self.professionId, self.professionName)


class ProfessionTier(models.Model):
    tierId = models.PositiveSmallIntegerField(primary_key=True)
    tierName = models.CharField(max_length=25)

    profession = models.ForeignKey(Profession, on_delete=models.CASCADE)

    class Meta:
        db_table = 'ft_professiontier'

    def __str__(self):
        return '%s - %s' % (self.tierId, self.tierName)


class ProfessionRecipe(models.Model):
    recipeId = models.PositiveSmallIntegerField(primary_key=True)
    recipeName = models.CharField(max_length=50)

    professionTier = models.ForeignKey(ProfessionTier, on_delete=models.CASCADE)

    class Meta:
        db_table = 'ft_professionrecipe'

    def __str__(self):
        return '%s - %s' % (self.recipeId, self.recipeName)


class AltProfession(models.Model):
    alt = models.OneToOneField(Alt, on_delete=models.CASCADE, primary_key=True)
    profession1 = models.PositiveIntegerField()
    profession2 = models.PositiveIntegerField()
    altProfessionExpiryDate = models.DateTimeField()

    class Meta:
        db_table = 'ft_altprofession'

    def __str__(self):
        return '%s - %s' % (self.alt.altName, self.alt.altRealm)


class AltProfessionData(models.Model):
    alt = models.ForeignKey(AltProfession, on_delete=models.CASCADE)
    professionRecipe = models.ForeignKey(ProfessionRecipe, on_delete=models.CASCADE)
    professionTier = models.ForeignKey(ProfessionTier, on_delete=models.CASCADE)
    profession = models.ForeignKey(Profession, on_delete=models.CASCADE)
    altProfessionDataExpiryDate = models.DateTimeField()

    class Meta:
        db_table = 'ft_altprofessiondata'
        constraints = [
            models.UniqueConstraint(fields=['alt', 'profession', 'professionTier', 'professionRecipe'], name='unique_altprofessiondata')
        ]


class AltAchievement(models.Model):
    alt = models.OneToOneField(Alt, on_delete=models.CASCADE, primary_key=True)
    achievementData = models.JSONField()
    altAchievementExpiryDate = models.DateTimeField()

    class Meta:
        db_table = 'ft_altachievement'

    def __str__(self):
        return '%s - %s' % (self.alt.altName, self.alt.altRealm)


class AltQuestCompleted(models.Model):
    alt = models.OneToOneField(Alt, on_delete=models.CASCADE, primary_key=True)
    questCompletedData = models.JSONField()
    altQuestCompletedExpiryDate = models.DateTimeField()

    class Meta:
        db_table = 'ft_altquestcompleted'

    def __str__(self):
        return '%s - %s' % (self.alt.altName, self.alt.altRealm)


class AltMedia(models.Model):
    alt = models.OneToOneField(Alt, on_delete=models.CASCADE, primary_key=True)
    avatar = models.CharField(max_length=100, default=None)
    inset = models.CharField(max_length=100, default=None)
    main = models.CharField(max_length=100, default=None)
    mainRaw = models.CharField(max_length=100, default=None)
    altMediaExpiryDate = models.DateTimeField()

    class Meta:
        db_table = 'ft_altmedia'

    def __str__(self):
        return '%s - %s' % (self.alt.altName, self.alt.altRealm)


class Equipment(models.Model):
    item_id = models.PositiveIntegerField(primary_key=True)
    name = models.CharField(max_length=80)
    slot = models.CharField(max_length=20)
    armour_type = models.CharField(max_length=20)
    icon = models.CharField(max_length=100)

    class Meta:
        db_table = 'ft_equipment'

    def __str__(self):
        return '%s' % (self.name, self.slot)


class AltEquipment(models.Model):
    alt = models.ForeignKey(Alt, on_delete=models.CASCADE)
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE)
    item_level = models.PositiveSmallIntegerField()
    stats = models.JSONField()
    slot = models.CharField(max_length=20)
    quality = models.CharField(max_length=20)
    sockets = models.JSONField()
    enchants = models.JSONField()
    spells = models.JSONField()
    azerite = models.JSONField()
    altEquipmentExpiryDate = models.DateTimeField()

    class Meta:
        db_table = 'ft_altequipment'

    def __str__(self):
        return '%s' % (self.alt.altName, self.slot)
